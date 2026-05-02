# 架构设计文档

> 本文档从技术角度深入分析 API Gateway 的设计决策、协议差异、核心算法和错误处理策略。面向贡献者和技术评审。

---

## 1. 设计目标

| 目标 | 约束 |
|------|------|
| **零配置切换** | 用户在控制面板点一下就能换模型，不需要重启任何东西 |
| **协议透明** | Claude Desktop / Codex CLI 完全无感知，它们以为自己在和官方 API 通信 |
| **故障隔离** | 上游任何一个提供商挂了不影响其他提供商，proxy 本身不崩溃 |
| **最小依赖** | proxy.py 只依赖 Flask + requests；codex-proxy.py 只依赖 aiohttp |

## 2. 系统架构

### 2.1 双进程模型

系统由两个独立进程组成，各自服务不同的客户端：

```
┌─────────────────────────────────────────────────────┐
│                   API Gateway                        │
│                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │     proxy.py         │  │   codex-proxy.py     │  │
│  │  (Flask, 同步)       │  │  (aiohttp, 异步)     │  │
│  │                      │  │                      │  │
│  │  :8082 代理端口      │  │  :5678 代理端口      │  │
│  │  :8083 控制面板      │  │                      │  │
│  │                      │  │                      │  │
│  │  多提供商路由        │  │  单提供商协议转换    │  │
│  │  模型名 → 提供商     │  │  Anthropic → OpenAI  │  │
│  └──────────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**为什么是两个进程而不是一个？**

- **协议方向不同**：proxy.py 接收 Anthropic 格式、按需转换；codex-proxy.py 固定做 Anthropic→OpenAI 转换
- **并发模型不同**：proxy.py 用 Flask（同步），因为 Claude Desktop 不会并发请求；codex-proxy.py 用 aiohttp（异步），因为流式 SSE 翻译需要非阻塞 I/O
- **生命周期独立**：可以只启动其中一个，互不依赖

### 2.2 请求路由策略

proxy.py 的路由分发基于**模型名归属判断**：

```
收到请求 → 提取 model 字段
    │
    ├── model ∈ SOPHNET_MODELS → _proxy_via_sophnet()  [Anthropic 直转]
    ├── model ∈ AIPROXIES_MODELS → _proxy_via_aiproxies() [Anthropic→OpenAI 转换]
    ├── model ∈ MIMO_MODELS → _proxy_via_mimo()  [Anthropic 直转，自带 Key]
    └── model 不在任何字典 → 使用控制面板当前选中的模型
```

**关键设计决策**：模型名作为路由键，而不是在配置中指定提供商。这样用户在 Claude Desktop 中选择模型时，请求自动路由到正确的提供商，无需额外配置。

## 3. 协议差异分析

### 3.1 Anthropic vs OpenAI 核心差异

这是整个项目存在的技术基础。两种协议虽然都是"发消息、得回复"，但结构差异很大：

| 维度 | Anthropic Messages API | OpenAI Chat Completions API |
|------|----------------------|---------------------------|
| **端点** | `POST /v1/messages` | `POST /v1/chat/completions` |
| **System Prompt** | 顶层 `system` 字段（字符串或 block 数组） | `messages` 中 `role: "system"` 的消息 |
| **图片输入** | `type: "image"` + `source.type: "base64"` | `type: "image_url"` + `image_url.url: "data:..."` |
| **工具定义** | `tools[].input_schema` | `tools[].function.parameters` |
| **工具调用** | `content` 中 `type: "tool_use"` block | `tool_calls[].function` |
| **工具结果** | `content` 中 `type: "tool_result"` block | `role: "tool"` 的独立消息 |
| **停止原因** | `stop_reason: "end_turn" / "tool_use"` | `finish_reason: "stop" / "tool_calls"` |
| **流式格式** | 自定义 SSE 事件（`message_start`, `content_block_delta` 等） | 标准 SSE `data:` 行（`choices[0].delta`） |
| **用量统计** | `usage.input_tokens / output_tokens` | `usage.prompt_tokens / completion_tokens` |

### 3.2 流式 SSE 事件映射

这是技术难度最高的部分。OpenAI 的流式输出是扁平的 delta 序列，Anthropic 的流式输出是**结构化的事件流**，有明确的 block 生命周期：

```
OpenAI 流式事件（扁平）          Anthropic 流式事件（结构化）
─────────────────────           ────────────────────────────
                                message_start
                                content_block_start (index=0, text)
                                ping
delta.content = "你"     →      content_block_delta (index=0, text_delta)
delta.content = "好"     →      content_block_delta (index=0, text_delta)
delta.tool_calls[0].id   →     content_block_stop (index=0)  ← 关闭文本块
                                content_block_start (index=1, tool_use)
