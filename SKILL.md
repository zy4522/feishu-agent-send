# feishu_agent_send - 飞书Agent通信工具

**版本：** 1.3.1  
**代码版本：** 1.3.1  
**定位：** 飞书环境下Agent通信的标准工具  
**核心机制：** Agent借助用户飞书通道发送消息，接收方通过格式识别实际发送者

---

## 🎯 一句话理解

> **Agent 之间不能直接对话，必须通过用户的飞书通道转发。**
> 
> **🔴 所有 Agent 通信都用 `feishu_agent_send`，不要用 `message` 或 `feishu_im_user_message`！**
> 
> **🔴 无论发送还是回复，无论私信还是群聊，都用 `feishu_agent_send`！**

---

## ❌ 常见错误（新手必犯）

| 错误做法 | 后果 | 正确做法 |
|---------|------|---------|
| 用 `message` 工具在群里发消息 | 其他 Agent 看不见 | 用 `feishu_agent_send(..., chat_type="group")` |
| 用 `feishu_im_user_message` 直接回复 | 其他 Agent 看不见 | 用 `feishu_agent_send` 回复 |
| 以为只有发消息时用，收消息不用 | 回复了对方看不见 | 收发都用 `feishu_agent_send` |
| 混淆 `chat_type="p2p"` 和 `"group"` | 消息发到错误场景 | 看收到的消息前缀判断 |

---

## ⚡ 5秒判断法

### 收到消息时：
1. 看到 `📨【代理】` 开头？→ **用 `feishu_agent_send` 回复**
2. 不管前面是【私信】还是【群】→ **都用 `feishu_agent_send`**
3. 复制对方的 `chat_type` → 保持场景一致

### 发送消息时：
1. 要给其他 Agent 发消息？→ **用 `feishu_agent_send`**
2. 在群里讨论？→ `chat_type="group"`
3. 私信单个 Agent？→ `chat_type="p2p"`

---

## 🔴 消息类型判断

收到 `📨【代理】` 消息时，判断消息来源：

| 消息前缀 | 来源场景 | 回复方式 |
|---------|---------|---------|
| `📨【私信】【代理】...` | **私信**收到的 | 用 `feishu_agent_send(..., chat_type="p2p")` |
| `📨【群】【代理】...` | **群聊**收到的 | 用 `feishu_agent_send(..., chat_type="group")` |

**关键理解：**
- **无论私信还是群聊，都用 `feishu_agent_send`**
- `chat_type` 只是标记消息来源场景
- **永远不要直接用 `message` 工具在群里发消息**（其他 Agent 看不见）

**示例：**
```
📨【私信】【代理】【CPA助攻→开发组长】  ← 私信场景，用 chat_type="p2p"
📨【群】【代理】【CPA助攻→开发组长】    ← 群聊场景，用 chat_type="group"
```

---

## 🚀 快速决策流程图

```
收到消息？
    ↓
看到 📨【私信】开头？
    ↓ 是
    用 feishu_agent_send(..., chat_type="p2p") 回复
    ↓
看到 📨【群】开头？
    ↓ 是
    用 feishu_agent_send(..., chat_type="group") 回复
    ↓
没看到 📨 开头？
    ↓
    这是普通消息，用普通方式回复

要给其他 Agent 发消息？
    ↓
    用 feishu_agent_send(...)
    ↓
    在群里？→ chat_type="group"
    私信？→ chat_type="p2p"
```

---

## ⚡ 5秒上手

### 场景1：发送私信（标记为【私信】）
```python
from feishu_agent_send import feishu_agent_send

result = feishu_agent_send(
    to="CPA助攻",
    message="你好！",
    from_agent="软件开发组长",
    chat_type="p2p"  # 私信标记
)
# 然后用 result['send_params'] 调用 feishu_im_user_message
```

### 场景2：发送到群聊（标记为【群】）
```python
from feishu_agent_send import feishu_agent_send

result = feishu_agent_send(
    to="CPA助攻",
    message="大家好！",
    from_agent="软件开发组长",
    chat_id="oc_xxx",  # 群聊ID
    chat_type="group"  # 群聊标记
)
```

### 场景3：收到消息后如何回复
```python
from feishu_agent_send import parse_proxy_message, feishu_agent_send

# 解析收到的消息
parsed = parse_proxy_message(received_message)

if parsed:
    print(f"来自：{parsed['from_agent']}")
    print(f"场景：{parsed['chat_type']}")  # "p2p" 或 "group"
    
    # ⚠️ 重要：无论哪种场景，都用 feishu_agent_send 回复！
    feishu_agent_send(
        to=parsed['from_agent'],
        message="收到！",
        from_agent="我",
        chat_type=parsed['chat_type']  # 保持相同场景
    )
```

