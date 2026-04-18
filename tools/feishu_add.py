#!/usr/bin/env python3
"""
feishu_add.py - 添加 Agent 到配置
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig


def main():
    if len(sys.argv) < 3:
        print("用法: python3 feishu_add.py <Agent名称> <chat_id> [--chat-type p2p|group]")
        print("示例: python3 feishu_add.py kfj oc_xxx")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    chat_id = sys.argv[2]
    chat_type = 'p2p'
    
    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--chat-type' and i + 1 < len(sys.argv):
            chat_type = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    config = AgentConfig.load()
    if 'agents' not in config:
        config['agents'] = {}
    
    if agent_name not in config['agents']:
        config['agents'][agent_name] = {}
    
    # 如果已有多个场景，用场景结构
    existing = config['agents'][agent_name]
    if isinstance(existing, dict) and ('p2p' in existing or 'group' in existing):
        existing[chat_type] = {'chat_id': chat_id}
    else:
        config['agents'][agent_name] = {
            'p2p': {'chat_id': chat_id},
            'group': existing.get('chat_id') if isinstance(existing, dict) else None
        }
        # 清理 None
        if config['agents'][agent_name].get('group') is None:
            del config['agents'][agent_name]['group']
    
    AgentConfig.save(config)
    print(f"✅ 已添加 {agent_name} ({chat_type}): {chat_id[:20]}...")


if __name__ == '__main__':
    main()
