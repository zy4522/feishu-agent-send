# feishu_agent_send - 飞书Agent通信工具

**版本：** 1.2.0  
**定位：** 飞书环境下Agent通信的标准工具  
**核心机制：** Agent借助用户飞书通道发送消息，接收方通过格式识别实际发送者

---

## 📦 安装

### 方式1：直接克隆
```bash
git clone https://github.com/zy4522/feishu-agent-send.git
cd feishu-agent-send
```

### 方式2：作为 OpenClaw Skill 安装
```bash
# 复制到工作区 skills 目录
cp -r feishu-agent-send /path/to/your/workspace/skills/
```

---

## 🔧 配置

### 1. 初始化配置

首次使用前，需要配置你的 Agent：

```python
from feishu_agent_send import setup_agent

# 添加一个 Agent
setup_agent(
    name="我的助手",
    chat_id="oc_xxxxxxxxxxxxxxxx",  # 群聊ID
    open_id="ou_xxxxxxxxxxxxxxxx"   # 用户open_id（可选）
)
```

### 2. 获取 chat_id

**方法1：通过飞书群聊获取**
- 在飞书群聊中，使用 `feishu_chat` 工具搜索群名称
- 或者查看群设置中的群ID

**方法2：通过历史消息获取**
```python
from feishu_agent_send import get_chat_id

# 如果 Agent 曾经在群里发过消息
chat_id = get_chat_id("Agent名称")
```

---

## ⚡ 5秒上手

**最常用的3个函数：**

```python
from feishu_agent_send import get_chat_id, list_known_agents, feishu_agent_send

# 1️⃣ 查询某个 Agent 的 chat_id
chat_id = get_chat_id("CPA助攻")  # 返回: "oc_2a8a6e7a9ddcee371b21aae0fcb29c54"

# 2️⃣ 列出所有已知的 Agent（含 chat_id）
agents = list_known_agents()  # 返回所有Agent的chat_id和open_id

# 3️⃣ 发送消息（自动查找chat_id）
result = feishu_agent_send(
    to="CPA助攻",
    message="你好！",
    from_agent="软件开发组长"
)
# 然后用 result['send_params'] 调用 feishu_im_user_message
```

**详细用法继续往下看 👇**

---

## 🔴 紧急警告（群聊必看！）

### ⚠️ 在群聊中必须使用 feishu_agent_send！

**如果你正在群聊中，必须使用本工具发送消息，否则其他 Agent 收不到！**

```
❌ 错误：普通消息
   你好，大家好！

✅ 正确：使用 feishu_agent_send
   📨【代理】【我→群聊】
   你好，大家好！
   ---
   实际发送者：我
   代理发送者：彦哥
   ---
```

**为什么？**
- 不同 Agent 在不同的工作区/会话中
- 普通群消息只能被同会话的 Agent 看到
- `feishu_agent_send` 通过统一的飞书通道确保所有 Agent 都能接收

**快速判断：**
- 在群里 @ 其他 Agent → **必须用 feishu_agent_send**
- 回复群里的讨论 → **必须用 feishu_agent_send**
- 私聊单个 Agent → 推荐用 feishu_agent_send（可选）

---

## ⚠️ 重要提示（使用前必读）

### 跨应用通信限制

**问题：** 不同 Agent 可能属于不同的飞书应用，直接使用 `open_id` 会报错：
```
open_id cross app
```

**解决方案：**
| 方式 | ID 类型 | 是否可行 | 说明 |
|------|---------|----------|------|
| 私聊 | `open_id` (ou_xxx) | ❌ 不可行 | 不同应用间会报 cross app |
| 私聊 | `chat_id` (oc_xxx) | ✅ 可行 | 通过群聊的 chat_id 发送 |
| 群聊 | `chat_id` (oc_xxx) | ✅ 可行 | 推荐方式，所有 Agent 可见 |

**结论：**
- **群聊优先** - 使用群的 `chat_id` 发送消息
- **避免 open_id** - 不要直接用 `open_id` 私聊其他 Agent
- **统一通道** - 借助彦哥的飞书通道，使用 `chat_id` 发送

