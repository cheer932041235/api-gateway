# API Gateway

> Make Claude Desktop & Codex CLI work with **any** third-party model provider — DeepSeek, GPT-5.5, MiMo, Kimi, GLM, and more.

Claude Desktop 的 3p (third-party) 模式和 Codex CLI / Claude Code 默认只能连接官方 API。本项目通过本地代理实现**多提供商接入 + 协议自动转换**，让你在这些工具中自由使用各种第三方模型。

## 特性

- **Claude Desktop 多模型网关** — 一个代理接入多个提供商，浏览器控制面板一键切换模型
- **Codex CLI / Claude Code 协议转换** — Anthropic ↔ OpenAI 格式双向翻译，支持流式输出和 Tool Use
- **图片输入支持** — 自动将 Anthropic 图片格式转为 OpenAI `image_url` 格式
- **DALL-E 生图** — 检测生图请求自动路由到 OpenAI Responses API
- **进程保活** — 全局异常捕获 + 自动重启循环，不会因为上游 API 报错而崩溃
- **密钥集中管理** — 所有 API Key 存储在 `secrets.json`，代码中无硬编码

## 架构

```
Claude Desktop (3p 模式)               Codex CLI / Claude Code
    │ Anthropic Messages API               │ Anthropic Messages API
    ▼                                      ▼
proxy.py (:8082)                      codex-proxy.py (:5678)
    │ 路由 & 协议转换                       │ 协议转换
    ├── Anthropic 兼容 → 直转               └── OpenAI 兼容 → Chat Completions
    └── OpenAI 兼容 → 协议转换
         ├── 文本 → Chat Completions API
         └── 生图 → Responses API
```

## 快速开始

### 1. 安装依赖

```bash
pip install flask requests
# Codex 代理需要额外安装
pip install aiohttp
```

### 2. 配置密钥

```bash
cp secrets.example.json secrets.json
# 编辑 secrets.json，填入你的 API Key
```

### 3. 启动代理

```bash
# Claude Desktop 网关代理（Proxy :8082 + 控制面板 :8083）
python proxy.py

# Codex CLI 协议转换代理（:5678）
python codex-proxy.py
```

### 4. 配置 Claude Desktop

Claude Desktop 3p 模式配置文件：`%LOCALAPPDATA%\Claude-3p\configLibrary\<uuid>.json`

```json
{
  "inferenceProvider": "gateway",
  "inferenceGatewayBaseUrl": "http://127.0.0.1:8082",
  "inferenceGatewayApiKey": "<your-api-key>",
  "inferenceGatewayAuthScheme": "x-api-key"
}
```

### 5. 配置 Codex CLI / Claude Code

```bash
export ANTHROPIC_BASE_URL=http://127.0.0.1:5678
export ANTHROPIC_API_KEY=sk-any-placeholder
claude  # 或 codex
```

或使用端点切换器：

```powershell
. .\claude-switch.ps1 codex    # 切到本地代理
. .\claude-switch.ps1 list     # 列出所有端点
```

## 文件结构

```
api-gateway/
├── proxy.py              # Claude Desktop 多模型网关代理
├── codex-proxy.py        # Codex CLI / Claude Code 协议转换代理
├── claude-switch.ps1     # Claude Code 端点切换器
├── secrets.json          # API 密钥（⚠️ gitignored）
├── secrets.example.json  # 密钥模板
├── start-proxy.vbs       # Windows 开机自启（静默启动）
├── proxy-loop.bat        # 自动重启循环
├── SKILL.md              # 工具描述文件
└── README.md             # 本文件
```

## 添加新模型提供商

1. **`secrets.json`** — 添加新的 API Key
2. **`proxy.py` 顶部** — 添加 Base URL 常量，从 `_secrets` 加载密钥
3. **模型字典** — 添加模型信息，合并到 `MODELS`
4. **路由函数** — Anthropic 兼容格式复制 `_proxy_via_mimo`；OpenAI 格式复制 `_proxy_via_aiproxies`
5. **路由分发** — 在 `proxy_post()` 中添加 `elif` 判断
6. 重启代理 + Claude Desktop

## 控制面板

启动后打开 `http://127.0.0.1:8083`：

- 查看当前选中模型
- 一键切换模型（下一条消息立即生效）
- 查看请求统计

## License

MIT
