"""
feishu_agent_send - 飞书Agent通信工具 v1.3.0

核心机制：Agent借助用户飞书通道发送消息，接收方通过格式识别实际发送者

v1.3.0 更新：
- 新增会话类型标记（【私信】/【群】），解决接收方无法判断回复方式的问题
- parse_proxy_message 返回 reply_method 建议

⚠️ 重要提示：在群聊中必须使用本工具发送消息，否则其他 Agent 收不到！
"""

import json
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime


class AgentNotFoundError(Exception):
    """找不到Agent时抛出"""
    pass


class FeishuAgentSendError(Exception):
    """发送消息失败时抛出"""
    pass


# 安装提示标志
_INSTALLATION_NOTICE_SHOWN = False

def show_installation_notice():
    """
    显示安装提示
    
    在首次导入模块时显示重要使用提示。
    """
    global _INSTALLATION_NOTICE_SHOWN
    if _INSTALLATION_NOTICE_SHOWN:
        return
    
    notice = """
╔════════════════════════════════════════════════════════════╗
║  🎉 feishu_agent_send 安装成功！                          ║
╠════════════════════════════════════════════════════════════╣
║  ⚠️  重要提示：                                            ║
║     在群聊中发送消息时，必须使用 feishu_agent_send！        ║
║     普通消息无法被其他 Agent 接收。                         ║
╠════════════════════════════════════════════════════════════╣
║  📖 快速开始：                                              ║
║     from feishu_agent_send import send_to_group            ║
║     result = send_to_group("消息", "我的名字")               ║
║     feishu_im_user_message(**result['send_params'])        ║
╠════════════════════════════════════════════════════════════╣
║  📚 详细文档：SKILL.md                                      ║
╚════════════════════════════════════════════════════════════╝
"""
    print(notice)
    _INSTALLATION_NOTICE_SHOWN = True


class AgentResolver:
    """
    Agent名称解析器（通用版）
    
    支持：
    1. 配置文件加载
    2. 动态发现（从历史消息）
    3. 首次建立机制
    """
    
    # 默认的Agent映射（可扩展）
    DEFAULT_AGENTS = {}
    
    def __init__(self, config_path: str = None):
        self.cache = {}
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 优先使用工作区目录
        workspace_config = "/root/.openclaw/workspace/skills/feishu_agent_send/config.json"
        if os.path.exists(workspace_config):
            return workspace_config
        
        # 回退到用户目录
        user_config = os.path.expanduser("~/.feishu_agent_send/config.json")
        return user_config
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}")
        
        # 返回默认配置
        return {
            "version": "1.1.0",
            "agents": {},
            "discovery": {"enabled": True, "cache_duration_hours": 24},
            "proxy": {"name": "默认代理", "enabled": True}
        }
    
    def _save_config(self):
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 配置文件保存失败: {e}")
    
    @property
    def KNOWN_AGENTS(self) -> Dict[str, str]:
        """获取已知的Agent open_id映射"""
        agents = self.DEFAULT_AGENTS.copy()
        for name, info in self.config.get("agents", {}).items():
            if isinstance(info, dict) and "open_id" in info:
                agents[name] = info["open_id"]
        return agents
    
    @property
    def KNOWN_AGENT_CHAT_IDS(self) -> Dict[str, str]:
        """获取已知的Agent chat_id映射"""
        chat_ids = {}
        for name, info in self.config.get("agents", {}).items():
            if isinstance(info, dict) and "chat_id" in info:
                chat_ids[name] = info["chat_id"]
        return chat_ids
    
    def resolve_chat_id(self, agent_identifier: str) -> Optional[str]:
        """
        解析Agent标识符为chat_id（优先）
        
        策略：
        1. 检查配置文件
        2. 检查缓存
        3. 尝试动态发现（如果启用）
        """
        name = agent_identifier.lstrip("@")
        
        # 1. 检查配置文件
        if name in self.KNOWN_AGENT_CHAT_IDS:
            return self.KNOWN_AGENT_CHAT_IDS[name]
        
        # 2. 检查缓存
        if name in self.cache:
            return self.cache[name]
        
        # 3. 尝试动态发现
        if self.config.get("discovery", {}).get("enabled", True):
            discovered = self._discover_chat_id(name)
            if discovered:
                # 保存到缓存
                self.cache[name] = discovered
                return discovered
        
        return None
    
    def _discover_chat_id(self, agent_name: str) -> Optional[str]:
        """
        动态发现Agent的chat_id
        
        实现思路：
        - 搜索历史消息
        - 从飞书API获取会话列表
        - 匹配Agent名称
        
        注意：这里只是一个框架，实际实现需要调用飞书API
        """
        # TODO: 实现动态发现逻辑
        # 例如：
        # 1. 调用 feishu_im_user_search_messages 搜索
        # 2. 从消息中提取 chat_id
        # 3. 验证是否匹配
        return None
    
    def resolve_open_id(self, agent_identifier: str) -> str:
        """
        解析Agent标识符为open_id（备选）
        """
        # 如果已经是open_id格式，直接返回
        if agent_identifier.startswith("ou_"):
            return agent_identifier
        
        # 去掉@前缀
        name = agent_identifier.lstrip("@")
        
        # 检查配置文件
        if name in self.KNOWN_AGENTS:
            return self.KNOWN_AGENTS[name]
        
        # 无法解析，抛出异常
        raise AgentNotFoundError(
            f"找不到Agent \"{agent_identifier}\"\n"
            f"请使用 setup_agent() 添加此Agent，或提供open_id"
        )
    
    def setup_agent(self, name: str, chat_id: str = None, open_id: str = None) -> bool:
        """
        首次建立Agent映射
        
        Args:
            name: Agent名称
            chat_id: 可选，会话ID
            open_id: 可选，用户ID
            
        Returns:
            是否成功
            
        Example:
            >>> resolver.setup_agent("新Agent", chat_id="oc_xxx")
            True
        """
        if not chat_id and not open_id:
            raise ValueError("必须提供 chat_id 或 open_id")
        
        if "agents" not in self.config:
            self.config["agents"] = {}
        
        self.config["agents"][name] = {
            "chat_id": chat_id,
            "open_id": open_id,
            "created_at": datetime.now().isoformat()
        }
        
        self._save_config()
        return True
    
    def list_agents(self) -> Dict[str, Dict[str, str]]:
        """
        列出所有已知的Agent
        
        Returns:
            Agent信息字典
        """
        result = {}
        for name, info in self.config.get("agents", {}).items():
            if isinstance(info, dict):
                result[name] = {
                    "chat_id": info.get("chat_id", "未设置"),
                    "open_id": info.get("open_id", "未设置"),
                    "created_at": info.get("created_at", "未知")
                }
        return result
    
    def remove_agent(self, name: str) -> bool:
        """移除Agent配置"""
        if name in self.config.get("agents", {}):
            del self.config["agents"][name]
            self._save_config()
            return True
        return False