**关键提醒：**
- ✅ 私信场景 → `chat_type="p2p"`
- ✅ 群聊场景 → `chat_type="group"`
- ❌ 不要用 `message` 工具直接回复（其他 Agent 看不见）

---

## 🔴 紧急警告（群聊必看！）

### ⚠️ 在群聊中必须使用 feishu_agent_send！

**如果你正在群聊中，必须使用本工具发送消息，否则其他 Agent 收不到！**

```
❌ 错误：普通消息
   你好，大家好！

✅ 正确：使用 feishu_agent_send（标记为【群】）
   📨【群】【代理】【我→群聊】
   你好，大家好！
   ---
   实际发送者：我
   代理发送者：彦哥
   ---
```

**为什么？**
- 不同 Agent 在不同的工作区/会话中
- 普通群消息只能被同会话的 Agent 看到（其他 Agent 看不见）
- `feishu_agent_send` 通过**用户的飞书通道**发送，确保所有 Agent 都能接收

**快速判断：**
- 在群里 @ 其他 Agent → **必须用 `feishu_agent_send`**
- 回复群里的讨论 → **必须用 `feishu_agent_send`**
- 私聊单个 Agent → **必须用 `feishu_agent_send`**
- **永远不要直接用 `message` 工具发消息**（其他 Agent 看不见）

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
- **所有通信都用 `feishu_agent_send`** - 通过用户的通道发送
- **避免 open_id** - 不要直接用 `open_id` 私聊其他 Agent（会报 cross app）
- **统一通道** - 借助用户的飞书通道，所有消息都能被其他 Agent 看见

---

## 🎯 核心设计

### 消息代理机制

```
Agent A → feishu_agent_send → 格式化消息 → 彦哥的飞书通道 → 群聊/私聊
```

**消息格式（v1.3.0 新增会话类型标记）：**

```
📨【私信】【代理】【Agent A→Agent B】  ← 私信场景
📨【群】【代理】【Agent A→Agent B】     ← 群聊场景

[消息内容]

---
实际发送者：Agent A
代理发送者：彦哥
---
```

**接收方识别：**
- 看到【私信】→ 知道这是私信发的 → 用 `feishu_im_user_message` 回复
- 看到【群】→ 知道这是群里发的 → 用 `message` 工具回复到群里
- 看到【Agent A→Agent B】→ 知道实际是谁发的

---

## 🎯 使用场景指南（重要！）

### 什么时候用 feishu_agent_send？

| 场景 | 是否使用 | 说明 |
|------|----------|------|
| **Agent → Agent 私信** | ✅ **使用** | `chat_type="p2p"`，消息标记为【私信】 |
| **Agent → Agent 群聊** | ✅ **使用** | `chat_type="group"`，消息标记为【群】 |
| **彦哥直接对话** | ❌ **不用** | 彦哥直接私聊你，直接回复即可 |
| **用户直接对话** | ❌ **不用** | 普通对话场景，用普通消息格式 |

### 判断口诀

```
发送者是 Agent（我）→ 用 feishu_agent_send
发送者是彦哥（用户）→ 直接回复，不用格式

chat_type="p2p" → 私信场景 → 接收方用 feishu_im_user_message 回复
chat_type="group" → 群聊场景 → 接收方用 message 工具回复到群里
```

### 示例

**✅ 正确：私信发送（chat_type="p2p"）**
```python
# 我是大总管，要给颖小兔发私信
from feishu_agent_send import feishu_agent_send

result = feishu_agent_send(
    to="颖小兔",
    message="请汇报进度",
    from_agent="大总管",
    chat_type="p2p"  # 标记为【私信】
)
# 颖小兔收到：📨【私信】【代理】【大总管→颖小兔】...
# 颖小兔知道要用 feishu_im_user_message 回复
```

**✅ 正确：群聊发送（chat_type="group"）**
```python
# 我在群里@颖小兔
from feishu_agent_send import feishu_agent_send

result = feishu_agent_send(
    to="颖小兔",
    message="请汇报进度",
    from_agent="大总管",
    chat_id="oc_xxx",  # 群聊ID
    chat_type="group"  # 标记为【群】
)
# 颖小兔收到：📨【群】【代理】【大总管→颖小兔】...
# 颖小兔知道要用 message 工具回复到群里
```
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

### Debug 模式（v1.3.1 新增）

**只预览，不实际发送：**

```python
from feishu_agent_send import feishu_agent_send

# 使用 dry_run 参数预览
result = feishu_agent_send(
    to="CPA助攻",
    message="你好！",
    from_agent="软件开发组长",
    chat_type="group",
    dry_run=True  # 只预览，不发送
)

# 查看预览信息
if result["success"]:
    print(f"✅ 验证通过")
    print(f"   接收方: {result['receiver_name']}")
    print(f"   chat_id: {result['chat_id']}")
    print(f"   chat_type: {result['chat_type']}")
    print(f"   消息预览: {result['formatted_message'][:100]}...")
else:
    print(f"❌ 验证失败: {result['error']}")
```

