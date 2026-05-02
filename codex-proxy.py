"""
Anthropic -> OpenAI Protocol Proxy

接收 Claude Code / Codex CLI 发出的 Anthropic Messages API 请求，
实时翻译为 OpenAI Chat Completions API 格式转发到上游，再将响应翻译回来。

核心能力：
  - 请求翻译：system prompt、messages、tools、tool_result 全量转换
  - 流式 SSE 翻译：OpenAI delta 事件流 → Anthropic 结构化事件流
  - 工具调用双向映射：tool_use ↔ function_call

Usage:
    python codex-proxy.py
    python codex-proxy.py --port 5678 --upstream https://www.aiproxies.cc --model gpt-5.4
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
import uuid
from typing import Any

from aiohttp import web, ClientSession, ClientTimeout

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("codex-proxy")

# ── Secrets ─────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_secrets() -> dict[str, str]:
    """从 secrets.json 加载 API 密钥。文件不存在时返回空字典。"""
    path = os.path.join(_SCRIPT_DIR, "secrets.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    log.warning("secrets.json not found, API keys will be empty")
    return {}

_secrets = _load_secrets()

# ── Default Config ──────────────────────────────────────
UPSTREAM_BASE = "https://www.aiproxies.cc"
UPSTREAM_KEY = _secrets.get("aiproxies_key", "")
DEFAULT_MODEL = "gpt-5.4"
PORT = 5678


# ══════════════════════════════════════════════════════════
#  Request Translation: Anthropic -> OpenAI
# ══════════════════════════════════════════════════════════

def translate_request(body: dict[str, Any]) -> dict[str, Any]:
    """将 Anthropic Messages API 请求体转换为 OpenAI Chat Completions 格式。

    处理：system prompt 提升、消息格式转换、tool_use/tool_result 双向映射、
    工具定义 input_schema → parameters 转换。
    """
    messages = []

    # System message (Anthropic: top-level "system" field)
    system = body.get("system")
    if system:
        if isinstance(system, str):
            messages.append({"role": "system", "content": system})
        elif isinstance(system, list):
            text = "\n".join(
                b.get("text", "") for b in system if b.get("type") == "text"
            )
            if text:
                messages.append({"role": "system", "content": text})

    # Convert messages
    for msg in body.get("messages", []):
        role = msg["role"]
        content = msg.get("content", "")

        if isinstance(content, str):
            messages.append({"role": role, "content": content})
        elif isinstance(content, list):
            tool_results = [b for b in content if b.get("type") == "tool_result"]

            if tool_results:
                # tool_result blocks -> OpenAI "tool" role messages
                for tr in tool_results:
                    tc_content = tr.get("content", "")
                    if isinstance(tc_content, list):
                        tc_content = "\n".join(
                            b.get("text", "") for b in tc_content
                            if b.get("type") == "text"
                        )
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tr.get("tool_use_id", ""),
                        "content": str(tc_content) if tc_content else "",
                    })
                # Include any accompanying text blocks
                text_blocks = [b for b in content if b.get("type") == "text"]
                if text_blocks:
                    text = "\n".join(b.get("text", "") for b in text_blocks)
                    messages.append({"role": "user", "content": text})
            else:
                # text + tool_use blocks (assistant messages)
                text_parts = []
                tool_calls = []
                for block in content:
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_calls.append({
                            "id": block.get("id", f"call_{uuid.uuid4().hex[:24]}"),
                            "type": "function",
                            "function": {
                                "name": block.get("name", ""),
                                "arguments": json.dumps(block.get("input", {})),
                            },
                        })

                assistant_msg = {
                    "role": role,
                    "content": "\n".join(text_parts) if text_parts else None,
                }
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                messages.append(assistant_msg)

    # Build OpenAI request
    result = {
        "model": DEFAULT_MODEL,  # Always use configured model
        "messages": messages,
        "stream": body.get("stream", False),
    }

    for key in ["max_tokens", "temperature", "top_p", "stop"]:
        if key in body:
            result[key] = body[key]

    # Tool definitions
    if "tools" in body:
        result["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {}),
                },
            }
            for t in body["tools"]
        ]
        result["tool_choice"] = "auto"

    if body.get("stream"):
        result["stream_options"] = {"include_usage": True}

    return result


# ══════════════════════════════════════════════════════════
#  Non-streaming Response: OpenAI -> Anthropic
# ══════════════════════════════════════════════════════════

def translate_response(openai_resp: dict[str, Any]) -> dict[str, Any]:
    """将 OpenAI Chat Completions 响应转换为 Anthropic Messages 格式。

    处理：finish_reason 映射、function_call → tool_use 转换、usage 字段重命名。
    """
    choice = openai_resp.get("choices", [{}])[0]
    message = choice.get("message", {})

    content = []
    text = message.get("content")
    if text:
        content.append({"type": "text", "text": text})

    for tc in message.get("tool_calls", []):
        func = tc.get("function", {})
        try:
            input_data = json.loads(func.get("arguments", "{}"))
        except json.JSONDecodeError:
            input_data = {}
        content.append({
            "type": "tool_use",
            "id": tc.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
            "name": func.get("name", ""),
            "input": input_data,
        })

    finish = choice.get("finish_reason", "stop")
    stop_reason = "tool_use" if finish == "tool_calls" else "end_turn"
    usage = openai_resp.get("usage", {})

    return {
        "id": f"msg_{uuid.uuid4().hex[:24]}",
        "type": "message",
        "role": "assistant",
        "content": content if content else [{"type": "text", "text": ""}],
        "model": DEFAULT_MODEL,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
    }


# ══════════════════════════════════════════════════════════
#  Streaming Translation: OpenAI SSE -> Anthropic SSE
# ══════════════════════════════════════════════════════════

def sse(event: str, data: dict[str, Any]) -> bytes:
    """构造一条 SSE 事件。"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n".encode("utf-8")