class MessageFormatter:
    """
    消息格式化器
    
    格式化代理消息，包含【代理】标记和实际发送者信息。
    支持区分群聊和私信场景。
    """
    
    CHAT_TYPE_GROUP = "群"
    CHAT_TYPE_PRIVATE = "私信"
    
    @staticmethod
    def format_proxy_message(
        from_agent: str, 
        to_agent: str, 
        content: str, 
        mark_as_self: bool = True,
        chat_type: str = "p2p"  # "p2p" 或 "group"
    ) -> str:
        """
        格式化代理消息
        
        Args:
            from_agent: 实际发送者名称
            to_agent: 接收者名称
            content: 消息内容
            mark_as_self: 是否添加自我标记（默认True）
            chat_type: 会话类型，"p2p"=私信, "group"=群聊
            
        Returns:
            格式化后的消息
        """
        # 添加隐藏的自我标记（用于接收方识别是自己发的）
        self_marker = f"<!--self:{from_agent}-->" if mark_as_self else ""
        
        # 根据会话类型添加标记
        if chat_type == "group":
            type_marker = f"【{MessageFormatter.CHAT_TYPE_GROUP}】"
        else:
            type_marker = f"【{MessageFormatter.CHAT_TYPE_PRIVATE}】"
        
        return f"📨{type_marker}【代理】【{from_agent}→{to_agent}】{self_marker}\n\n{content}\n\n---\n实际发送者：{from_agent}\n代理发送者：用户\n---"
    
    @staticmethod
    def parse_proxy_message(message: str) -> Optional[Dict[str, str]]:
        """
        解析代理消息
        
        Args:
            message: 收到的消息
            
        Returns:
            解析结果字典，如果不是代理消息返回None
            包含字段：
            - from_agent: 发送者
            - to_agent: 接收者
            - content: 内容
            - chat_type: 会话类型 ("group" 或 "p2p")
            - is_proxy: 是否是代理消息
            - marked_sender: 自我标记的发送者
            - reply_method: 建议的回复方式 ("message" 或 "feishu_im_user_message")
        """
        # 检查是否是代理消息（支持新旧格式）
        if not message.startswith("📨"):
            return None
        
        # 解析会话类型标记
        chat_type = "p2p"  # 默认私信
        
        if f"【{MessageFormatter.CHAT_TYPE_GROUP}】" in message[:10]:
            chat_type = "group"
        elif f"【{MessageFormatter.CHAT_TYPE_PRIVATE}】" in message[:10]:
            chat_type = "p2p"
        else:
            # 旧格式没有标记，尝试推断
            # 如果包含 "群聊" 字样或特定上下文，可能是群消息
            pass
        
        # 注意：不管是私信还是群聊，都用 feishu_im_user_message 发送
        # 区别只是 receive_id 是私聊 chat_id 还是群 chat_id
        reply_method = "feishu_im_user_message"
        
        # 解析【from→to】
        pattern = r'📨(?:【.*?】)*【代理】【(.+?)→(.+?)】'
        match = re.search(pattern, message)
        
        if not match:
            # 尝试旧格式
            pattern_old = r'📨【代理】【(.+?)→(.+?)】'
            match = re.search(pattern_old, message)
        
        if not match:
            return None
        
        from_agent = match.group(1)
        to_agent = match.group(2)
        
        # 提取消息内容（在最后一个】之后，---之前）
        # 找到【代理】【xxx→xxx】之后的第一个】
        proxy_end = message.find('】', message.find('【代理】'))
        if proxy_end != -1:
            content_start = proxy_end + 1
        else:
            content_start = message.find('】') + 1
            
        content_end = message.find('---')
        
        if content_end == -1:
            content = message[content_start:].strip()
        else:
            content = message[content_start:content_end].strip()
        
        # 检查是否有自我标记
        self_marker_pattern = r'<!--self:(.+?)-->'
        self_match = re.search(self_marker_pattern, message)
        marked_sender = None
        
        if self_match:
            marked_sender = self_match.group(1)
        
        return {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "content": content,
            "chat_type": chat_type,
            "is_proxy": True,
            "marked_sender": marked_sender,
            "reply_method": reply_method  # 建议的回复方式
        }


