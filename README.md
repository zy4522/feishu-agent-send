# feishu_agent_send

飞书多 Agent 通信工具 - 一个 skill，所有 agent 共用，自动识别身份

## 版本

v3.1.0

## 功能

- ✅ 一站式发送（`--deliver`）
- ✅ 多场景智能提示（私聊/群聊）
- ✅ 统一 JSON 输出
- ✅ chat_type 参数验证

## 快速开始

```bash
# 设置当前 Agent 的发送者信息
python3 tools/feishu_set_self.py <Agent名> <你的chat_id>

# 发送消息
python3 tools/feishu_send.py <目标Agent> "消息内容" --deliver
```

## 文档

详细配置和使用说明见 [SKILL.md](SKILL.md)

## 作者

zy4522 (张彦)

## License

MIT

<!-- auto-sync test: 2026-04-23T15:46:00Z -->
