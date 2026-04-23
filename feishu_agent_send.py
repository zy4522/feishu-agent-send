"""
feishu_agent_send - 飞书多 Agent 通信工具 v3.6.0

核心原则：一个 skill，所有 agent 共用，自动识别身份

v3.6.0 更新：
- 保留群聊 @ 功能（post 消息 + app_id）
- 吸收 v3.1.0 代码改进：JSON 元数据、代码精简、Bug 修复
- 统一 JSON 输出

配置文件位置：~/.feishu_agent_send/config.json
"""

import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone


class AgentConfig:
    """本地 Agent 配置管理"""

    @classmethod
    def _config_path(cls) -> str:
        return os.path.expanduser('~/.feishu_agent_send/config.json')

    @classmethod
    def load(cls) -> Dict[str, Any]:
        path = cls._config_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"version": "3.6.0", "agents": {}, "self_by_agent": {}}

    @classmethod
    def save(cls, data: Dict[str, Any]):
        path = cls._config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def get_agent_app_id(cls, name: str) -> Optional[str]:
        """获取 Agent 的飞书 app_id（用于群聊 @）"""
        config = cls.load()
        agent = config.get('agents', {}).get(name)
        if not agent:
            return None
        if isinstance(agent, dict):
            if 'app_id' in agent:
                return agent['app_id']
            for scene in ['p2p', 'group']:
                if scene in agent and isinstance(agent[scene], dict):
                    if 'app_id' in agent[scene]:
                        return agent[scene]['app_id']
        return None

    @classmethod
    def set_agent_app_id(cls, name: str, app_id: str, chat_type: str = 'group'):
        """设置 Agent 的 app_id"""
        config = cls.load()
        if 'agents' not in config:
            config['agents'] = {}
        if name not in config['agents']:
            config['agents'][name] = {}
        
        agent = config['agents'][name]
        if isinstance(agent, dict) and ('p2p' in agent or 'group' in agent):
            if chat_type in agent and isinstance(agent[chat_type], dict):
                agent[chat_type]['app_id'] = app_id
            else:
                agent['app_id'] = app_id
        else:
            if isinstance(agent, dict):
                agent['app_id'] = app_id
            else:
                config['agents'][name] = {'app_id': app_id}
        
        cls.save(config)

    @classmethod
    def get_agent_info(cls, name: str, chat_type: str = None) -> Optional[Dict]:
        config = cls.load()
        agent = config.get('agents', {}).get(name)
        if not agent:
            return None
        if chat_type and isinstance(agent, dict) and chat_type in agent:
            info = agent[chat_type].copy()
            info['chat_type'] = chat_type
            return info
        if isinstance(agent, dict) and 'chat_id' in agent:
            return {'chat_id': agent['chat_id'], 'chat_type': agent.get('chat_type', 'p2p')}
        if isinstance(agent, dict) and 'p2p' in agent:
            info = agent['p2p'].copy()
            info['chat_type'] = 'p2p'
            return info
        return None

    @classmethod
    def get_self(cls, agent_name: str) -> Optional[Dict]:
        config = cls.load()
        return config.get('self_by_agent', {}).get(agent_name)

    @classmethod
    def get_all_self(cls) -> Dict[str, Dict]:
        config = cls.load()
        return config.get('self_by_agent', {})

    @classmethod
    def set_self(cls, agent_name: str, chat_id: str):
        config = cls.load()
        if 'self_by_agent' not in config:
            config['self_by_agent'] = {}
        config['self_by_agent'][agent_name] = {'chat_id': chat_id}
        cls.save(config)

    @classmethod
    def detect_current_agent(cls) -> Optional[str]:
        # 优先级：AGENT_NAME > OPENCLAW_AGENT_ID > 工作区路径
        for env_key in ['AGENT_NAME', 'OPENCLAW_AGENT_ID']:
            val = os.environ.get(env_key)
            if val:
                return val.lower()
        cwd = os.getcwd()
        workspace_dir = os.path.expanduser('~/.openclaw/workspace')
        try:
            if os.path.commonpath([os.path.abspath(cwd), os.path.abspath(workspace_dir)]) == os.path.abspath(workspace_dir):
                rel = os.path.relpath(cwd, workspace_dir)
                parts = rel.split(os.sep)
                if len(parts) > 1 and parts[0] == 'agents':
                    return parts[1].lower()
        except ValueError:
            pass
        return None


def list_known_agents() -> list:
    config = AgentConfig.load()
    return list(config.get('agents', {}).keys())