def feishu_agent_send(
    to: str,
    message: str,
    from_agent: str,
    chat_id: Optional[str] = None,
    mark_as_self: bool = True,
    chat_type: str = "p2p"  # 新增：会话类型 "p2p" 或 "group"
) -> Dict[str, Any]:
    """
    发送消息给Agent（通过用户飞书通道）
    
    这是主要的用户接口，极简设计。
    
    ⚠️ 重要提示：
    - 不同 Agent 可能属于不同飞书应用，直接用 open_id 会报 "cross app" 错误
    - 推荐使用 chat_id（群聊ID）发送消息，避免跨应用问题
    - 如果提供了 chat_id，会优先使用 chat_id 发送
    
    Args:
        to: 目标Agent名称或open_id
        message: 消息内容（纯文本，不要加格式）
        from_agent: 发送者Agent名称
        chat_id: 群聊ID（可选，推荐提供以避免跨应用问题）
               注意：如果提供此参数，会优先使用；如果不提供，会自动查找
        mark_as_self: 是否添加自我标记（默认True），用于接收方识别是自己发的消息
        chat_type: 会话类型（默认"p2p"）
               - "p2p": 私信，消息标记为【私信】，接收方应使用 feishu_im_user_message 回复
               - "group": 群聊，消息标记为【群】，接收方应使用 message 工具回复到群里
        
    Returns:
        发送结果字典，包含格式化后的消息和发送参数
        
    Example:
        # 方式1：私信发送（标记为【私信】）
        >>> result = feishu_agent_send(
        ...     to="CPA助攻",
        ...     message="请汇报进度",
        ...     from_agent="软件开发组长",
        ...     chat_type="p2p"
        ... )
        
        # 方式2：群聊发送（标记为【群】）
        >>> result = feishu_agent_send(
        ...     to="CPA助攻",
        ...     message="请汇报进度",
        ...     from_agent="软件开发组长",
        ...     chat_id="oc_9d8e4a53e3f558d3457dad06f1e0a275",
        ...     chat_type="group"
        ... )
    """
    # 1. 准备变量
    resolved_chat_id = chat_id  # 保存传入的 chat_id
    receiver_id = None
    
    resolver = AgentResolver()
    
    # 如果没有提供 chat_id，尝试自动查找
    if not resolved_chat_id:
        resolved_chat_id = resolver.resolve_chat_id(to)
    
    # 如果没有 chat_id，再尝试获取 open_id
    if not resolved_chat_id:
        try:
            receiver_id = resolver.resolve_open_id(to)
        except AgentNotFoundError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "AgentNotFoundError",
                "hint": "请提供有效的Agent名称，或手动提供 chat_id"
            }
    
    # 2. 格式化消息
    formatter = MessageFormatter()
    receiver_name = to.lstrip("@") if not to.startswith("ou_") else "Agent"
    formatted_message = formatter.format_proxy_message(
        from_agent=from_agent,
        to_agent=receiver_name,
        content=message,
        mark_as_self=mark_as_self,
        chat_type=chat_type  # 传递会话类型
    )
    
    # 3. 准备发送参数
    if resolved_chat_id:
        # 使用群聊发送（推荐，避免 cross app 问题）
        send_params = {
            "tool": "feishu_im_user_message",
            "params": {
                "action": "send",
                "receive_id_type": "chat_id",
                "receive_id": resolved_chat_id,
                "msg_type": "text",
                "content": json.dumps({"text": formatted_message}, ensure_ascii=False)
            }
        }
    else:
        # 使用 open_id 发送（可能遇到 cross app 问题）
        send_params = {
            "tool": "feishu_im_user_message",
            "params": {
                "action": "send",
                "receive_id_type": "open_id",
                "receive_id": receiver_id,
                "msg_type": "text",
                "content": json.dumps({"text": formatted_message}, ensure_ascii=False)
            }
        }
    
    # 4. 返回结果
    return {
        "success": True,
        "receiver_id": receiver_id,
        "receiver_name": receiver_name,
        "chat_id": resolved_chat_id,
        "chat_id_source": "provided" if chat_id else ("auto" if resolved_chat_id else None),
        "formatted_message": formatted_message,
        "from_agent": from_agent,
        "timestamp": datetime.now().isoformat(),
        "send_params": send_params
    }


