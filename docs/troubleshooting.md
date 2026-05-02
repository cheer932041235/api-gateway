# Troubleshooting / 踩坑指南

> 汇总 Claude Desktop 3P 模式 + Codex CLI 配置过程中遇到的所有已知问题及修复方案。

---

## Claude Desktop 相关

### 坑 1：中转站直连报 400 错误

**现象**：Claude Desktop 直连中转站（如 SophNet），请求报 400 Bad Request。

**原因**：Claude Desktop 在请求中带了大量 Anthropic 专有字段和 headers（`anthropic-beta`、`anthropic-version` 等），中转站的 Anthropic 兼容层无法处理这些字段。

**修复**：使用本项目的 `proxy.py` 做中间层，自动清洗请求中中转站不认识的字段。

> DeepSeek 官方（`api.deepseek.com/anthropic`）专门做了完整适配，可以直连不需要代理。

---

### 坑 2：Gateway URL 用 localhost 无法连接

**现象**：Gateway URL 填 `http://localhost:8082`，连接失败。

**修复**：必须用 `http://127.0.0.1:8082`，Claude Desktop 只允许 IP 地址形式的本地连接。

---

### 坑 3：系统代理/Clash 导致本地请求被拦截

**现象**：开了 Clash 后 Claude Desktop 连不上本地代理。

**原因**：Clash TUN 模式或系统代理会拦截所有 HTTP 请求，包括发往 `127.0.0.1` 的。

**修复**：
- Clash 规则中添加 `127.0.0.1` 和 `localhost` 到 DIRECT
- 或在 Clash 设置中排除本地地址

---

### 坑 4：Claude Desktop 自动更新被墙

**现象**：启动时卡在 "Checking for updates"，或更新下载失败。

**原因**：更新服务器在国外，国内无法直接访问。

**修复**：
```powershell
# 注册表禁用自动更新
Set-ItemProperty -Path "HKCU:\SOFTWARE\Policies\Claude" -Name "disableAutoUpdates" -Value 1 -Type DWord
```

需要手动更新时：开 Clash + 浏览器访问 `claude.ai/download` 下载安装包。

---

### 坑 5：模型名在下拉框中显示异常

**现象**：注册表里填了 `mimo-v2.5-pro`，Claude Desktop 显示为 `Mim* 2 Pro`。

**原因**：Claude Desktop 会解析模型名生成"美化"的显示名，小写+带点号的名字会被错误解析。

**修复**：注册表里用大写驼峰命名（如 `MiMo-V2.5-Pro`），proxy 内部再映射回 API 需要的小写名。

**规则**：所有注册到 Claude Desktop 的模型名都用 **大写首字母+连字符** 格式。

---

### 坑 6：新增模型不显示在模型选择器中

**现象**：proxy.py 添加了新模型，重启后模型选择器里没有。

**原因**：Claude Desktop 3P 模式有两种模型列表来源，且**互相覆盖**：

| 方式 | 来源 | 优先级 |
|------|------|--------|
| **UI 手动列表** | "管理第三方供应商" → Connection 页面手动添加 | **高**（覆盖自动发现） |
| **/v1/models 自动发现** | proxy 的 `GET /v1/models` 端点返回 | **低**（仅 UI 列表为空时生效） |

**修复**（二选一）：
1. 在 UI 里手动添加新模型名
2. **推荐**：清空 UI 手动列表，改用 `/v1/models` 自动发现（以后 proxy 加新模型自动出现）

---

### 坑 7：Cowork 沙箱 VM 启动失败（MSIX 路径不匹配）

**现象**：Cowork 任务永远卡在 "starting"，bash 命令无法运行。

**原因**：Claude Desktop 以 MSIX 格式安装，VM 文件下载路径与 VM 服务查找路径不匹配。

**修复**（用文件硬链接）：
```powershell
$roaming = "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude-3p\vm_bundles\claudevm.bundle"
New-Item -ItemType Directory -Path $roaming -Force | Out-Null

$src = "$env:LOCALAPPDATA\Claude-3p\vm_bundles\claudevm.bundle"
Get-ChildItem $src -File | ForEach-Object {
    cmd /c mklink /H "$roaming\$($_.Name)" "$($_.FullName)"
}

Remove-Item "$src\.auto_reinstall_attempted" -ErrorAction SilentlyContinue
Remove-Item "$roaming\.auto_reinstall_attempted" -ErrorAction SilentlyContinue
# 重启 Claude Desktop
```

**注意**：必须用文件级硬链接（`mklink /H`），不能用 junction（目录符号链接），VM 服务会拒绝 junction。

