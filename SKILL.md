# feishu_agent_send - 飞书多 Agent 通信工具

**版本：** 3.9.0  
**定位：** 一个 skill，所有 agent 共用，自动识别身份

⚠️ **安全声明：** 本 skill 使用 `feishu_im_user_message` 以**用户身份**发送飞书消息。请确保只在你信任的 Agent 之间使用，避免敏感信息泄露。

## 🚀 快速开始

### 1. 首次设置（每个 Agent 必做）

```bash
# 设置当前 Agent 的 self 信息
python3 ~/.openclaw/skills/feishu-agent-send/tools/feishu_set_self.py <Agent名> <你的chat_id>

# 示例
python3 feishu_set_self.py kfj oc_xxx
```

### 2. 添加其他 Agent

```bash
python3 feishu_add.py <目标Agent> <chat_id>

# 示例
python3 feishu_add.py ying oc_xxx
```

### 3. 群聊初始化（采集 app_id）

**群聊 @ 功能需要先在群里采集各 Agent 的 app_id：**

```bash
# 方式一：全自动扫描（推荐）
python3 feishu_scan_group.py oc_xxx --auto

# 方式二：手动导入
# 步骤 1：在群里 @ 各 Agent 发一条消息（确保机器人在群里）
# 步骤 2：获取群成员列表
feishu_chat_members(
    chat_id='oc_xxx',
    page_size=200
)
# 步骤 3：保存结果到文件，然后导入
python3 feishu_scan_group.py oc_xxx --manual /tmp/group_members.json
```

采集完成后，后续群聊发送会自动使用 post 富文本格式并 @ 目标 Agent。

### 4. 配置诊断

```bash
# 检查所有配置
python3 feishu_status.py

# 检查指定 Agent
python3 feishu_status.py --check kfj

# 检查并自动修复
python3 feishu_status.py --fix
```

### 5. 发送消息

```bash
# 一站式发送（推荐）：输出 feishu_im_user_message 调用指令
python3 feishu_send.py ying "你好" --deliver

# 预览模式（仅输出 JSON，不调用）
python3 feishu_send.py ying "你好"
```

## 🛠️ 工具列表

| 工具 | 用途 | 推荐 |
|------|------|------|
| `feishu_send.py --deliver` | **一站式发送**（输出调用指令） | ⭐⭐⭐ |
| `feishu_send.py --execute` | **生成发送指令**（需手动执行） | ⭐⭐ |
| `feishu_status.py` | **配置诊断**（检查配置健康状态） | ⭐⭐⭐ |
| `feishu_send.py` | 预览 JSON（调试用） | ⭐ |
| `feishu_set_self.py` | 设置自己的发送者信息 | 仅首次 |
| `feishu_add.py` | 添加其他 Agent | 配置时 |
| `feishu_scan_group.py` | 扫描群成员采集 app_id | 群初始化 |
| `feishu_who.py` | 查看所有 Agent | 查询 |

## ✨ v3.9.0 改进（2026-04-25）

### 1. --execute 一站式发送
`--execute` 模式升级为真正的一站式发送：直接调用飞书 API 完成消息发送，无需手动复制执行 `feishu_im_user_message` 调用指令：
```bash
python3 feishu_send.py ying "你好" --execute
# 输出：🚀 执行发送... ✅ 发送执行完成（message_id: om_xxx）
```
同时保留 `--deliver` 模式，输出完整调用指令供审查或手动执行。

### 2. feishu_direct_send.py 独立发送模块
新增独立发送模块，将发送逻辑从 `feishu_send.py` 解耦：
- 提供更底层的 API 调用接口
- 支持在其他脚本中直接复用发送能力
- 简化测试和调试流程

### 3. UAT 解密支持
增强实际发送者（actual-sender）的双身份支持，支持 UAT 环境解密，适配更复杂的生产场景。

### 4. parse_agent_message() 自动解析函数
新增消息解析函数，自动识别代理消息格式：
```python
{
    "is_agent_message": True,
    "from_agent": "kfj",
    "to_agent": "ying",
    "message": "消息正文",
    "chat_type": "p2p",
    "raw_content": {...}
}
```
支持自动识别 post/text 消息类型并提取代理消息内容。

### 5. 批量发送（逗号分隔多目标）
支持一次性向多个 Agent 发送相同消息：
```bash
python3 feishu_send.py "kfj,ying,zz" "消息" --deliver --chat-type group
```
使用逗号分隔多个目标 Agent，自动逐个发送。

