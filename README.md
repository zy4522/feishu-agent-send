# feishu-agent-send

飞书Agent通信工具 - 通用版

让多个 AI Agent 通过飞书通道互相通信，支持代理发送、自动格式化和动态发现。

## 特性

- 🚀 **一键发送** - 自动格式化消息并准备发送参数
- 🔍 **动态发现** - 自动查找 Agent 的 chat_id
- ⚙️ **配置化** - 通过配置文件管理 Agent 映射
- 🛠️ **首次建立** - 支持运行时添加新 Agent
- 📦 **零依赖** - 纯 Python 实现，易于集成

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/feishu-agent-send.git
cd feishu-agent-send

# 安装
pip install -e .
```

## 快速开始

### 1. 首次配置

```python
from feishu_agent_send import setup_agent

# 添加你的第一个 Agent
setup_agent(
    name="我的Agent",
    chat_id="oc_xxx",  # 从飞书获取
    open_id="ou_xxx"   # 可选
)
```

### 2. 发送消息

```python
from feishu_agent_send import feishu_agent_send_and_deliver

# 一键准备发送
result = feishu_agent_send_and_deliver(
    to="我的Agent",
    message="你好！",
    from_agent="另一个Agent"
)

# 使用飞书工具实际发送
feishu_im_user_message(**result["send_params"])
```

## 配置说明

配置文件位置：`~/.feishu_agent_send/config.json`

```json
{
  "version": "1.1.0",
  "agents": {
    "AgentA": {
      "chat_id": "oc_xxx",
      "open_id": "ou_xxx",
      "created_at": "2024-01-01T00:00:00"
    }
  },
  "discovery": {
    "enabled": true,
    "cache_duration_hours": 24
  }
}
```

## API 文档

### feishu_agent_send_and_deliver()

一键发送函数，自动完成格式化和发送准备。

```python
result = feishu_agent_send_and_deliver(
    to="目标Agent",
    message="消息内容",
    from_agent="发送者Agent"
)
```

### setup_agent()

首次建立 Agent 映射。

```python
setup_agent(
    name="Agent名称",
    chat_id="oc_xxx",  # 可选
    open_id="ou_xxx"   # 可选
)
```

### get_chat_id()

查询 Agent 的 chat_id。

```python
chat_id = get_chat_id("Agent名称")
```

## 获取 chat_id 的方法

### 方法1：从飞书客户端获取
1. 打开飞书，进入与目标 Agent 的会话
2. 从 URL 中提取 chat_id（oc_xxx 格式）

### 方法2：通过 API 获取
```python
# 让目标 Agent 先发一条消息
# 然后使用飞书 API 查询会话列表
```

### 方法3：动态发现（开发中）
```python
# 启用动态发现功能
# 自动从历史消息中查找
```

## 完整示例

```python
import sys
sys.path.insert(0, '/path/to/feishu-agent-send')

from feishu_agent_send import (
    setup_agent,
    feishu_agent_send_and_deliver,
    list_known_agents
)

# 1. 配置 Agent
setup_agent("助手A", chat_id="oc_xxx")

# 2. 查看已配置的 Agent
agents = list_known_agents()
print(agents)

# 3. 发送消息
result = feishu_agent_send_and_deliver(
    to="助手A",
    message="请汇报进度",
    from_agent="助手B"
)

# 4. 实际发送（使用你的飞书工具）
feishu_im_user_message(**result["send_params"])
```

## 注意事项

1. **chat_id  vs open_id**
   - chat_id (oc_xxx): 用于群聊和单聊，推荐
   - open_id (ou_xxx): 用于直接@用户

2. **跨应用问题**
   - 不同飞书应用间的 open_id 不互通
   - 使用 chat_id 可以避免此问题

3. **权限要求**
   - 需要飞书 API 权限
   - 需要能够发送消息到目标会话

## 许可证

MIT License

## 反馈与支持

- 🐛 **Bug 报告**: [提交 Issue](https://github.com/zy4522/feishu-agent-send/issues)
- 💡 **功能建议**: [提交 Issue](https://github.com/zy4522/feishu-agent-send/issues)
- 📧 **联系作者**: 通过 GitHub Issues 留言

## 贡献

欢迎提交 Issue 和 PR！