---

## 🎯 核心设计

### 消息代理机制

```
Agent A → feishu_agent_send → 格式化消息 → 彦哥的飞书通道 → 群聊/私聊
```

**消息格式：**
```
📨【代理】【Agent A→Agent B】

[消息内容]

---
实际发送者：Agent A
代理发送者：彦哥
---
```

**接收方识别：**
- 看到【代理】标记 → 知道这是借助彦哥通道发的
- 看到【Agent A→Agent B】→ 知道实际是谁发的
- 回复时也用 feishu_agent_send，保持格式一致

---

## 🎯 使用场景指南（重要！）

### 什么时候用 feishu_agent_send？

| 场景 | 是否使用 | 说明 |
|------|----------|------|
| **Agent → Agent 通信** | ✅ **使用** | 借助彦哥的飞书通道，让其他 Agent 知道实际是谁发的 |
| **群聊广播** | ✅ **使用** | 在群里@所有人，标明实际发送者 |
| **彦哥直接对话** | ❌ **不用** | 彦哥直接私聊你，直接回复即可，不需要【代理】标记 |
| **用户直接对话** | ❌ **不用** | 普通对话场景，用普通消息格式 |

### 判断口诀

```
发送者是 Agent（我）→ 用 feishu_agent_send
发送者是彦哥（用户）→ 直接回复，不用格式
```

### 示例

**✅ 正确：Agent 间通信**
```python
# 我是大总管，要给颖小兔发消息
from feishu_agent_send import feishu_agent_send

result = feishu_agent_send(
    to="颖小兔",
    message="请汇报进度",
    from_agent="大总管"
)
# 颖小兔收到：📨【代理】【大总管→颖小兔】...
```

**❌ 错误：直接对话也用代理格式**
```python
# 彦哥直接问我问题
# 我错误地用了代理格式回复
📨【代理】【大总管→彦哥】  # ← 这是错误的！

# 应该直接回复：
彦哥，这个问题是这样的...
```

---

## 🚀 快速开始

### 安装

```bash
# skill已安装到 ~/.openclaw/skills/feishu_agent_send/
# 自动加载，无需额外安装
```

### 基础用法

**好消息：skill 会自动帮你查找 chat_id！**

```python
from feishu_agent_send import feishu_agent_send

# 发送消息（自动查找 chat_id，避免 cross app）
result = feishu_agent_send(
    to="大总管",             # 目标Agent名称
    message="请汇报进度",    # 消息内容（纯文本）
    from_agent="软件开发组长"  # 自己的Agent名称
)

# 查看发送参数
if result["success"]:
    print(f"使用 chat_id: {result.get('chat_id', '无')}")
    print(f"使用 open_id: {result.get('receiver_id', '无')}")
    print(f"格式化消息:\n{result['formatted_message']}")
```

### 推荐用法（一键发送）⭐

```python
from feishu_agent_send import feishu_agent_send_and_deliver

# 第1步：一键准备发送（自动格式化 + 查找chat_id）
result = feishu_agent_send_and_deliver(
    to="软件开发组长",        # 目标Agent名称
    message="你好！",         # 消息内容
    from_agent="CPA助攻"      # 自己的名称
)

# 第2步：直接发送
if result["success"]:
    feishu_im_user_message(**result["send_params"])
    print("✅ 发送成功！")
```

### 群聊专用（简化版）💬

```python
from feishu_agent_send import send_to_group

# 发送到当前群聊（自动使用群chat_id）
result = send_to_group(
    message="大家好！",       # 消息内容
    from_agent="我",          # 自己的名称
    group_chat_id="oc_xxx"    # 群聊ID（可选，自动检测）
)

# 直接发送
if result["success"]:
    feishu_im_user_message(**result["send_params"])
```

### 基础用法（分步控制）

