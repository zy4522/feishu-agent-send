#!/usr/bin/env python3
"""
feishu_who.py - 查看所有 Agent 信息 v3.1.0

输出格式：统一 JSON
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig


def main():
    config = AgentConfig.load()
    agents = config.get('agents', {})
    self_by_agent = config.get('self_by_agent', {})
    
    result = {
        'version': config.get('version', '3.1.0'),
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
                agent_entry['scenes']['p2p'] = {
                    'chat_id_prefix': info['p2p'].get('chat_id', 'N/A')[:20] + '...'
                }
            if 'group' in info:
                agent_entry['scenes']['group'] = {
                    'chat_id_prefix': info['group'].get('chat_id', 'N/A')[:20] + '...'
                }
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