def build_post_content(
    message: str,
    from_agent: str,
    to_agent: str,
    at_app_id: str = None
) -> Dict[str, Any]:
    """
    构造飞书 post 消息内容（富文本，支持 @）
    
    Args:
        message: 消息正文
        from_agent: 发送者名称
        to_agent: 目标 Agent 名称
        at_app_id: 要 @ 的 Agent app_id（如 cli_xxx）
    
    Returns:
        飞书 post 消息格式的 content 字典
    """
    content_blocks = []
    
    # 如果有 app_id，添加 @ 标签（放在最前面，最醒目）
    if at_app_id:
        content_blocks.append({
            "tag": "at",
            "user_id": at_app_id,
            "user_name": to_agent
        })
        content_blocks.append({"tag": "text", "text": "\n\n"})
    
    # 添加消息正文
    content_blocks.append({"tag": "text", "text": message})
    
    # 添加代理标识（小字）
    content_blocks.append({"tag": "text", "text": f"\n\n---\n📨 群聊代理发送 | {from_agent} → {to_agent}"})
    
    return {
        "zh_cn": {
            "title": f"@{to_agent} 你有新消息",
            "content": [content_blocks]
        }
    }


def build_text_content(
    message: str,
    from_agent: str,
    to_agent: str,
    my_chat_id: str = None
) -> str:
    """
    构造纯文本消息内容（私聊用）
    """
    type_label = '私信'
    
    # v3.6.0: 使用 JSON 元数据块替代 HTML 注释
    metadata = {
        'from_agent': from_agent,
        'to_agent': to_agent,
        'from_chat_id': my_chat_id,
        'chat_type': 'p2p',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '3.6.0'
    }
    metadata_json = json.dumps(metadata, ensure_ascii=False)
    
    formatted = (
        f'📨【{type_label}】【代理】【{from_agent}→{to_agent}】\n\n'
        f'{message}\n\n'
        f'---\n'
        f'实际发送者：{from_agent}\n'
        f'代理发送者：用户\n'
        f'元数据：{metadata_json}\n'
        f'---'
    )
    
    return json.dumps({'text': formatted}, ensure_ascii=False)


def feishu_agent_send(
    to: str,
    message: str,
    from_agent: str = None,
    chat_type: str = None
) -> Dict[str, Any]:
    """
    格式化 Agent 间通信消息

    Args:
        to: 目标 Agent 名称
        message: 消息内容
        from_agent: 发送者名称（自动检测）
        chat_type: 强制指定聊天类型

    Returns:
        包含发送参数的字典
    """
    if not from_agent:
        from_agent = AgentConfig.detect_current_agent()

    self_info = AgentConfig.get_self(from_agent) if from_agent else None
    my_chat_id = self_info.get('chat_id') if self_info else None

    agent_info = AgentConfig.get_agent_info(to, chat_type)
    if not agent_info:
        agent_info = AgentConfig.get_agent_info(to)

    if not agent_info:
        return {
            'success': False,
            'error': f"找不到 Agent '{to}'",
            'available_agents': list_known_agents()[:10]
        }

    chat_id = agent_info.get('chat_id')
    ct = chat_type or agent_info.get('chat_type', 'p2p')
    type_label = '私信' if ct == 'p2p' else '群'

    # 获取目标 Agent 的 app_id（群聊 @ 用）
    to_app_id = AgentConfig.get_agent_app_id(to) if ct == 'group' else None
    
    # 根据聊天类型构造不同消息格式
    if ct == 'group' and to_app_id:
        # 群聊：使用 post 富文本格式，包含 @
        content_obj = build_post_content(message, from_agent, to, to_app_id)
        content = json.dumps(content_obj, ensure_ascii=False)
        msg_type = 'post'
    else:
        # 私聊：使用 text 纯文本格式
        content = build_text_content(message, from_agent, to, my_chat_id)
        msg_type = 'text'

    return {
        'success': True,
        'chat_id': chat_id,
        'chat_type': ct,
        'msg_type': msg_type,
        'content': content,
        'formatted_message': content,
        'to_app_id': to_app_id
    }


def feishu_agent_send_and_deliver(
    to: str,
    message: str,
    from_agent: str = None,
    chat_type: str = None
) -> Dict[str, Any]:
    """
    一站式发送：格式化 + 发送指令
    """
    result = feishu_agent_send(to, message, from_agent, chat_type)
    if not result.get('success'):
        return result

    chat_id = result['chat_id']
    ct = result['chat_type']
    msg_type = result.get('msg_type', 'text')
    content = result['content']
    to_app_id = result.get('to_app_id')
    
    # 构造 feishu_im_user_message 调用指令
    instruction = (
        f'请执行以下操作完成发送：\n\n'
        f'feishu_im_user_message(\n'
        f"    action='send',\n"
        f"    receive_id_type='chat_id',\n"
        f"    receive_id='{chat_id}',\n"
        f"    msg_type='{msg_type}',\n"
        f"    content='{content}'\n"
        f')'
    )
    
    if to_app_id:
        instruction += (
            f'\n\n注：消息包含 @{to} 的 @ 提醒（app_id: {to_app_id}）'
        )

    deliver = {
        'success': True,
        'mode': 'deliver',
        'instruction': instruction,
        'send_params': {
            'action': 'send',
            'receive_id_type': 'chat_id',
            'receive_id': chat_id,
            'msg_type': msg_type,
            'content': content
        },
        'preview': content,
        'chat_id': chat_id,
        'chat_type': ct,
        'msg_type': msg_type,
        'to': to,
        'from_agent': from_agent,
        'to_app_id': to_app_id,
    }
    return deliver
