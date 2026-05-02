---
name: api-gateway
description:
  AI API 代理网关：管理 Claude Desktop、Codex CLI、Claude Code 等工具的多提供商 API 转接。
  包含 Claude Desktop 多模型网关代理（SophNet/aiproxies/MiMo）、Codex CLI 协议转换代理（Anthropic↔OpenAI）、
  Claude Code 端点切换器。所有 API 密钥集中存储在 secrets.json（已 gitignore）。
metadata:
  author: 一泽Eze
  version: "1.0.0"
---

# API Gateway

AI 工具的统一 API 代理网关，集中管理所有 API 密钥和代理转接配置。

## 文件结构

```
api-gateway/
├── SKILL.md              ← 本文件
├── README.md             ← 详细文档
├── secrets.json          ← API 密钥（⚠️ gitignored，不会上传）
├── secrets.example.json  ← 密钥模板（安全，可提交）
├── proxy.py              ← Claude Desktop 多模型网关代理
├── codex-proxy.py        ← Codex CLI / Claude Code 协议转换代理
├── claude-switch.ps1     ← Claude Code 端点切换器
├── start-proxy.vbs       ← Windows 开机自启（静默启动）
└── proxy-loop.bat        ← 自动重启循环
```

## 组件说明

### 1. Claude Desktop 网关代理 (`proxy.py`)

Claude Desktop 3p 模式的多提供商路由代理。

```
Claude Desktop → Proxy (:8082) → SophNet / aiproxies / MiMo
控制面板: http://127.0.0.1:8083
```

- **SophNet 模型**：Anthropic 格式直转（DeepSeek、Doubao、Kimi 等）
- **aiproxies 模型**：Anthropic→OpenAI 协议转换（GPT-5.5、GPT-4o 等）
- **MiMo 模型**：Anthropic 格式直转，内置 API Key

特性：全局异常捕获防崩溃、自动重启循环、图片格式转换（Anthropic↔OpenAI）、DALL-E 生图支持。

### 2. Codex CLI 协议代理 (`codex-proxy.py`)

让 Claude Code / Codex CLI 通过 OpenAI 中转站使用 GPT 模型。

```
Claude Code → Proxy (:5678) [Anthropic格式] → aiproxies.cc [OpenAI格式]
```

支持流式输出和 Tool Use 双向转换。

### 3. Claude Code 端点切换器 (`claude-switch.ps1`)

一键切换 Claude Code 的后端 API 端点。

```powershell
. .\claude-switch.ps1 codex    # 切到 GPT-5.4 (via local proxy)
. .\claude-switch.ps1 qwen     # 切到 Qwen
. .\claude-switch.ps1 vector   # 切到 VectorEngine Claude
. .\claude-switch.ps1 list     # 列出所有端点
```

## 密钥管理

所有 API 密钥存储在 `secrets.json`，该文件被 `.gitignore` 排除，**不会上传到 GitHub**。

首次使用时，复制 `secrets.example.json` 为 `secrets.json` 并填入真实密钥：
```powershell
Copy-Item secrets.example.json secrets.json
# 然后编辑 secrets.json 填入真实 API Key
```

## 启动

```powershell
# Claude Desktop 代理
python proxy.py

# Codex CLI 代理
python codex-proxy.py

# Windows 开机自启（双击 start-proxy.vbs）
```
