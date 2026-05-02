# API Gateway

<p align="center">
  <img src="docs/api-gateway-banner.png" alt="API Gateway Architecture" width="800">
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000.svg)](https://flask.palletsprojects.com)
[![aiohttp](https://img.shields.io/badge/aiohttp-3.9-2c5bb4.svg)](https://docs.aiohttp.org)

**Make Claude Desktop & Codex CLI work with any third-party model provider.**

Claude Desktop's 3p (third-party) mode and Codex CLI / Claude Code only connect to official APIs by default. This project provides a local proxy layer that enables **multi-provider routing + automatic protocol translation**, so you can freely use any third-party model in these tools.

[English](#why-this-project) | [中文](#中文说明)

---

## Why This Project?

Using AI coding tools (Claude Desktop, Codex CLI, Claude Code) with official APIs faces several real-world barriers:

**Cost** — Claude Sonnet 4 API costs $3/$15 per 1M tokens. A full day of coding (30-50 refactoring sessions) costs $11-19/day, or **$300-500/month**. That's more expensive than hiring a junior developer in many regions.

**Payment** — OpenAI and Anthropic only accept US/EU credit cards. Users in many countries simply **cannot pay** for official API access, regardless of willingness.

**Network** — `api.openai.com` and `api.anthropic.com` are blocked in some regions. Even with a valid API key, direct connections fail without a VPN.

**Protocol Lock-in** — Claude Desktop speaks Anthropic's Messages API. If your model provider uses OpenAI's Chat Completions API, you're stuck — unless something translates between the two formats.

**This project solves all four problems.** It lets you connect to affordable third-party providers (relay stations, self-hosted proxies, regional model providers) and handles all the protocol translation automatically. One proxy, any model, any provider.

---

## What Are These Tools?

### Claude Desktop

[Claude Desktop](https://claude.ai/download) is Anthropic's desktop client for Claude. In **3P (Third-Party) mode**, it can connect to any API endpoint instead of Anthropic's servers — this is what makes the gateway possible.

**Setup notes:**
- Download from [claude.ai/download](https://claude.ai/download) (Windows / macOS)
- Enable Developer Mode: **Help → Troubleshooting → Enable Developer Mode**
- Configure Gateway: **Developer → Configure Third-Party Inference**
- Gateway URL must use `http://127.0.0.1:port` (not `localhost`)

### Codex CLI

[Codex CLI](https://github.com/openai/codex) is OpenAI's open-source CLI coding agent. It uses the OpenAI API by default, but with `codex-proxy.py`, you can run it through any provider.

```bash
npm install -g @openai/codex
```

### Claude Code

[Claude Code](https://docs.anthropic.com/en/docs/claude-code) is Anthropic's CLI coding assistant. It's a terminal-based agent that can read, write, and execute code autonomously.

```bash
npm install -g @anthropic-ai/claude-code
```

> For detailed troubleshooting (MSIX path bugs, registry quirks, Cowork VM issues, etc.), see **[docs/troubleshooting.md](docs/troubleshooting.md)**.

---

## Architecture

```mermaid
graph TB
    subgraph Clients
        CD["Claude Desktop<br/>(3p Mode)"]
        CC["Codex CLI /<br/>Claude Code"]
    end

    subgraph API Gateway
        P["proxy.py<br/>:8082"]
        CP["codex-proxy.py<br/>:5678"]
        Panel["Control Panel<br/>:8083"]
    end

    subgraph Providers
        SP["SophNet<br/>DeepSeek, Doubao, Kimi, GLM..."]
        AP["aiproxies.cc<br/>GPT-5.5, GPT-4o..."]
        MI["Xiaomi MiMo<br/>MiMo-V2.5-Pro..."]
    end

    CD -->|"Anthropic API"| P
    CC -->|"Anthropic API"| CP
    P -->|"Anthropic (passthrough)"| SP
    P -->|"Anthropic → OpenAI"| AP
    P -->|"Anthropic (passthrough)"| MI
    CP -->|"Anthropic → OpenAI"| AP
    Panel -.->|"model switch"| P

    style CD fill:#6b4fbb,color:#fff
    style CC fill:#6b4fbb,color:#fff
    style P fill:#ff6b35,color:#fff
    style CP fill:#ff6b35,color:#fff
    style Panel fill:#ff6b35,color:#fff
    style SP fill:#00a67e,color:#fff
    style AP fill:#00a67e,color:#fff
    style MI fill:#00a67e,color:#fff
```

## Features

- **Multi-Provider Gateway** — Route Claude Desktop to multiple model providers through a single proxy, with a browser-based control panel for instant model switching
- **Protocol Translation** — Bidirectional Anthropic <-> OpenAI format translation with full support for streaming and tool use
- **Image Input** — Automatically converts Anthropic image blocks to OpenAI `image_url` format
- **Image Generation** — Detects image generation requests and routes them to OpenAI Responses API (DALL-E)
- **Process Resilience** — Global exception handler + auto-restart loop ensures the proxy never crashes from upstream API errors
- **Centralized Key Management** — All API keys stored in `secrets.json` (gitignored), zero hardcoded credentials

## Supported Providers

| Provider | Models | Protocol | Notes |
|----------|--------|----------|-------|
| **SophNet** | DeepSeek-V4-Flash, DeepSeek-V4-Pro, GPT-4o-mini, Doubao-Seed-1.6, MiniMax, Kimi, GLM | Anthropic-compatible | Direct passthrough |
| **aiproxies.cc** | GPT-5.5, GPT-5.4, GPT-4o | OpenAI | Auto-translated to/from Anthropic format |
| **Xiaomi MiMo** | MiMo-V2.5-Pro, MiMo-V2.5, MiMo-V2-Pro | Anthropic-compatible | Direct passthrough |

> Adding a new provider takes ~20 lines of code. See [Adding New Providers](#adding-new-providers).

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp secrets.example.json secrets.json
# Edit secrets.json with your actual API keys
```

<details>
<summary><b>secrets.json format</b></summary>

```json
{
  "aiproxies_key": "sk-your-aiproxies-key",
  "mimo_key": "sk-your-mimo-key",
  "qwen_key": "sk-your-qwen-key",
  "vectorengine_key": "sk-your-vectorengine-key"
}
```

</details>

### 3. Start the proxy

```bash
# Claude Desktop gateway (Proxy :8082 + Control Panel :8083)
python proxy.py

# Codex CLI protocol proxy (:5678)
python codex-proxy.py
```

### 4. Configure Claude Desktop

Create a 3p mode config file at `%LOCALAPPDATA%\Claude-3p\configLibrary\<uuid>.json`:

```json
{
  "inferenceProvider": "gateway",
  "inferenceGatewayBaseUrl": "http://127.0.0.1:8082",
  "inferenceGatewayApiKey": "<your-upstream-api-key>",
  "inferenceGatewayAuthScheme": "x-api-key"
}
```

Register available models in the Windows Registry:

```powershell
Set-ItemProperty -Path "HKCU:\SOFTWARE\Policies\Claude" -Name "inferenceModels" `
  -Value '["DeepSeek-V4-Flash","gpt-5.5","MiMo-V2.5-Pro"]' -Type String
```

### 5. Configure Codex CLI / Claude Code

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:5678
export ANTHROPIC_API_KEY=sk-any-placeholder
codex  # or claude
```

Or use the endpoint switcher (PowerShell):

```powershell
. .\scripts\claude-switch.ps1 codex    # Local proxy → GPT-5.4
. .\scripts\claude-switch.ps1 qwen     # Self-hosted → Qwen
. .\scripts\claude-switch.ps1 vector   # VectorEngine → Claude
. .\scripts\claude-switch.ps1 list     # List all endpoints
```

## Project Structure

```
api-gateway/
├── proxy.py                  # Claude Desktop multi-provider gateway proxy
├── codex-proxy.py            # Codex CLI / Claude Code protocol translation proxy
├── requirements.txt          # Python dependencies
├── secrets.example.json      # API key template (safe to commit)
├── scripts/
│   ├── claude-switch.ps1     # Claude Code endpoint switcher
│   ├── proxy-loop.bat        # Auto-restart loop
│   └── start-proxy.vbs       # Windows silent startup (for Task Scheduler)
├── docs/
│   └── SKILL.md              # Tool description file
├── LICENSE
└── README.md
```

## How It Works

### proxy.py — Claude Desktop Gateway

```mermaid
sequenceDiagram
    participant CD as Claude Desktop
    participant GW as proxy.py (:8082)
    participant UP as Upstream Provider

    CD->>GW: POST /v1/messages (Anthropic format)
    GW->>GW: Identify provider by model name
    
    alt Anthropic-compatible provider (SophNet, MiMo)
        GW->>UP: Forward as-is (Anthropic format)
        UP->>GW: Anthropic response
    else OpenAI provider (aiproxies)
        GW->>GW: Convert Anthropic → OpenAI format
        GW->>UP: POST /v1/chat/completions (OpenAI format)
        UP->>GW: OpenAI response
        GW->>GW: Convert OpenAI → Anthropic format
    end
    
    GW->>CD: Anthropic response
```

### codex-proxy.py — Protocol Translation

```mermaid
sequenceDiagram
    participant CX as Codex CLI
    participant PX as codex-proxy.py (:5678)
    participant AI as aiproxies.cc

    CX->>PX: POST /v1/messages (Anthropic format)
    PX->>PX: Translate messages, tools, system prompt
    PX->>AI: POST /v1/chat/completions (OpenAI format)
    AI-->>PX: SSE stream (OpenAI delta format)
    PX-->>CX: SSE stream (Anthropic delta format)
    
    Note over PX: Handles tool_use ↔ function_call<br/>bidirectional translation
```

## Control Panel

The gateway includes a built-in web control panel at `http://127.0.0.1:8083`:

- View the currently active model
- Switch models instantly (takes effect on the next message)
- Monitor request statistics and logs

## Adding New Providers

Adding a new model provider takes 5 steps:

**Step 1.** Add your API key to `secrets.json`:
```json
{ "new_provider_key": "sk-your-key" }
```

**Step 2.** Add constants at the top of `proxy.py`:
```python
NEW_PROVIDER_BASE = "https://api.newprovider.com/v1"
NEW_PROVIDER_KEY = _secrets.get("new_provider_key", "")
```

**Step 3.** Add model definitions and merge into `MODELS`:
```python
NEW_MODELS = {
    "new-model-name": {"provider": "newprovider", "upstream": "actual-model-id"},
}
MODELS = {**SOPHNET_MODELS, **AIPROXIES_MODELS, **MIMO_MODELS, **NEW_MODELS}
```

**Step 4.** Write a routing function. Copy the pattern that matches your provider's API:
- Anthropic-compatible? Copy `_proxy_via_mimo`
- OpenAI-compatible? Copy `_proxy_via_aiproxies`

**Step 5.** Add routing in `proxy_post()`:
```python
elif info["provider"] == "newprovider":
    return _proxy_via_newprovider(data, info["upstream"])
```

Restart the proxy and Claude Desktop. Done.

## Auto-Start on Windows

To start the proxy silently on boot:

1. Press `Win + R`, type `shell:startup`
2. Create a shortcut to `scripts/start-proxy.vbs`
3. The proxy will start silently in the background with auto-restart

---

## 中文说明

### 为什么做这个项目？

用官方 API 跑 AI 编程工具，成本是真实的痛：

- **贵**：Claude Sonnet 4 按量计费，连续编程一天 $11-19，一个月 $300-500
- **买不了**：OpenAI / Anthropic 只收海外信用卡，国内用户根本没法直接付款
- **连不上**：`api.openai.com` 和 `api.anthropic.com` 在国内被墙，没代理用不了
- **协议不通**：Claude Desktop 发 Anthropic 格式，你的中转站可能只支持 OpenAI 格式

**本项目一次性解决以上所有问题**——接入便宜的中转站/自建反代/国产模型，协议自动转换，一个代理搞定一切。

### 这些工具是什么？

| 工具 | 说明 | 安装 |
|------|------|------|
| **Claude Desktop** | Anthropic 桌面客户端，3P 模式可接入第三方模型 | [claude.ai/download](https://claude.ai/download) |
| **Codex CLI** | OpenAI 开源命令行编程 Agent | `npm install -g @openai/codex` |
| **Claude Code** | Anthropic 命令行编程助手，支持 Sub-agent 并行 | `npm install -g @anthropic-ai/claude-code` |

### 配置要点

- Claude Desktop 需启用开发者模式：**Help → Troubleshooting → Enable Developer Mode**
- Gateway URL 必须用 `http://127.0.0.1:端口`，不能用 `localhost`
- 开了 Clash 注意排除本地地址，避免代理拦截 127.0.0.1 的请求
- MSIX 安装的 Claude Desktop 存在路径虚拟化问题，详见踩坑指南

### 踩坑指南

我们整理了 12+ 个配置过程中遇到的坑和修复方案，包括 MSIX 路径 bug、注册表配置、模型名显示异常、VM 沙箱启动失败等。

详见 **[docs/troubleshooting.md](docs/troubleshooting.md)**

## License

[MIT](LICENSE) - feel free to use, modify, and distribute.