**用途：**
- 发送前确认接收方正确
- 验证 chat_id 是否有效
- 检查消息格式是否正确
- 调试时避免误发

---

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

### `feishu_agent_send(to, message, from_agent, chat_id=None, chat_type="p2p")`

向飞书Agent发送消息（通过彦哥的通道）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `to` | str | ✅ | 目标Agent名称 |
| `message` | str | ✅ | 消息内容（纯文本，不要加格式） |
| `from_agent` | str | ✅ | 自己的Agent名称 |
| `chat_id` | str | ❌ | 可选，指定chat_id发送（优先使用） |
| `chat_type` | str | ❌ | 会话类型：`"p2p"`（私信，默认）或 `"group"`（群聊） |

**重要：** `chat_type` 决定消息标记和接收方的回复方式：
- `"p2p"` → 消息标记为 `📨【私信】【代理】...`，接收方应使用 `feishu_im_user_message` 回复
- `"group"` → 消息标记为 `📨【群】【代理】...`，接收方应使用 `message` 工具回复到群里

**返回值：**

```python
{
    "success": True,
    "receiver_id": "ou_xxx",           # open_id（如果使用）
    "receiver_name": "CPA助攻",
    "chat_id": "oc_xxx",               # 实际使用的chat_id
    "chat_id_source": "auto",          # "provided"(传入) 或 "auto"(自动查找)
    "formatted_message": "📨【私信】【代理】...",  # 或 📨【群】【代理】...
    "send_params": {...}               # 发送参数，供feishu_im_user_message使用
}
```

### `parse_proxy_message(message, my_agent_name=None)`

解析收到的代理消息，提取发送者、接收者、内容，以及**场景类型**。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | str | ✅ | 收到的消息内容 |
| `my_agent_name` | str | ❌ | 自己的Agent名称，用于判断是否是自己发的 |

**返回值：**

```python
{
    "from_agent": "CPA助攻",           # 发送者
    "to_agent": "开发组长",            # 接收者
    "content": "消息内容",              # 消息正文
    "chat_type": "p2p",                # 场景类型："p2p" 或 "group"
    "is_proxy": True,                  # 是否是代理消息
    "is_from_myself": False,           # 是否是自己发的（需要提供 my_agent_name）
    "marked_sender": "CPA助攻",        # 自我标记的发送者
    "reply_chat_id": "oc_xxx"          # 建议回复到这个 chat_id（v1.3.1 新增）
}
```

**使用示例：**

```python
from feishu_agent_send import parse_proxy_message, feishu_agent_send

# 收到消息
received = "📨【群】【代理】【CPA助攻→开发组长】..."

# 解析
parsed = parse_proxy_message(received, my_agent_name="开发组长")

if parsed:
    print(f"来自：{parsed['from_agent']}")
    print(f"场景：{parsed['chat_type']}")  # "p2p" 或 "group"
    
    # ⚠️ 重要：无论哪种场景，都用 feishu_agent_send 回复！
    if not parsed.get('is_from_myself'):
        feishu_agent_send(
            to=parsed['from_agent'],
            message="收到！",
            from_agent="开发组长",
            chat_id=parsed.get('reply_chat_id'),  # 使用建议的 chat_id
            chat_type=parsed['chat_type']  # 保持相同场景
        )
```
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

### `auto_reply(received_message, reply_content, my_agent_name)` ⭐ 新增

自动回复收到的代理消息（简化版）。

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `received_message` | str | ✅ | 收到的消息内容 |
| `reply_content` | str | ✅ | 回复内容 |
| `my_agent_name` | str | ✅ | 自己的Agent名称 |

**返回值：**

```python
{
    "success": True,           # 是否成功
    "result": {...}            # feishu_agent_send 的返回结果
}
# 或
{
    "success": False,
    "error": "不是代理消息"     # 或 "是自己发的"
}
```

**使用示例：**

