# 贡献指南

感谢你对 API Gateway 项目的关注！欢迎提交 Issue 和 Pull Request。

## 开发环境

```bash
# 克隆仓库
git clone https://github.com/cheershuyang/api-gateway.git
cd api-gateway

# 安装依赖
pip install -r requirements.txt
pip install pytest ruff

# 复制密钥模板
cp secrets.example.json secrets.json
# 编辑 secrets.json，填入你的 API Key
```

## 代码规范

- **Python 3.10+**，使用 type hints
- **结构化日志**：使用 `logging` 模块，不使用 `print`
- **Lint**：`ruff check . --select E,F,W --ignore E501`
- **测试**：`python -m pytest tests/ -v`

## 提交 PR 前

1. 确保所有测试通过：`python -m pytest tests/ -v`
2. 确保 lint 无报错：`ruff check .`
3. 如果修改了协议转换逻辑，请添加对应的测试用例
4. PR 描述中说明修改动机和测试方法

## 添加新提供商

参考 `docs/architecture.md` 第 6 节"可扩展性"，添加新提供商只需：

1. 在 `proxy.py` 中添加模型字典和路由函数
2. 在 `secrets.json` 中添加对应的 API Key
3. 在控制面板 HTML 中添加模型选项
4. 添加测试用例

## Issue 规范

- **Bug 报告**：附上错误日志、Python 版本、操作系统
- **功能请求**：描述使用场景和预期行为
- **提供商适配**：说明提供商 API 文档链接和协议格式
