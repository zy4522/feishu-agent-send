#!/usr/bin/env python3
"""
feishu_set_self.py - 设置当前 Agent 的 self 信息

用法：
  python3 feishu_set_self.py <Agent名称> <chat_id>

示例：
  python3 feishu_set_self.py kfj oc_xxx
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig


def main():
    if len(sys.argv) < 3:
        print("用法: python3 feishu_set_self.py <Agent名称> <chat_id>")
        print("示例: python3 feishu_set_self.py kfj oc_xxx")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    chat_id = sys.argv[2]
    
    AgentConfig.set_self(agent_name, chat_id)
    
    all_self = AgentConfig.get_all_self()
    result = {
        'success': True,
        'agent': agent_name,
        'chat_id_prefix': chat_id[:20] + '...',
        'total_configured': len(all_self),
        'all_agents': {
            name: {'chat_id_prefix': info.get('chat_id', 'N/A')[:20] + '...'}
            for name, info in all_self.items()
        }
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