```python
from feishu_agent_send import auto_reply

# 收到消息后自动回复
result = auto_reply(
    received_message="📨【群】【代理】【CPA助攻→开发组长】...",
    reply_content="收到，马上处理！",
    my_agent_name="开发组长"
)

if result["success"]:
    print("✅ 回复成功")
else:
    print(f"❌ 回复失败：{result['error']}")
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

## ❓ 常见问题

### Q1: 发了消息对方说没收到？

**可能原因：**
1. ❌ 你用了 `message` 工具直接发 → 其他 Agent 看不见
2. ❌ 你用了 `feishu_im_user_message` 直接回复 → 其他 Agent 看不见
3. ❌ `chat_type` 选错了 → 消息发到错误场景

**解决方法：**
- ✅ 检查是否用了 `feishu_agent_send`
- ✅ 检查 `chat_type` 是否与对方发送的场景一致
- ✅ 检查消息是否以 `📨【代理】` 开头

### Q2: 怎么知道当前是群聊还是私聊？

**看收到的消息前缀：**
- `📨【私信】【代理】...` → 私聊场景 → `chat_type="p2p"`
- `📨【群】【代理】...` → 群聊场景 → `chat_type="group"`

**或者解析消息：**
```python
parsed = parse_proxy_message(received_message)
chat_type = parsed['chat_type']  # "p2p" 或 "group"
```

### Q3: 可以不给 chat_id 吗？

**可以！** `chat_id` 是可选参数：
- 如果不给，`feishu_agent_send` 会自动查找目标 Agent 的 chat_id
- 如果找不到，会报错提示你手动提供
- 建议：让 skill 自动查找，除非你知道确切的 chat_id

### Q4: 怎么快速回复收到的消息？

**用 `auto_reply` 函数（v1.3.1 新增）：**
```python
from feishu_agent_send import auto_reply

result = auto_reply(
    received_message=收到的消息,
    reply_content="收到！",
    my_agent_name="你的名字"
)
```

### Q5: 为什么必须用 `feishu_agent_send`？

**飞书的限制：**
- 不同 Agent 属于不同的飞书应用/会话
- 机器人之间直接发消息，其他机器人看不见
- 必须通过用户的飞书通道转发，所有 Agent 才能看见

---

## ✅ 发送前检查清单

**每次发送前，确认以下3项：**

- [ ] **接收方名称正确？** 
  - 检查 `to` 参数是否写对了 Agent 名称
  - 示例：`to="CPA助攻"` 不是 `to="cpa助攻"`

- [ ] **chat_id 对应正确的接收方？**
  - 如果手动指定了 `chat_id`，确认它属于目标 Agent
  - 建议：不指定 `chat_id`，让 skill 自动查找

- [ ] **chat_type 与场景匹配？**
  - 私信场景 → `chat_type="p2p"`
  - 群聊场景 → `chat_type="group"`
  - 不确定？看收到的消息前缀判断

**快速验证代码：**
```python
# 发送前预览（不实际发送）
result = feishu_agent_send(
    to="CPA助攻",
    message="你好",
    from_agent="我",
    chat_type="group",
    dry_run=True  # 只预览，不发送
)
print(f"将发送给: {result['receiver_name']}")
print(f"使用 chat_id: {result['chat_id']}")
print(f"消息格式: {result['formatted_message'][:50]}...")
```

---

## ❌ 常见发送错误

### 错误1：发给了错误的 Agent
```python
# ❌ 错误：想发给 CPA助攻，却发给了大总管
feishu_agent_send(
    to="大总管",  # 错了！
    message="...",
    from_agent="我"
)

# ✅ 正确：检查接收方名称
feishu_agent_send(
    to="CPA助攻",  # 确认名称正确
    message="...",
    from_agent="我"
)
```

### 错误2：chat_type 与场景不匹配
```python
# ❌ 错误：群里收到的消息，用 p2p 回复
# 收到：📨【群】【代理】【CPA助攻→我】
feishu_agent_send(
    to="CPA助攻",
    message="...",
    chat_type="p2p"  # 错了！应该用 "group"
)

# ✅ 正确：保持场景一致
feishu_agent_send(
    to="CPA助攻",
    message="...",
    chat_type="group"  # 与收到的消息场景一致
)
```

### 错误3：直接用 message 工具发送
```python
# ❌ 错误：其他 Agent 看不见
message(action="send", to="群ID", message="大家好")

# ✅ 正确：用 feishu_agent_send
feishu_agent_send(
    to="CPA助攻",
    message="大家好",
    from_agent="我",
    chat_type="group"
)
```

### 错误4：忘记用 FAS，用 sessions_send 失败后不知所措
```python
# ❌ 错误：sessions_send 失败后，没想到用 FAS
sessions_send(sessionKey="...", message="...")  # 超时失败
# 然后不知道怎么办

# ✅ 正确：第一时间用 FAS
feishu_agent_send(
    to="目标Agent",
    message="...",
    from_agent="我",
    chat_type="p2p"  # 或 "group"
)
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
- v1.3.1 (2026-03-29) - 修正文档错误；新增发送前检查清单、常见发送错误章节、debug模式说明；强化"所有Agent通信都用FAS"提醒
- v1.3.0 (2026-03-29) - 新增会话类型标记（【私信】/【群】），解决接收方无法判断回复方式的问题
- v1.2.0 (2026-03-28) - 增加消息解析和自动识别功能
- v1.0.0 (2026-03-27) - 初始版本，基于FAP改进，增加消息代理机制

---

## 📄 许可证

Apache License 2.0
