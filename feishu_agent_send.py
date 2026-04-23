"""
feishu_agent_send - 飞书多 Agent 通信工具 v3.1.0

核心原则：一个 skill，所有 agent 共用，自动识别身份
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
        return {"version": "3.1.0", "agents": {}, "self_by_agent": {}}

    @classmethod
    def save(cls, data: Dict[str, Any]):
        path = cls._config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

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

    # v3.1.0: 使用 JSON 元数据块替代 HTML 注释
    metadata = {
        'from_agent': from_agent,
        'to_agent': to,
        'from_chat_id': my_chat_id,
        'chat_type': ct,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '3.1.0'
    }
    metadata_json = json.dumps(metadata, ensure_ascii=False)

    formatted = (
        f'📨【{type_label}】【代理】【{from_agent}→{to}】\n\n'
        f'{message}\n\n'
        f'---\n'
        f'实际发送者：{from_agent}\n'
        f'代理发送者：用户\n'
        f'元数据：{metadata_json}\n'
        f'---'
    )

    return {
        'success': True,
        'chat_id': chat_id,
        'chat_type': ct,
        'formatted_message': formatted,
        'metadata': metadata
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
    content = json.dumps({'text': result['formatted_message']}, ensure_ascii=False)

    deliver = {
        'success': True,
        'mode': 'deliver',
        'instruction': (
            f'请执行以下操作完成发送：\n\n'
            f'feishu_im_user_message(\n'
            f"    action='send',\n"
            f"    receive_id_type='chat_id',\n"
            f"    receive_id='{chat_id}',\n"
            f"    msg_type='text',\n"
            f"    content='{content}'\n"
            f')'
        ),
        'send_params': {
            'action': 'send',
            'receive_id_type': 'chat_id',
            'receive_id': chat_id,
            'msg_type': 'text',
            'content': content
        },
        'preview': result['formatted_message'],
        'chat_id': chat_id,
        'chat_type': ct,
        'to': to,
        'from_agent': from_agent
    }
    return deliver