### 6. 版本号统一修复
- SKILL.md 头部版本更新为 3.9.0
- feishu_status.py 内部版本号同步为 3.9.0
- 修复 feishu_status.py 版本检查误报问题（v3.9.0 修复）
- 修复 feishu_status.py 配置一致性检查误报问题（v3.9.0 修复）

---

## ✨ v3.8.0 改进（2026-04-24）
- 修复 `--execute` 假执行问题（改为真正调用 API）
- 修复 `feishu_status.py` 版本检查误报（配置版本与代码版本比较逻辑）
- 统一所有工具版本号为 3.8.0（SKILL.md、代码注释、配置检查）
- 新增 `parse_agent_message()` 消息解析函数骨架（v3.9.0 完成实现）
- 新增批量发送支持（逗号分隔多目标）
- 新增 `feishu_direct_send.py` 独立发送模块（v3.9.0 完成解耦）

---

## ✨ v3.7.0 改进（2026-04-24）
### 1. 单 self 自动选择
当配置文件中只有一个 self 配置时，`detect_current_agent()` 自动选择该配置，无需每次指定 `--from`：
```bash
# 之前：必须指定 --from
python3 feishu_send.py ying "你好" --from kfj --deliver

# 现在：自动检测
python3 feishu_send.py ying "你好" --deliver
# 输出：📝 自动检测发送者：kfj
```

### 2. --execute 直接执行模式
新增 `--execute` 参数，尝试直接调用 API 发送消息，无需手动复制指令：
```bash
python3 feishu_send.py ying "你好" --execute
# 输出：🚀 执行发送... ✅ 发送执行完成
```

### 3. feishu_status.py 配置诊断工具
新增诊断工具，快速检查配置状态：
```bash
# 检查所有配置
python3 feishu_status.py

# 检查指定 Agent
python3 feishu_status.py --check kfj

# 检查并自动修复
python3 feishu_status.py --fix
```

**诊断内容**：
- 版本号一致性检查
- Self 配置完整性
- Agents 配置完整性
- 配置一致性（重复 chat_id 检测）

### 4. 配置防呆检查
`feishu_set_self.py` 和 `feishu_add.py` 添加冲突检测：
- 检测 self 和 agent chat_id 重复（容易搞混自己和对方）
- 检测私聊 chat_id 重复（应该是唯一的）
- 群聊重复正常，不警告

### 5. 消息来源标识优化
群聊消息 title 格式统一为：
```
【代理消息】@目标 来自 发送者
```

示例：
```
【代理消息】@kfj 来自 kclaw
```

### 6. --actual-sender 双身份支持
支持区分实际发送者（人类）和代理执行者（AI）：
```bash
python3 feishu_send.py kfj "消息" --from kfj --actual-sender kclaw --deliver
# 显示：kclaw（经由 kfj）→ kfj
```

## ✨ v3.6.0 改进

### 1. 合并 v3.5.0 群聊 @ 功能与 v3.1.0 代码改进
- 保留群聊 post 富文本格式和 @ 提醒功能
- 吸收代码精简、Bug 修复、JSON 元数据等改进

### 2. 统一 JSON 元数据格式
从 HTML 注释 `<!--from:xxx-->` 升级为 **JSON 元数据块**：
```
元数据：{"from_agent":"kfj","to_agent":"ying","chat_type":"p2p","timestamp":"2024-...","version":"3.6.0"}
```

### 3. 代码精简
- 删除无意义的单例模式
- 修复 `detect_current_agent` 的路径前缀匹配 Bug
- 移除硬编码路径和延迟提示

### 4. 修复 `feishu_add.py` 数据迁移 Bug
旧格式升级到新格式时，不再污染数据。

## ✨ v3.5.0 群聊 @ 功能

### 1. 群聊自动使用 post 富文本格式

群聊发送时自动切换为 `msg_type='post'`，支持 @ 目标 Agent。

### 2. 群初始化引导

无需手动配置 app_id，通过群成员扫描自动采集：

```bash
# 扫描群成员并自动匹配已配置 Agent
python3 feishu_scan_group.py oc_xxx --import /tmp/group_members.json
```

### 3. 向后兼容

私聊继续沿用 `msg_type='text'` 纯文本格式，不受影响。

## ✨ v3.4.0 改进

### 1. 删除不可用的 --send 模式

