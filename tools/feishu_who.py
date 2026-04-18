#!/usr/bin/env python3
"""
feishu_who.py - 查看所有 Agent 信息
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig, list_known_agents


def main():
    config = AgentConfig.load()
    agents = config.get('agents', {})
    self_by_agent = config.get('self_by_agent', {})
    
    print("📋 已知 Agent 列表\n" + "=" * 50)
    
    for name, info in agents.items():
        print(f"\n👤 {name}")
        
        # 显示对话配置
        if isinstance(info, dict):
            if 'p2p' in info:
                cid = info['p2p'].get('chat_id', 'N/A')[:20]
                print(f"   私聊: {cid}...")
            if 'group' in info:
                cid = info['group'].get('chat_id', 'N/A')[:20]
                print(f"   群聊: {cid}...")
            if 'chat_id' in info:
                cid = info['chat_id'][:20]
                print(f"   对话: {cid}...")
        
        # 显示 self 配置
        if name in self_by_agent:
            cid = self_by_agent[name].get('chat_id', 'N/A')[:20]
            print(f"   ✅ self: {cid}...")
        else:
            print(f"   ❌ 未设置 self")
    
    print("\n" + "=" * 50)
    print(f"总计: {len(agents)} 个 Agent")


if __name__ == '__main__':
    main()