---

### 坑 8：MCP 配置文件不生效（MSIX 虚拟化）

**现象**：`claude_desktop_config.json` 已配置 MCP 服务器，但 Claude Desktop 显示"未添加服务器"。

**原因**：MSIX 文件系统虚拟化。外部工具写入真实 `%APPDATA%\Claude\`，但 Claude Desktop 读取 MSIX 虚拟化路径。

**修复**：
```powershell
$msixClaude = "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude"
if (!(Test-Path $msixClaude)) { New-Item -ItemType Directory -Path $msixClaude -Force | Out-Null }
Copy-Item "$env:APPDATA\Claude\claude_desktop_config.json" "$msixClaude\claude_desktop_config.json" -Force
```

**MSIX 路径规律**：

| 资源类型 | 真实路径 | MSIX 虚拟化路径 |
|---------|---------|----------------|
| VM Bundle | `%LOCALAPPDATA%\Claude-3p\` | `Packages\Claude_xxx\LocalCache\Roaming\Claude-3p\` |
| 配置文件 | `%APPDATA%\Claude\` | `Packages\Claude_xxx\LocalCache\Roaming\Claude\` |

> **经验**：凡是 Claude Desktop 的文件，外部修改后都要检查 MSIX 虚拟化路径是否同步。

---

### 坑 9：3P 配置文件位置找不到

**说明**：3P 模式的 Gateway 配置不在注册表，也不在 `claude_desktop_config.json`，而是在：

```
%LOCALAPPDATA%\Claude-3p\configLibrary\
├── _meta.json                              ← 配置索引
└── 685d6dd8-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json  ← Gateway 连接配置
```

通常通过 Claude Desktop UI 设置，排查问题时需要知道这个位置。

---

### 坑 10：Proxy 崩溃后 Claude Desktop 无法连接

**现象**：频繁出现 "The provider didn't respond" 错误。

**修复**：使用 `scripts/proxy-loop.bat` 启动（自动重启循环），配合 `proxy.py` 的全局异常捕获，确保 proxy 永不掉线。

---

## Codex CLI / Claude Code 相关

### 坑 11：Claude Code 环境变量在新终端窗口失效

**现象**：设置了 `$env:ANTHROPIC_BASE_URL`，关闭终端后再打开就没了。

**原因**：PowerShell `$env:` 只在当前进程有效，不会持久化。

**修复**：使用 `scripts/claude-switch.ps1` 快速设置，或写入 PowerShell Profile：
```powershell
# 写入 $PROFILE（每次打开终端自动加载）
Add-Content $PROFILE '. "路径\scripts\claude-switch.ps1" codex'
```

---

### 坑 12：Codex CLI 流式输出中断

**现象**：Codex CLI 长时间任务中途断开。

**原因**：中转站连接超时，或网络不稳定导致 SSE 流中断。

**修复**：`codex-proxy.py` 已设置 300 秒超时和连接保活。如仍有问题，检查网络稳定性。

---

## 通用问题

### Windows curl 不走系统代理

**现象**：在终端里 curl API 地址返回连接超时，但浏览器可以访问。

**原因**：Windows 的 curl 默认不走系统代理（Clash）。

**修复**：手动指定代理：
```powershell
curl -x http://127.0.0.1:7897 https://api.example.com/v1/models
```

---

## 注册表策略速查

### Gateway 连接

| 键名 | 类型 | 说明 |
|------|------|------|
| `inferenceProvider` | String | `gateway` / `bedrock` / `vertex` / `foundry` |
| `inferenceGatewayBaseUrl` | String | Gateway URL（HTTP 仅允许 127.0.0.1） |
| `inferenceGatewayApiKey` | String | API Key |
| `inferenceGatewayAuthScheme` | String | `x-api-key` / `bearer` |
| `inferenceModels` | String (JSON) | 模型列表 JSON 数组 |

### Cowork / MCP / 工具

| 键名 | 类型 | 说明 |
|------|------|------|
| `enableCowork` | DWORD | `1` 启用 Cowork 模式 |
| `coworkEnabled` | DWORD | `1` 同上（两个都设，确保生效） |
| `isLocalDevMcpEnabled` | DWORD | `1` 允许用户添加本地 MCP 服务器 |
| `disableAutoUpdates` | DWORD | `1` 禁止自动更新 |
| `coworkEgressAllowedHosts` | String (JSON) | Cowork 出站白名单，`["*"]` = 全放行 |

注册表路径：`HKCU:\SOFTWARE\Policies\Claude`