之前尝试通过飞书 Bot API 直接发送，但 Bot 没有目标 chat 的成员权限（报 `Bot can NOT be out of the chat`），因此删除此功能，避免 Agent 困惑。

### 2. 修复 `get_agent_info()` 多场景判断逻辑

调整判断顺序：先检查多场景（p2p/group），再检查单场景（chat_id），避免多场景配置被错误识别。

### 3. 修复 `feishu_add.py` 升级逻辑

从单场景升级到多场景时，正确保留旧 chat_id 和对应的 chat_type。

### 4. 统一 "代理发送者" 字段

所有代码路径统一为 `{from_agent}`，避免不同文件输出不一致。

## ✨ v3.2.0 功能

- 自动身份检测增强：`detect_current_agent()` 支持 main Agent 在 workspace 根目录
- 消息格式规范：完整的消息结构说明
- openclaw.json 绑定检查：首次设置自动检查路由配置

## ✨ v3.0.0 功能

### 1. --deliver 一站式发送

输出完整的 `feishu_im_user_message` 调用指令 + 日志记录提示

### 2. 多场景智能提示

当 Agent 同时有私聊+群聊配置时，自动提示并给出切换指令

### 3. 用户语言错误提示

错误信息不再是技术术语，而是分步骤的解决指引

### 4. 群消息延迟发送

群消息（`--chat-type group`）会提示等待 6 秒后再执行发送，避免频繁发送

## 📖 消息标准格式

### 私聊格式（text）

所有 Agent 间私聊通信消息遵循以下统一格式：

```
📨【私信】【代理】【{发送者}→{接收者}】

{消息正文}

---
实际发送者：{发送者}
代理发送者：用户
元数据：{"from_agent":"xxx","to_agent":"xxx","chat_type":"p2p","timestamp":"...","version":"3.6.0"}
---
```

### 群聊格式（post）

群聊使用飞书富文本格式，自动包含 @ 提醒：

```json
{
  "zh_cn": {
    "title": "@{接收者} 你有新消息",
    "content": [
      [
        {"tag": "at", "user_id": "cli_xxx", "user_name": "{接收者}"},
        {"tag": "text", "text": "\n\n{消息正文}\n\n---\n📨 群聊代理发送 | {发送者} → {接收者}"}
      ]
    ]
  }
}
```

### 解析规则

接收方 Agent 应按以下优先级提取信息：
1. 从 JSON 元数据块提取真实发送者（私聊）
2. 从 post 消息 title 和内容提取路由信息（群聊）
3. 从元数据 `from_chat_id` 提取发送者会话 ID（用于回复）

## 📋 配置结构

```json
{
  "version": "3.6.0",
  "agents": {
    "ying": {
      "p2p": {"chat_id": "oc_xxx"},
      "group": {"chat_id": "oc_yyy", "app_id": "cli_xxx"}
    },
    "kfj": {
      "p2p": {"chat_id": "oc_xxx"},
      "app_id": "cli_xxx"
    }
  },
  "self_by_agent": {
    "kfj": {"chat_id": "oc_xxx"},
    "main": {"chat_id": "oc_xxx"}
  }
}
```

配置文件位置：`~/.feishu_agent_send/config.json`

**说明：**
- `app_id` 通过 `feishu_scan_group.py` 自动采集，无需手动配置
- 多场景配置中，`app_id` 可放在顶层或 group 子配置中

## 🏷️ 群聊 @ 功能配置（name_mappings）

群聊 @ 功能需要配置名称映射，将飞书机器人名称映射到 Agent 名称：

```json
{
  "version": "3.6.0",
  "name_mappings": {
    "ying": ["颖", "ying", "颖小兔"],
    "main": ["大总管", "main"],
    "iio": ["信息官", "iio"],
    "kfj": ["开发机", "kfj"],
    "zz": ["组长", "zz"],
    "ayy": ["啊呀呀", "ayy"],
    "cpaas": ["cpa", "cpaas", "学助", "CPA学习助理"]
  }
}
```

**配置说明：**
- 键：Agent 名称（与 `agents` 中的键一致）
- 值：字符串数组，包含该 Agent 在飞书中的所有可能名称/别名
- `feishu_scan_group.py` 会自动使用此配置匹配机器人

**默认值（内置）：**
如果 `config.json` 中没有 `name_mappings` 字段，系统会使用以下默认映射：

