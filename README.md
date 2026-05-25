# AI Agent for Jad

基于 Claude API 的个人 AI Agent，支持工具调用、对话记忆和多步任务执行。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 ANTHROPIC_API_KEY

# 3. 启动交互式对话
python main.py
```

## 项目结构

```
AI-Agent-for-Jad/
├── agent/
│   ├── core.py        # Agent 主循环
│   └── memory.py      # 对话记忆管理
├── tools/
│   └── definitions.py # 工具定义与执行
├── tests/             # 测试套件
├── examples/          # 使用示例
├── main.py            # CLI 入口
└── requirements.txt
```

## 内置工具

| 工具 | 功能 |
|------|------|
| `web_search` | 搜索互联网获取最新信息 |
| `read_file` | 读取本地文件 |
| `write_file` | 写入本地文件 |
| `run_python` | 执行 Python 代码 |
| `list_directory` | 浏览文件系统 |

## 运行测试

```bash
pip install pytest
pytest tests/ -v
```
