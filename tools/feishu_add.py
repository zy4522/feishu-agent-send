#!/usr/bin/env python3
"""
feishu_add.py - 添加 Agent 到配置
"""

import sys
import os
import json

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
    
    # v3.1.0 修复：正确处理新旧配置迁移
    existing = config['agents'][agent_name]
    
    # 如果已经是场景结构，直接追加/覆盖
    if isinstance(existing, dict) and ('p2p' in existing or 'group' in existing):
        existing[chat_type] = {'chat_id': chat_id}
    elif isinstance(existing, dict) and 'chat_id' in existing:
        # 旧格式迁移：把单 chat_id 拆到场景结构
        old_chat_id = existing.pop('chat_id')
        old_type = existing.pop('chat_type', 'p2p')
        config['agents'][agent_name] = {
            old_type: {'chat_id': old_chat_id},
            chat_type: {'chat_id': chat_id}
        }
    else:
        # 空或无效配置，新建
        config['agents'][agent_name] = {chat_type: {'chat_id': chat_id}}
    
    AgentConfig.save(config)
    print(json.dumps({
        'success': True,
        'agent': agent_name,
        'chat_type': chat_type,
        'chat_id_prefix': chat_id[:20] + '...'
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