| Agent | 默认映射 |
|-------|---------|
| ying | ["颖", "ying"] |
| main | ["大总管", "main"] |
| iio | ["信息官", "iio"] |
| kfj | ["开发机", "kfj"] |
| zz | ["组长", "zz"] |
| ayy | ["啊呀呀", "ayy"] |
| cpaas | ["cpa", "cpaas", "学助"] |

**自定义示例：**
如果你的机器人名称与默认值不同，请在 `config.json` 中添加：

```json
{
  "name_mappings": {
    "my_agent": ["我的机器人", "my_bot"]
  }
}
```

## 📝 使用流程

```bash
# 1. 设置自己
python3 feishu_set_self.py <你的Agent名> <你的chat_id>

# 2. 添加常用联系人
python3 feishu_add.py <目标Agent> <目标chat_id>

# 3. 群聊初始化（如需要群聊 @ 功能）
# 方式A：全自动（从消息历史提取）
python3 feishu_scan_group.py <群chat_id>

# 方式B：手动导入（兼容旧版）
python3 feishu_scan_group.py <群chat_id> --manual <消息历史文件>

# 4. 发送消息（--deliver 模式）
python3 feishu_send.py <目标> "消息" --deliver

# 5. 执行输出的 feishu_im_user_message 调用
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

**Q: 群聊没有 @ 提醒？**  
A: 需要先运行群初始化采集 app_id：

```bash
# 全自动方式（推荐）
python3 feishu_scan_group.py oc_xxx

# 或手动方式
feishu_im_user_get_messages(chat_id='oc_xxx', page_size=100, relative_time='last_7_days')
# 保存结果后
python3 feishu_scan_group.py oc_xxx --manual /tmp/messages.json
```

**Q: 扫描时显示"未匹配的机器人"？**  
A: 需要在 `config.json` 中添加 `name_mappings` 配置：

```json
{
  "name_mappings": {
    "your_agent": ["飞书机器人名", "别名"]
  }
}
```

**Q: 多场景配置怎么用？**  
A: 默认选择私聊，如需发群聊加 `--chat-type group`
```bash
# Agent 同时有私聊和群聊配置时，会提示：
# ⚠️ Agent 'ying' 有多个配置：私聊、群聊
#    已自动选择：私聊
#    如需切换，请使用：--chat-type group
```

## 📚 错误输出格式（v3.6.0 统一 JSON）

所有输出均为 JSON，方便解析：

| 错误类型 | 输出字段 | 示例 |
|---------|---------|------|
| 缺少发送者 | `error`, `hint`, `v3.6.0_help` | "首次使用请运行 feishu_set_self.py" |
| 找不到Agent | `error`, `available_agents`, `v3.6.0_help` | "找不到 'test'，可用: ying, kfj" |
| 无效chat_type | `error`, `valid_options`, `hint` | "无效 'private'，有效: p2p, group" |
| 未采集app_id | `error`, `hint` | "请先运行 feishu_scan_group.py 采集 app_id" |

**示例输出**：
```json
{
  "success": false,
  "error": "找不到 Agent 'test'",
  "available_agents": ["ying", "kfj", "main"],
  "v3.6.0_help": "请先添加：python3 feishu_add.py test oc_xxx"
}
```

## 版本历史

| 版本 | 功能 |
|------|------|
| v3.9.0 | --execute一站式发送、feishu_direct_send.py独立模块、UAT解密、parse_agent_message()实现、批量发送、版本号统一修复 |
| v3.8.0 | 修复--execute假执行、修复feishu_status.py误报、统一版本号、parse_agent_message骨架、批量发送骨架 |
| v3.7.0 | 单self自动选择、--execute直接执行、feishu_status.py诊断工具、配置防呆检查、消息来源标识优化、--actual-sender双身份支持 |
| v3.6.0 | 合并 v3.5.0 群聊 @ 功能与 v3.1.0 代码改进：JSON 元数据、代码精简、Bug 修复 |
| v3.5.0 | 群聊 post 富文本格式、@ 提醒功能、群初始化采集 app_id、feishu_scan_group.py 工具 |
| v3.4.0 | 删除不可用--send、修复get_agent_info多场景判断、修复feishu_add升级逻辑、统一代理发送者字段 |
| v3.2.0 | main路径检测、消息格式规范、openclaw.json绑定检查、移除死代码 |
| v3.0.1 | 群消息延迟发送、移除真实chat_id |
| v3.0.0 | --deliver一站式发送、多场景提示、用户语言错误、chat_type验证 |
