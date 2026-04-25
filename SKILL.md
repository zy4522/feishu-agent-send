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
python3 <skill路径>/tools/feishu_send.py <目标> "消息" --deliver    # 输出调用指令
python3 <skill路径>/tools/feishu_send.py <目标> "消息" --execute   # 直接发送
```

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

## 🐛 常见问题

**Q: 报错"缺少发送者信息"？**  
A: 首次使用必须运行 `feishu_set_self.py`

**Q: 报错"找不到 Agent 'xxx'"？**  
A: 按提示添加：`python3 feishu_add.py xxx oc_xxx`

**Q: 群聊没有 @ 提醒？**  
A: 先运行 `feishu_scan_group.py <群chat_id>` 采集 app_id

**Q: 多场景配置怎么用？**  
A: 默认选私聊，发群聊加 `--chat-type group`

**Q: 扫描时显示"未匹配的机器人"？**  
A: 在 `config.json` 中添加 `name_mappings` 配置

## 版本历史

| 版本 | 功能 |
|------|------|
| v3.9.0 | --execute一站式发送、feishu_direct_send.py独立模块、UAT解密、parse_agent_message()实现、批量发送、版本号统一修复 |
| v3.8.0 | 修复--execute假执行、修复feishu_status.py误报、统一版本号、parse_agent_message骨架、批量发送骨架 |
| v3.7.0 | 单self自动选择、--execute直接执行、feishu_status.py诊断工具、配置防呆检查、消息来源标识优化、--actual-sender双身份支持 |
| v3.6.0 | 合并群聊@功能与代码改进：JSON元数据、代码精简、Bug修复 |
| v3.5.0 | 群聊post富文本格式、@提醒、群初始化采集app_id |
| v3.4.0 | 删除不可用--send、修复get_agent_info、统一代理发送者字段 |
| v3.2.0 | main路径检测、消息格式规范、openclaw.json绑定检查 |
| v3.0.1 | 群消息延迟发送、移除真实chat_id |
| v3.0.0 | --deliver一站式发送、多场景提示、用户语言错误、chat_type验证 |