```python
from feishu_agent_send import feishu_agent_send

# 第1步：格式化消息
result = feishu_agent_send(
    to="大总管",
    message="请汇报进度",
    from_agent="软件开发组长"
)

# 第2步：手动发送
if result["success"]:
    feishu_im_user_message(
        action="send",
        msg_type="text",
        content=result["send_params"]["params"]["content"],
        receive_id_type="chat_id",
        receive_id=result["chat_id"]
    )
```

**工作原理：**
1. skill 内置了常见 Agent 的 **chat_id** 映射表（自动查找）
2. 如果找到 chat_id，优先使用 chat_id 发送（避免 cross app）
3. 如果找不到 chat_id，会回退到 **open_id**（可能报 cross app）
4. 返回发送参数，供调用方使用

**已知的 Agent chat_id：**
| Agent | chat_id | 说明 |
|-------|---------|------|
| 大总管 | oc_3f984cbfb19dbcfd658f0537689dd19c | 与彦哥的私聊 |
| 颖小兔 | oc_9c8528a08be665f04bfa857e07cd535d | 与彦哥的私聊 |
| AYY | oc_9d8e4a53e3f558d3457dad06f1e0a275 | 测试群 |
| 测试群 | oc_9d8e4a53e3f558d3457dad06f1e0a275 | 群聊 |

**如果找不到 chat_id 怎么办？**
- 方法1：手动提供 `chat_id` 参数
- 方法2：在群里发送（使用群的 chat_id）
- 方法3：使用 `get_chat_id()` 函数查询
- 方法4：联系彦哥添加新的 chat_id 映射

---

## 📚 API文档

### `feishu_agent_send(to, message, from_agent, chat_id=None)`

向飞书Agent发送消息（通过彦哥的通道）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `to` | str | ✅ | 目标Agent名称 |
| `message` | str | ✅ | 消息内容（纯文本，不要加格式） |
| `from_agent` | str | ✅ | 自己的Agent名称 |
| `chat_id` | str | ❌ | 可选，指定chat_id发送（优先使用） |

**返回值：**

```python
{
    "success": True,
    "receiver_id": "ou_xxx",           # open_id（如果使用）
    "receiver_name": "CPA助攻",
    "chat_id": "oc_xxx",               # 实际使用的chat_id
    "chat_id_source": "auto",          # "provided"(传入) 或 "auto"(自动查找)
    "formatted_message": "📨【代理】...",
    "send_params": {...}               # 发送参数，供feishu_im_user_message使用
}
```

### `get_chat_id(agent_name)`

获取 Agent 的 chat_id，不用手动去会话记录里翻。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_name` | str | ✅ | Agent名称 |

**返回值：**

```python
chat_id = get_chat_id("颖小兔")
print(chat_id)  # "oc_9c8528a08be665f04bfa857e07cd535d"
```

**示例：**

```python
from feishu_agent_send import feishu_agent_send, get_chat_id

# 先查询 chat_id
chat_id = get_chat_id("颖小兔")
if chat_id:
    # 使用查询到的 chat_id 发送
    result = feishu_agent_send(
        to="颖小兔",
        message="测试消息",
        from_agent="大总管",
        chat_id=chat_id  # 明确指定
    )
else:
    print("找不到颖小兔的 chat_id")
```

### `list_known_agents()`

列出所有已知的 Agent 信息（open_id 和 chat_id）。

**返回值：**

```python
agents = list_known_agents()
# {
#     "颖小兔": {
#         "open_id": "ou_b011e627ccc9e10abc18a3c992a23a3d",
#         "chat_id": "oc_9c8528a08be665f04bfa857e07cd535d"
#     },
#     ...
# }
```

---

## 🔧 工作原理

### 发送流程

```
1. Agent调用 feishu_agent_send(to, message, from_agent)
    ↓
2. 格式化消息：加上【代理】【from→to】标记
    ↓
3. 查找目标Agent的open_id
    ↓
4. 调用彦哥的 feishu_im_user_message 发送
    ↓
5. 消息以"彦哥"名义发出，但格式标明实际发送者
```

### 接收识别

当收到消息时：

```python
if "📨【代理】" in message:
    # 解析实际发送者
    actual_sender = parse_sender(message)  # 例如："软件开发组长"
    
    # 知道这是借助彦哥通道发的
    # 回复时也用 feishu_agent_send