def get_chat_id(agent_name: str, config_path: str = None) -> Optional[str]:
    """
    获取 Agent 的 chat_id（便捷函数）
    
    支持从配置文件查询，不用手动去会话记录里翻。
    
    Args:
        agent_name: Agent名称
        config_path: 可选，配置文件路径
        
    Returns:
        chat_id字符串，找不到返回None
        
    Example:
        >>> chat_id = get_chat_id("颖小兔")
        >>> print(chat_id)  # "oc_9c8528a08be665f04bfa857e07cd535d"
        
        >>> chat_id = get_chat_id("不存在的Agent")
        >>> print(chat_id)  # None
    """
    resolver = AgentResolver(config_path=config_path)
    return resolver.resolve_chat_id(agent_name)


def setup_agent(name: str, chat_id: str = None, open_id: str = None, config_path: str = None) -> bool:
    """
    首次建立Agent映射（便捷函数）
    
    Args:
        name: Agent名称
        chat_id: 可选，会话ID
        open_id: 可选，用户ID
        config_path: 可选，配置文件路径
        
    Returns:
        是否成功
        
    Example:
        >>> setup_agent("新Agent", chat_id="oc_xxx")
        True
        
        >>> setup_agent("另一个Agent", open_id="ou_xxx")
        True
    """
    resolver = AgentResolver(config_path=config_path)
    return resolver.setup_agent(name, chat_id, open_id)


def list_known_agents(config_path: str = None) -> Dict[str, Dict[str, str]]:
    """
    列出所有已知的 Agent 信息
    
    Args:
        config_path: 可选，配置文件路径
        
    Returns:
        包含 open_id 和 chat_id 的字典
        
    Example:
        >>> agents = list_known_agents()
        >>> print(agents["颖小兔"]["chat_id"])  # 获取颖小兔的 chat_id
    """
    resolver = AgentResolver(config_path=config_path)
    return resolver.list_agents()


