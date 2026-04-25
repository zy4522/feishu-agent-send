# feishu_agent_send - 飞书多 Agent 通信工具

**版本：** 3.9.0（版本号统一在 `_version.py`，所有工具从此引用）  
**定位：** 一个 skill，所有 agent 共用，自动识别身份

⚠️ **安全声明：** 本 skill 使用 `feishu_im_user_message` 以**用户身份**发送飞书消息。确保只在你信任的 Agent 之间使用。

## 🚀 快速开始

### 1. 首次设置（每个 Agent 必做）

```bash
python3 <skill路径>/tools/feishu_set_self.py <Agent名> <你的chat_id>
# 例：python3 tools/feishu_set_self.py kfj oc_xxx
```

### 2. 添加其他 Agent

```bash
python3 <skill路径>/tools/feishu_add.py <目标Agent> <chat_id>
```

### 3. 群聊初始化（采集 app_id，群聊 @ 功能必需）

```bash
python3 <skill路径>/tools/feishu_scan_group.py <群chat_id>
```

### 4. 发送消息

```bash
python3 <skill路径>/tools/feishu_send.py <目标> "消息" --deliver    # 输出调用指令，推荐审查后执行
python3 <skill路径>/tools/feishu_send.py <目标> "消息" --execute   # 直接发送（信任场景）
```

> **版本管理：** 所有工具的版本号从 `_version.py` 统一读取，升版本只需改一处。

## 🛠️ 工具列表

| 工具 | 用途 |
|------|------|
| `feishu_send.py --deliver` | 一站式发送，输出 `feishu_im_user_message` 调用指令 ⭐⭐⭐ |
| `feishu_send.py --execute` | 直接调用飞书 API 发送 ⭐⭐⭐ |
| `feishu_send.py`（无参数） | 预览 JSON（调试用） |
| `feishu_status.py` | 配置诊断（检查/修复） |
| `feishu_set_self.py` | 设置自己的发送者信息（首次必做） |
| `feishu_add.py` | 添加其他 Agent |
| `feishu_scan_group.py` | 扫描群成员采集 app_id（群初始化） |
| `feishu_who.py` | 查看所有 Agent 配置信息 |
| `feishu_direct_send.py` | 底层 API 发送（供其他脚本调用） |
| `parse_agent_message.py` | 解析收到的代理消息 |

## 📖 消息标准格式

### 私聊格式（text）

```
📨【私信】【代理】【{发送者}→{接收者}】

{消息正文}

---
实际发送者：{发送者}
代理发送者：用户
元数据：{"from_agent":"xxx","to_agent":"xxx","chat_type":"p2p","timestamp":"...","version":"..."}
---
```

### 群聊格式（post 富文本）

自动包含 @ 目标 Agent 提醒，title 格式：`【代理消息】@目标 来自 发送者`

### 解析规则

接收方按优先级提取：
1. JSON 元数据块 → 真实发送者（私聊）
2. post title 和内容 → 路由信息（群聊）
3. 元数据 `from_chat_id` → 发送者会话 ID（用于回复）

## 📋 配置结构

配置文件：`~/.feishu_agent_send/config.json`

```json
{
  "version": "3.9.0",
  "agents": {
    "ying": {
      "p2p": {"chat_id": "oc_xxx"},
      "group": {"chat_id": "oc_yyy", "app_id": "cli_xxx"}
    }
  },
  "self_by_agent": {
    "kfj": {"chat_id": "oc_xxx"}
  },
  "name_mappings": {
    "ying": ["颖", "ying", "颖小兔"]
  }
}
```

**说明：**
- `app_id` 通过 `feishu_scan_group.py` 自动采集，无需手动配置
- `name_mappings` 用于群聊 @ 功能，将飞书机器人名称映射到 Agent 名称

## 🐛 常见问题（关键词索引）
`missing_sender` · `agent_not_found` · `no_at_reminder` · `multi_scene` · `unmatched_bot`

**Q: 报错"缺少发送者信息"？** (`missing_sender`)  
A: 首次使用必须运行 `feishu_set_self.py`

**Q: 报错"找不到 Agent 'xxx'"？** (`agent_not_found`)  
A: 按提示添加：`python3 feishu_add.py xxx oc_xxx`

**Q: 群聊没有 @ 提醒？** (`no_at_reminder`)  
A: 先运行 `feishu_scan_group.py <群chat_id>` 采集 app_id

**Q: 多场景配置怎么用？** (`multi_scene`)  
A: 默认选私聊，发群聊加 `--chat-type group`

**Q: 扫描时显示"未匹配的机器人"？** (`unmatched_bot`)  
A: 在 `config.json` 中添加 `name_mappings` 配置

## 版本历史 | 完整变更见 [CHANGELOG.md](CHANGELOG.md)

| 版本 | 功能 |
|------|------|
| v3.9.0 | --execute一站式发送、feishu_direct_send.py独立模块、批量发送、版本号统一、安全加固、文档瘦身 |