delta.tool_calls[0].args →     content_block_delta (index=1, input_json_delta)
finish_reason = "tool_calls" → content_block_stop (index=1)
                                message_delta (stop_reason="tool_use")
[DONE]                   →      message_stop
```

**核心状态机**：codex-proxy.py 中的 `translate_stream()` 维护以下状态：

- `block_index`：当前内容块索引（文本块是 0，后续工具块递增）
- `tool_buffers`：`{tool_call_id: block_index}` 映射，跟踪每个工具调用的块位置
- `text_block_closed`：文本块是否已关闭（遇到工具调用时必须先关闭文本块）
- `finish_reason`：最终停止原因的翻译

**为什么这很难？** 因为 OpenAI 的 delta 是"追加式"的（每个 chunk 只有增量），而 Anthropic 需要**显式的 block 开始/结束事件**。翻译器必须在流中实时判断"什么时候开始新 block、什么时候关闭旧 block"，不能等全部收完再处理。

### 3.3 工具调用翻译

工具调用是 AI Agent 的核心能力，翻译必须双向精确：

**Anthropic → OpenAI（请求方向）**：

```python
# Anthropic 工具定义
{"name": "read_file", "description": "...", "input_schema": {"type": "object", ...}}

# → OpenAI 工具定义
{"type": "function", "function": {"name": "read_file", "description": "...", "parameters": {"type": "object", ...}}}
```

**OpenAI → Anthropic（响应方向）**：

```python
# OpenAI 工具调用
{"tool_calls": [{"id": "call_abc", "function": {"name": "read_file", "arguments": "{\"path\": \"/tmp\"}"}}]}

# → Anthropic 工具调用
{"content": [{"type": "tool_use", "id": "call_abc", "name": "read_file", "input": {"path": "/tmp"}}]}
```

**Anthropic → OpenAI（结果返回）**：

```python
# Anthropic 工具结果
{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "call_abc", "content": "file contents..."}]}

# → OpenAI 工具结果
{"role": "tool", "tool_call_id": "call_abc", "content": "file contents..."}
```

## 4. 错误处理策略

### 4.1 分层错误处理

```
第 1 层：Flask/aiohttp 全局异常捕获
  → 任何未处理异常返回 500，进程不崩溃

第 2 层：路由函数 try/except
  → 上游连接失败返回 502 (Bad Gateway)
  → 上游返回错误码原样透传

第 3 层：进程级保活
  → proxy.py 主循环 while True + except
  → proxy-loop.bat 外层重启循环
  → start-proxy.vbs 静默启动（开机自启）
```

### 4.2 端口冲突处理

proxy.py 启动时检测端口占用，等待最多 30 秒让旧进程释放端口，避免重启时新旧进程冲突。这在 `proxy-loop.bat` 自动重启场景中尤其重要。

## 5. 密钥管理

```
secrets.json（gitignored）
    ├── 中转站 Key（SophNet）→ 从 Claude Desktop 请求头透传，proxy 不存储
    ├── aiproxies Key → proxy 内部使用（OpenAI 格式需要 Bearer token）
    ├── MiMo Key → proxy 内部使用（自带 Key，不走用户的）
    └── 其他提供商 Key → 按需添加
```

**设计原则**：能透传的就透传（SophNet），必须由 proxy 持有的才存在 secrets.json（aiproxies、MiMo）。这样用户的主密钥始终在 Claude Desktop 端管理，proxy 只持有辅助密钥。

## 6. 可扩展性

### 6.1 添加新提供商

新提供商分两类：

| 类型 | 需要做什么 | 示例 |
|------|-----------|------|
| **Anthropic 兼容** | 加模型字典 + 复制 `_proxy_via_mimo` 改 URL/Key | DeepSeek 官方、MiMo |
| **OpenAI 兼容** | 加模型字典 + 复制 `_proxy_via_aiproxies` 改 URL/Key | aiproxies、OpenRouter |

核心代码量约 20 行，主要是配置，不涉及协议转换逻辑的修改。

### 6.2 控制面板扩展

控制面板目前是单页 HTML 内嵌在 Python 代码中。如果需要更复杂的 UI（如请求日志、延迟统计、历史图表），可以：

1. 将 HTML 提取为独立的 `static/` 目录
2. 添加 WebSocket 实时推送请求日志
3. 引入 SQLite 持久化统计数据

## 7. 性能特征

| 指标 | 值 | 说明 |
|------|-----|------|
| **proxy.py 内存** | ~30MB | Flask 单进程 |
| **codex-proxy.py 内存** | ~25MB | aiohttp 单进程 |
| **代理延迟** | <5ms | 本地 HTTP 转发，可忽略 |
| **瓶颈** | 上游 API 响应时间 | 通常 1-30 秒，取决于模型和输入长度 |
| **并发** | proxy.py 单线程（Flask dev server）| Claude Desktop 不并发，够用 |