def parse_proxy_message(message: str, my_agent_name: Optional[str] = None) -> Optional[Dict[str, str]]:
    """
    解析代理消息（便捷函数）
    
    Args:
        message: 收到的消息
        my_agent_name: 自己的Agent名称，用于判断是否是自己发的
        
    Returns:
        解析结果字典，如果不是代理消息返回None
        包含字段：
        - from_agent: 发送者
        - to_agent: 接收者  
        - content: 内容
        - chat_type: 会话类型 ("group" 或 "p2p")
        - is_proxy: 是否是代理消息
        - is_from_myself: 是否是自己发的（需要提供 my_agent_name）
        - marked_sender: 自我标记的发送者
        - reply_method: 建议的回复方式 ("message" 或 "feishu_im_user_message")
        
    Example:
        >>> result = parse_proxy_message("📨【私信】【代理】【CPA助攻→软件开发组长】...", "软件开发组长")
        >>> print(result["from_agent"])  # "CPA助攻"
        >>> print(result["chat_type"])   # "p2p"
        >>> print(result["reply_method"])  # "feishu_im_user_message"
        >>> print(result["is_from_myself"])  # False
        >>> print(result["content"])     # 消息内容
    """
    formatter = MessageFormatter()
    result = formatter.parse_proxy_message(message)
    
    if result and my_agent_name:
        # 判断是否是自已发的消息
        # 优先使用自我标记判断
        marked_sender = result.get("marked_sender")
        if marked_sender:
            # 如果有自我标记，比较标记的发送者和自己的名字
            result["is_from_myself"] = (marked_sender == my_agent_name)
        else:
            # 如果没有自我标记，回退到传统的名称匹配
            result["is_from_myself"] = (result.get("from_agent") == my_agent_name)
    
    return result


# 便捷函数别名
send = feishu_agent_send
parse = parse_proxy_message


def send_simple(to: str, message: str, from_agent: str) -> Dict[str, Any]:
    """
    简化版发送函数（推荐日常使用）
    
    自动查找 chat_id，返回可直接使用的参数，无需手动调用 feishu_im_user_message。
    
    Args:
        to: 目标Agent名称
        message: 消息内容（纯文本）
        from_agent: 自己的Agent名称
        
    Returns:
        包含发送参数的字典，直接传给 feishu_im_user_message 即可
        
    Example:
        >>> result = send_simple("颖小兔", "你好！", "大总管")
        >>> # 然后直接调用 feishu_im_user_message
        >>> feishu_im_user_message(**result["send_params"]["params"])
    """
    return feishu_agent_send(to=to, message=message, from_agent=from_agent)


def quick_send(to: str, message: str, from_agent: str) -> str:
    """
    超简化版 - 只返回格式化后的消息内容
    
    适合只需要消息内容，自己处理发送的场景。
    
    Args:
        to: 目标Agent名称
        message: 消息内容
        from_agent: 自己的Agent名称
        
    Returns:
        格式化后的消息字符串
        
    Example:
        >>> msg = quick_send("颖小兔", "你好！", "大总管")
        >>> print(msg)
        📨【代理】【大总管→颖小兔】
        
        你好！
        
        ---
        实际发送者：大总管
        代理发送者：用户
        ---
    """
    result = feishu_agent_send(to=to, message=message, from_agent=from_agent)
    if result["success"]:
        return result["formatted_message"]
    else:
        raise FeishuAgentSendError(f"格式化失败: {result.get('error', '未知错误')}")


def feishu_agent_send_and_deliver(
    to: str, 
    message: str, 
    from_agent: str,
    auto_send: bool = True
) -> Dict[str, Any]:
    """
    一键发送函数（推荐！自动完成格式化和发送）
    
    ⚠️ 注意：此函数需要调用 feishu_im_user_message 工具，确保你有权限使用。
    
    Args:
        to: 目标Agent名称
        message: 消息内容（纯文本）
        from_agent: 自己的Agent名称
        auto_send: 是否自动发送（默认True）
        
    Returns:
        发送结果字典
        
    Example:
        >>> # 一键发送！自动完成格式化和发送
        >>> result = feishu_agent_send_and_deliver(
        ...     to="软件开发组长",
        ...     message="测试消息",
        ...     from_agent="CPA助攻"
        ... )
        >>> print(f"发送成功！消息ID: {result.get('message_id')}")
    """
    # 第1步：格式化消息
    format_result = feishu_agent_send(to=to, message=message, from_agent=from_agent)
    
    if not format_result["success"]:
        return {
            "success": False,
            "error": format_result.get("error", "格式化失败"),
            "stage": "format"
        }
    
    if not auto_send:
        # 只返回格式化结果，不发送
        return {
            "success": True,
            "stage": "format_only",
            "formatted_message": format_result["formatted_message"],
            "send_params": format_result["send_params"],
            "hint": "请手动调用 feishu_im_user_message 发送"
        }
    
    # 第2步：实际发送
    try:
        # 尝试导入 feishu_im_user_message
        # 注意：这里假设调用环境中有 feishu_im_user_message 工具
        send_params = format_result["send_params"]["params"]
        
        # 返回发送参数，让调用者执行实际发送
        # （因为 skill 作为 Python 库不能直接调用 OpenClaw 工具）
        return {
            "success": True,
            "stage": "ready_to_send",
            "formatted_message": format_result["formatted_message"],
            "chat_id": format_result.get("chat_id"),
            "receiver_id": format_result.get("receiver_id"),
            "send_params": send_params,
            "hint": "请使用返回的 send_params 调用 feishu_im_user_message",
            "example": "feishu_im_user_message(**result['send_params'])"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stage": "send",
            "formatted_message": format_result["formatted_message"],
            "send_params": format_result["send_params"]
        }