async def translate_stream(resp: Any, response: web.StreamResponse) -> None:
    """将 OpenAI 的扁平 delta SSE 流翻译为 Anthropic 的结构化事件流。

    维护状态机：跟踪 block_index、tool_buffers、text_block_closed，
    在流中实时判断何时开始/关闭内容块。
    """
    msg_id = f"msg_{uuid.uuid4().hex[:24]}"

    # message_start
    await response.write(sse("message_start", {
        "type": "message_start",
        "message": {
            "id": msg_id, "type": "message", "role": "assistant",
            "content": [], "model": DEFAULT_MODEL,
            "stop_reason": None, "stop_sequence": None,
            "usage": {
                "input_tokens": 0, "output_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
        },
    }))

    # content_block_start (text)
    await response.write(sse("content_block_start", {
        "type": "content_block_start",
        "index": 0,
        "content_block": {"type": "text", "text": ""},
    }))

    await response.write(sse("ping", {"type": "ping"}))

    block_index = 0
    tool_buffers = {}  # tc_id -> index
    finish_reason = "end_turn"
    output_tokens = 0
    text_block_closed = False

    buffer = ""
    async for chunk_bytes, _ in resp.content.iter_chunks():
        buffer += chunk_bytes.decode("utf-8", errors="replace")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line or not line.startswith("data: "):
                continue

            data_str = line[6:]
            if data_str == "[DONE]":
                continue

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            # Handle usage chunk (stream_options.include_usage)
            if chunk.get("usage"):
                output_tokens = chunk["usage"].get("completion_tokens", output_tokens)

            choices = chunk.get("choices", [])
            if not choices:
                continue

            delta = choices[0].get("delta", {})
            fr = choices[0].get("finish_reason")

            # Text content
            text = delta.get("content")
            if text:
                output_tokens = max(output_tokens, output_tokens + max(1, len(text) // 4))
                await response.write(sse("content_block_delta", {
                    "type": "content_block_delta",
                    "index": 0,
                    "delta": {"type": "text_delta", "text": text},
                }))

            # Tool calls
            for tc in delta.get("tool_calls", []):
                tc_id = tc.get("id")
                func = tc.get("function", {})
                tc_name = func.get("name")
                tc_args = func.get("arguments", "")

                if tc_id and tc_id not in tool_buffers:
                    # Close text block before first tool
                    if not text_block_closed:
                        await response.write(sse("content_block_stop", {
                            "type": "content_block_stop", "index": 0,
                        }))
                        text_block_closed = True

                    block_index += 1
                    tool_buffers[tc_id] = block_index

                    await response.write(sse("content_block_start", {
                        "type": "content_block_start",
                        "index": block_index,
                        "content_block": {
                            "type": "tool_use",
                            "id": tc_id,
                            "name": tc_name or "",
                        },
                    }))

                if tc_args:
                    idx = tool_buffers.get(tc_id, block_index)
                    await response.write(sse("content_block_delta", {
                        "type": "content_block_delta",
                        "index": idx,
                        "delta": {"type": "input_json_delta", "partial_json": tc_args},
                    }))

            if fr:
                if fr == "tool_calls":
                    finish_reason = "tool_use"
                elif fr == "length":
                    finish_reason = "max_tokens"
                else:
                    finish_reason = "end_turn"

    # Close open blocks
    if tool_buffers:
        for tc_id, idx in tool_buffers.items():
            await response.write(sse("content_block_stop", {
                "type": "content_block_stop", "index": idx,
            }))
    if not text_block_closed:
        await response.write(sse("content_block_stop", {
            "type": "content_block_stop", "index": 0,
        }))

    # message_delta
    await response.write(sse("message_delta", {
        "type": "message_delta",
        "delta": {"stop_reason": finish_reason, "stop_sequence": None},
        "usage": {"output_tokens": output_tokens},
    }))

    # message_stop
    await response.write(sse("message_stop", {"type": "message_stop"}))


# ══════════════════════════════════════════════════════════
#  HTTP Handlers
# ══════════════════════════════════════════════════════════

async def handle_messages(request: web.Request) -> web.StreamResponse:
    body = await request.json()
    is_stream = body.get("stream", False)
    openai_body = translate_request(body)

    headers = {
        "Authorization": f"Bearer {UPSTREAM_KEY}",
        "Content-Type": "application/json",
    }

    session: ClientSession = request.app["session"]

    try:
        if is_stream:
            resp = await session.post(
                f"{UPSTREAM_BASE}/v1/chat/completions",
                json=openai_body, headers=headers,
            )

            response = web.StreamResponse(
                status=200,
                headers={
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                },
            )
            await response.prepare(request)
            await translate_stream(resp, response)
            await response.write_eof()
            resp.close()
            return response
        else:
            async with session.post(
                f"{UPSTREAM_BASE}/v1/chat/completions",
                json=openai_body, headers=headers,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    log.error("Upstream %d: %s", resp.status, error_text[:200])
                    return web.json_response(
                        {"error": {"type": "api_error", "message": error_text}},
                        status=resp.status,
                    )
                openai_resp = await resp.json()
                return web.json_response(translate_response(openai_resp))

    except Exception as e:
        log.error("Upstream error: %s", e)
        return web.json_response(
            {"error": {"type": "api_error", "message": str(e)}},
            status=500,
        )


async def handle_health(request: web.Request):
    return web.json_response({"status": "ok"})


# ── App Lifecycle ───────────────────────────────────────

async def on_startup(app):
    app["session"] = ClientSession(timeout=ClientTimeout(total=300))


async def on_cleanup(app):
    await app["session"].close()


def main():
    global UPSTREAM_BASE, UPSTREAM_KEY, DEFAULT_MODEL

    parser = argparse.ArgumentParser(description="Anthropic -> OpenAI Protocol Proxy")
    parser.add_argument("--port", type=int, default=PORT, help="Local port (default: 5678)")
    parser.add_argument("--upstream", default=UPSTREAM_BASE, help="Upstream OpenAI-compatible base URL")
    parser.add_argument("--key", default=UPSTREAM_KEY, help="Upstream API key")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model to use (default: gpt-5.4)")
    args = parser.parse_args()

    UPSTREAM_BASE = args.upstream.rstrip("/")
    UPSTREAM_KEY = args.key
    DEFAULT_MODEL = args.model

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.router.add_post("/v1/messages", handle_messages)
    app.router.add_get("/", handle_health)

    log.info("=== Anthropic -> OpenAI Protocol Proxy ===")
    log.info("Listen:   http://127.0.0.1:%d", args.port)
    log.info("Upstream: %s", UPSTREAM_BASE)
    log.info("Model:    %s", DEFAULT_MODEL)

    web.run_app(app, host="127.0.0.1", port=args.port, print=None)


if __name__ == "__main__":
    main()
