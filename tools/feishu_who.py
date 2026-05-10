#!/usr/bin/env python3
"""
feishu_who.py - 查看所有 Agent 信息 v3.10.3

输出格式：统一 JSON
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig

try:
    from _version import __version__
except ImportError:
    __version__ = "3.10.3"  # fallback，与_version.py保持一致


def main():
    config = AgentConfig.load()
    agents = config.get('agents', {})
    self_by_agent = config.get('self_by_agent', {})
    
    result = {
        'version': config.get('version', __version__),
        'total': len(agents),
        'agents': {}
    }
    
    for name, info in agents.items():
        agent_entry = {
            'self_configured': name in self_by_agent,
            'scenes': {}
        }
        
        if isinstance(info, dict):
            if 'p2p' in info:
                scene_info = {
                    'chat_id_prefix': info['p2p'].get('chat_id', 'N/A')[:20] + '...'
                }
                if 'open_id' in info['p2p']:
                    scene_info['open_id_prefix'] = info['p2p']['open_id'][:20] + '...'
                agent_entry['scenes']['p2p'] = scene_info
            if 'group' in info:
                scene_info = {
                    'chat_id_prefix': info['group'].get('chat_id', 'N/A')[:20] + '...'
                }
                # v3.10.3: 显示 open_id 配置状态
                if 'open_id' in info['group']:
                    scene_info['open_id_prefix'] = info['group']['open_id'][:20] + '...'
                    scene_info['at_support'] = '✅'  # 支持 @ 提醒
                elif 'app_id' in info['group']:
                    scene_info['at_support'] = '⚠️'  # 只有 app_id，@ 可能不工作
                else:
                    scene_info['at_support'] = '❌'  # 不支持 @ 提醒
                agent_entry['scenes']['group'] = scene_info
            if 'chat_id' in info:
                # 旧格式兼容
                agent_entry['scenes']['legacy'] = {
                    'chat_type': info.get('chat_type', 'p2p'),
                    'chat_id_prefix': info['chat_id'][:20] + '...'
                }
        
        if name in self_by_agent:
            agent_entry['self'] = {
                'chat_id_prefix': self_by_agent[name].get('chat_id', 'N/A')[:20] + '...'
            }
        
        result['agents'][name] = agent_entry
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
