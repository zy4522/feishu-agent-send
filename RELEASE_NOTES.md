# Release Notes v1.1.0

## 新增功能

### 🚀 一键发送函数
- `feishu_agent_send_and_deliver()` - 自动完成格式化和发送准备

### ⚙️ 配置化支持
- 从配置文件加载 Agent 映射
- 支持运行时添加/删除 Agent
- 配置文件位置：`~/.feishu_agent_send/config.json`

### 🔍 动态发现（框架）
- 预留动态发现接口
- 可扩展实现自动查找 chat_id

### 🛠️ 首次建立机制
- `setup_agent()` - 运行时添加新 Agent
- `list_known_agents()` - 列出所有已知 Agent

## 改进

- 移除硬编码映射，改用配置文件
- 支持自定义配置文件路径
- 更好的错误提示
- 完整的文档和示例

## 文件结构

```
feishu-agent-send/
├── README.md              # 项目说明
├── LICENSE                # MIT 许可证
├── setup.py               # 安装脚本
├── config.json            # 默认配置
├── feishu_agent_send.py   # 核心代码
├── feishu_agent_send_integration.py  # 集成模块
├── SKILL.md               # 详细文档
├── examples/              # 示例代码
│   └── basic_usage.py
└── .gitignore
```

## 安装

```bash
pip install feishu-agent-send
```

## 快速开始

```python
from feishu_agent_send import setup_agent, feishu_agent_send_and_deliver

# 1. 配置 Agent
setup_agent("助手", chat_id="oc_xxx")

# 2. 发送消息
result = feishu_agent_send_and_deliver(
    to="助手",
    message="你好！",
    from_agent="我"
)

# 3. 实际发送
feishu_im_user_message(**result["send_params"])
```

## GitHub 仓库

https://github.com/openclaw/feishu-agent-send