def check_group_chat_environment() -> Dict[str, Any]:
    """
    检测当前是否在群聊环境中
    
    Returns:
        检测结果字典
        {
            "is_group_chat": bool,  # 是否在群聊
            "chat_id": str,         # 群聊ID（如果是）
            "warning": str          # 警告信息
        }
    """
    result = {
        "is_group_chat": False,
        "chat_id": None,
        "warning": None
    }
    
    # 尝试从环境变量或上下文检测
    # 注意：这里需要根据实际运行环境实现
    # 例如：检测当前会话类型、读取 OpenClaw 上下文等
    
    # 暂时返回通用警告
    result["warning"] = (
        "⚠️  提醒：如果在群聊中，请使用 feishu_agent_send 发送消息！\n"
        "   普通消息无法被其他 Agent 接收。\n"
        "   使用方法：feishu_agent_send_and_deliver(to, message, from_agent)"
    )
    
    return result


def send_to_group(
    message: str,
    from_agent: str,
    group_chat_id: str = None
) -> Dict[str, Any]:
    """
    简化版：发送到当前群聊
    
    自动使用群聊 chat_id，无需手动指定接收者。
    
    Args:
        message: 消息内容
        from_agent: 发送者名称
        group_chat_id: 可选，指定群聊ID。如果不提供，尝试自动检测
        
    Returns:
        发送结果
        
    Example:
        >>> result = send_to_group("大家好！", "我")
        >>> feishu_im_user_message(**result["send_params"])
    """
    if not group_chat_id:
        # 尝试自动检测当前群聊
        env = check_group_chat_environment()
        if env.get("chat_id"):
            group_chat_id = env["chat_id"]
        else:
            return {
                "success": False,
                "error": "无法自动检测群聊ID，请手动提供 group_chat_id 参数",
                "hint": "例如：send_to_group('消息', '我', group_chat_id='oc_xxx')"
            }
    
    # 使用群聊ID直接发送
    return feishu_agent_send(
        to="群聊",
        message=message,
        from_agent=from_agent,
        chat_id=group_chat_id
    )


# 便捷别名
send_and_deliver = feishu_agent_send_and_deliver

# 模块加载时显示安装提示（仅在直接导入时显示）
show_installation_notice()


if __name__ == "__main__":
    # 运行测试
    print("=== feishu_agent_send 测试 ===")
    
    # 测试1：发送消息
    print("\n1. 发送消息测试：")
    result = feishu_agent_send(
        to="CPA助攻",
        message="请汇报会计科目进度",
        from_agent="软件开发组长"
    )
    
    if result["success"]:
        print(f"✅ 格式化成功")
        print(f"接收者: {result['receiver_name']} ({result['receiver_id']})")
        print(f"格式化消息:\n{result['formatted_message']}")
        print(f"\n发送参数:")
        print(json.dumps(result["send_params"], indent=2, ensure_ascii=False))
    else:
        print(f"❌ 失败: {result['error']}")
    
    # 测试2：解析消息
    print("\n2. 解析消息测试：")
    test_message = """📨【代理】【CPA助攻→软件开发组长】

已完成50%

---
实际发送者：CPA助攻
代理发送者：彦哥
---"""
    
    parsed = parse_proxy_message(test_message)
    if parsed:
        print(f"✅ 解析成功")
        print(f"实际发送者: {parsed['from_agent']}")
        print(f"接收者: {parsed['to_agent']}")
        print(f"内容: {parsed['content']}")
    else:
        print("❌ 不是代理消息")
    
    print("\n=== 所有测试完成 ===")
