# feishu_agent_send - 飞书多 Agent 通信工具

**版本：** 3.1.0  
**定位：** 一个 skill，所有 agent 共用，自动识别身份

⚠️ **安全声明：** 本 skill 使用 `feishu_im_user_message` 以**用户身份**发送飞书消息。请确保只在你信任的 Agent 之间使用，避免敏感信息泄露。

## 🚀 快速开始

### 1. 首次设置（每个 Agent 必做）

```bash
# 设置当前 Agent 的 self 信息
python3 ~/.openclaw/skills/feishu_agent_send/tools/feishu_set_self.py <Agent名> <你的chat_id>

# 示例
python3 feishu_set_self.py kfj oc_xxx
```

### 2. 添加其他 Agent

```bash
python3 feishu_add.py <目标Agent> <chat_id> [--chat-type p2p|group]

# 示例
python3 feishu_add.py ying oc_xxx
python3 feishu_add.py ying oc_yyy --chat-type group
```

### 3. 发送消息（推荐 --deliver）

```bash
# v3.1.0 推荐：一站式发送
python3 feishu_send.py ying "你好" --deliver

# 预览模式（不输出发送指令）
python3 feishu_send.py ying "你好"
```

## 🛠️ 工具列表

| 工具 | 用途 | 推荐 |
|------|------|------|
| `feishu_send.py --deliver` | **一站式发送**（输出 `feishu_im_user_message` 调用指令） | ⭐⭐⭐ |
| `feishu_send.py` | 预览消息（返回格式化后的消息和参数） | ⭐ |
| `feishu_set_self.py` | 设置自己的发送者信息 | 仅首次 |
| `feishu_add.py` | 添加其他 Agent（支持多场景） | 配置时 |
| `feishu_who.py` | 查看所有 Agent 配置（JSON 输出） | 查询 |

## ✨ v3.1.0 改进

### 1. 统一 JSON 输出
所有工具（成功和失败）统一输出 JSON，方便脚本解析和 AI 处理。

### 2. 修复 `feishu_add.py` 数据迁移 Bug
旧格式（单 `chat_id`）升级到新格式（场景结构 `p2p`/`group`）时，不再污染数据。

### 3. 改进消息元数据格式
从 HTML 注释 `<!--from:xxx-->` 升级为 **JSON 元数据块**，接收方可稳定解析：
```
元数据：{"from_agent":"kfj","to_agent":"ying","chat_type":"p2p","timestamp":"2024-...","version":"3.1.0"}
```

### 4. 清理硬编码路径
移除项目特定的日志路径 `/root/.openclaw/self-evolving-feishu/storage/execution_log.jsonl`。

### 5. 移除无依据的延迟提示
删除"群消息需等待 6 秒"的提示（飞书 API 无此限制）。

### 6. 代码精简
- 删除死代码 `ConfigManager` 类
- 移除 `AgentConfig` 无意义的单例模式
- 修复 `detect_current_agent` 的路径前缀匹配 Bug

## 📋 配置结构

```json
{
  "version": "3.1.0",
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
# 输出中会有："available_agents": ["ying", "kfj", "main"]

# 解决：添加该 Agent
python3 feishu_add.py test oc_xxx
```

**Q: 报错"无效的 chat_type: 'xxx'"？**  
A: `--chat-type` 只接受 `p2p` 或 `group`，其他值会报错并列出有效选项
```bash
# 正确用法
python3 feishu_send.py ying "消息" --chat-type p2p   # 私聊
python3 feishu_send.py ying "消息" --chat-type group  # 群聊
```

**Q: 多场景配置怎么用？**  
A: 默认选择私聊，如需发群聊加 `--chat-type group`
```bash
# Agent 同时有私聊和群聊配置时，JSON 中会包含：
# "scene_hint": "Agent 'ying' 有多个配置：私聊、群聊。已自动选择：私聊。如需切换，请使用：--chat-type group"
```

## 📚 错误输出格式（统一 JSON）

所有输出均为 JSON，方便解析：

| 场景 | 字段 |
|------|------|
| 成功发送 | `success`, `send_params`, `preview`, `chat_id`, `chat_type`, `to`, `from_agent` |
| 缺少发送者 | `success`, `error`, `hint`, `v3.1.0_help` |
| 找不到Agent | `success`, `error`, `available_agents`, `v3.1.0_help` |
| 无效chat_type | `success`, `error`, `valid_options`, `hint` |

**示例错误输出**：
```json
{
  "success": false,
  "error": "找不到 Agent 'test'",
  "available_agents": ["ying", "kfj", "main"],
  "v3.1.0_help": "请先添加：python3 feishu_add.py test oc_xxx"
}
```

## 版本历史

| 版本 | 功能 |
|------|------|
| v3.1.0 | 统一 JSON 输出、修复 add Bug、JSON 元数据、清理硬编码路径、代码精简 |
| v3.0.0 | --deliver一站式发送、多场景提示、用户语言错误、chat_type验证 |