```

---

## 💡 使用示例

### 示例1：简单发送

```python
from feishu_agent_send import feishu_agent_send

result = feishu_agent_send(
    to="CPA助攻",
    message="会计科目进度如何？",
    from_agent="软件开发组长"
)

if result["success"]:
    print(f"发送成功，消息ID: {result['message_id']}")
```

### 示例2：接收并回复

```python
# 收到消息时识别
received_message = "📨【代理】【CPA助攻→软件开发组长】\n\n已完成50%\n\n---\n实际发送者：CPA助攻\n代理发送者：彦哥\n---"

if "📨【代理】" in received_message:
    # 解析出实际发送者是CPA助攻
    actual_sender = "CPA助攻"
    
    # 回复
    feishu_agent_send(
        to=actual_sender,  # 回复给CPA助攻
        message="收到，继续推进",
        from_agent="软件开发组长"
    )
```

### 示例3：群发通知

```python
agents = ["CPA助攻", "AYY", "颖小兔"]

for agent in agents:
    feishu_agent_send(
        to=agent,
        message="会议通知：下午3点讨论进度",
        from_agent="软件开发组长"
    )
```

---

## 📋 规则说明

### 对于发送方

1. **必须使用 feishu_agent_send** - 不要直接用 feishu_im_user_message
2. **提供正确的 from_agent** - 让接收方知道你是谁
3. **消息内容用纯文本** - 不要手动加格式，工具会自动加

### 对于接收方

1. **识别【代理】标记** - 看到此标记就知道是借助彦哥通道
2. **解析实际发送者** - 从【Agent A→Agent B】中提取
3. **判断是否是自己发的** - 如果 `from_agent` 等于自己的名称，说明是自己发的，不需要回复
4. **回复也用 feishu_agent_send** - 保持格式一致

**示例代码：**
```python
from feishu_agent_send import parse_proxy_message

# 收到消息时解析
parsed = parse_proxy_message(received_message, my_agent_name="软件开发组长")

if parsed:
    if parsed.get("is_from_myself"):
        # 是自己发的消息，不需要回复
        print("这是我自己发的消息，跳过")
    else:
        # 是其他 Agent 发的消息，正常处理
        print(f"收到 {parsed['from_agent']} 的消息: {parsed['content']}")
        # 回复...
```

---

## 🆚 与传统方式对比

| 特性 | 传统方式 | feishu_agent_send |
|------|---------|-------------------|
| 发送通道 | Agent自己的通道 | 彦哥的通道（统一） |
| 消息格式 | 普通文本 | 📨【代理】【A→B】格式 |
| 身份识别 | 不清楚 | 格式标明实际发送者 |
| 跨应用 | 受限 | 通过彦哥通道解决 |
| 管理 | 分散 | 统一代理，便于管理 |

---

## 📁 文件结构

```
~/.openclaw/skills/feishu_agent_send/
├── SKILL.md              # 本文档
├── feishu_agent_send.py  # 核心模块
├── agent_resolver.py     # Agent名称解析器
├── message_formatter.py  # 消息格式化
└── examples/             # 示例代码
    ├── basic_usage.py
    └── reply_example.py
```

---

## 🔄 迁移指南

### 从旧FAP迁移

**旧代码：**
```python
from fap import FAP

fap = FAP(agent_name="软件开发组长", chat_id="oc_xxx")
msg = fap.create_message("CPA助攻", "请汇报进度")
# 然后手动调用feishu_im_user_message
```

**新代码：**
```python
from feishu_agent_send import feishu_agent_send

feishu_agent_send(
    to="CPA助攻",
    message="请汇报进度",
    from_agent="软件开发组长"
)
```

---

## 👥 作者

- **Zhang Yan (张彦)** - Product Lead
- **Dev-Leader Team** - Core Development

**版本历史：**
- v1.0.0 (2026-03-27) - 初始版本，基于FAP改进，增加消息代理机制

---

## 📄 许可证

Apache License 2.0
