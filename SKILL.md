# feishu_agent_send - 飞书多 Agent 通信工具

**版本：** 3.0.0  
**定位：** 一个 skill，所有 agent 共用，自动识别身份

## 🚀 快速开始

### 1. 首次设置（每个 Agent 必做）

```bash
# 设置当前 Agent 的 self 信息
python3 ~/.openclaw/skills/feishu_agent_send/tools/feishu_set_self.py <Agent名> <你的chat_id>

# 示例
python3 feishu_set_self.py kfj oc_4811eda51e2e9626fc7dfea21882942b
```

### 2. 添加其他 Agent

```bash
python3 feishu_add.py <目标Agent> <chat_id>

# 示例
python3 feishu_add.py ying oc_9c8528a08be665f04bfa857e07cd535d
```

### 3. 发送消息（推荐 --deliver）

```bash
# v3.0.0 推荐：一站式发送
python3 feishu_send.py ying "你好" --deliver

# 预览模式（不调用的发送）
python3 feishu_send.py ying "你好"
```

## 🛠️ 工具列表

| 工具 | 用途 | 推荐 |
|------|------|------|
| `feishu_send.py --deliver` | **一站式发送**（推荐） | ⭐⭐⭐ |
| `feishu_send.py` | 预览消息 | ⭐ |
| `feishu_set_self.py` | 设置自己的发送者信息 | 仅首次 |
| `feishu_add.py` | 添加其他 Agent | 配置时 |
| `feishu_who.py` | 查看所有 Agent | 查询 |

## ✨ v3.0.0 新功能

### 1. --deliver 一站式发送

输出完整的 `feishu_im_user_message` 调用指令 + 日志记录提示

### 2. 多场景智能提示

当 Agent 同时有私聊+群聊配置时，自动提示并给出切换指令

### 3. 用户语言错误提示

错误信息不再是技术术语，而是分步骤的解决指引

## 📋 配置结构

```json
{
  "version": "3.0.0",
  "agents": {
    "ying": {
      "p2p": {"chat_id": "oc_xxx"},
      "group": {"chat_id": "oc_yyy"}
    },
    "kfj": {
      "p2p": {"chat_id": "oc_xxx"}
    }
  },
  "self_by_agent": {
    "kfj": {"chat_id": "oc_xxx"},
    "main": {"chat_id": "oc_xxx"}
  }
}
```

配置文件位置：`~/.feishu_agent_send/config.json`

## 📝 使用流程

```bash
# 1. 设置自己
python3 feishu_set_self.py <你的Agent名> <你的chat_id>

# 2. 添加常用联系人
python3 feishu_add.py <目标Agent> <目标chat_id>

# 3. 发送消息（--deliver 模式）
python3 feishu_send.py <目标> "消息" --deliver

# 4. 执行输出的 feishu_im_user_message 调用
```

## 🐛 常见问题与错误处理

**Q: 报错"缺少发送者信息"？**  
A: 首次使用必须运行 `feishu_set_self.py` 设置自己的 chat_id
```bash
python3 feishu_set_self.py <你的Agent名> oc_xxx
```

**Q: 报错"找不到 Agent 'xxx'"？**  
A: 工具会自动列出可用 Agent，按提示添加：
```bash
# 错误示例：找不到 'test'
# 输出：available_agents: ['ying', 'kfj', 'main']

# 解决：添加该 Agent
python3 feishu_add.py test oc_xxx
```

**Q: 报错"无效的 chat_type: 'xxx'"？**  
A: `--chat-type` 只接受 `p2p` 或 `group`，其他值会报错并列出有效选项
```bash
# 错误示例：--chat-type private
# 输出：valid_options: ['p2p', 'group']

# 正确用法
python3 feishu_send.py ying "消息" --chat-type p2p   # 私聊
python3 feishu_send.py ying "消息" --chat-type group  # 群聊
```

**Q: 多场景配置怎么用？**  
A: 默认选择私聊，如需发群聊加 `--chat-type group`
```bash
# Agent 同时有私聊和群聊配置时，会提示：
# ⚠️ Agent 'ying' 有多个配置：私聊、群聊
#    已自动选择：私聊
#    如需切换，请使用：--chat-type group
```

## 📚 错误输出格式（v3.0.0 用户语言）

所有错误都包含以下字段，方便快速定位问题：

| 错误类型 | 输出字段 | 示例 |
|---------|---------|------|
| 缺少发送者 | `error`, `hint`, `v3.0.0_help` | "首次使用请运行 feishu_set_self.py" |
| 找不到Agent | `error`, `available_agents`, `v3.0.0_help` | "找不到 'test'，可用: ying, kfj" |
| 无效chat_type | `error`, `valid_options`, `hint` | "无效 'private'，有效: p2p, group" |

**示例输出**：
```json
{
  "success": false,
  "error": "找不到 Agent 'test'",
  "available_agents": ["ying", "kfj", "main"],
  "v3.0.0_help": "请先添加：python3 feishu_add.py test oc_xxx"
}
```

## 版本历史

| 版本 | 功能 |
|------|------|
| v3.0.0 | --deliver一站式发送、多场景提示、用户语言错误、chat_type验证 |
