# Changelog

本项目版本变更记录，遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 格式。

## [2.0.0] - 2025-05-02

### 新增
- 架构设计文档 `docs/architecture.md`：协议差异分析、流式翻译状态机、设计决策说明
- 20 个单元测试覆盖协议转换核心逻辑
- Docker 容器化部署（Dockerfile + docker-compose.yml）
- GitHub Actions CI（ruff lint + pytest）
- 贡献指南 CONTRIBUTING.md
- 中文版架构图 Banner

### 改进
- 代码全面添加 type hints 和 docstrings
- `print` 日志替换为结构化 `logging` 模块
- 模块注释从英文更新为中英双语
- codex-proxy.py 修复 `global` 声明位置（SyntaxError）

### 不变
- 所有运行时行为完全兼容，无破坏性变更
- 端口配置不变：8082（代理）、8083（控制面板）、5678（Codex 代理）
- secrets.json 格式不变

## [1.0.0] - 2025-04-20

### 新增
- proxy.py：Claude Desktop 多提供商网关代理
- codex-proxy.py：Codex CLI / Claude Code 协议转换代理
- 多提供商路由：SophNet、aiproxies.cc、小米 MiMo
- Anthropic ↔ OpenAI 协议双向转换（含流式 SSE）
- 浏览器控制面板实时切换模型
- AI 图片生成路由（Responses API）
- Windows 开机自启脚本
- 密钥管理（secrets.json）
- 故障排查文档
