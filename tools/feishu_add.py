#!/usr/bin/env python3
"""
feishu_add.py - 添加 Agent 到配置
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig


def check_duplicate_for_add(chat_id, chat_type, agent_name):
    """检查添加 Agent 时的潜在冲突"""
    config = AgentConfig.load()
    agents = config.get('agents', {})
    self_by_agent = config.get('self_by_agent', {})
    
    warnings = []
    
    # 检查是否和 self 配置重复（容易搞混自己和对方）
    for self_name, self_info in self_by_agent.items():
        if self_info.get('chat_id') == chat_id:
            warnings.append({
                'type': 'self_conflict',
                'message': f'此 chat_id 与 self 配置 {self_name} 重复',
                'detail': '容易搞混自己和对方，建议确认'
            })
    
    # 检查私聊重复（可能是错误）
    if chat_type == 'p2p':
        for other_agent, other_config in agents.items():
            if other_agent == agent_name:
                continue
            
            if isinstance(other_config, dict):
                # 检查单场景配置
                if other_config.get('chat_id') == chat_id and other_config.get('chat_type') == 'p2p':
                    warnings.append({
                        'type': 'p2p_duplicate',
                        'message': f'私聊 chat_id 与 {other_agent} 重复',
                        'detail': '私聊应该是唯一的，建议检查'
                    })
                # 检查多场景配置的 p2p
                if 'p2p' in other_config and other_config['p2p'].get('chat_id') == chat_id:
                    warnings.append({
                        'type': 'p2p_duplicate',
                        'message': f'私聊 chat_id 与 {other_agent} (p2p) 重复',
                        'detail': '私聊应该是唯一的，建议检查'
                    })
    
    return warnings


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
    
    # 检查潜在冲突
    warnings = check_duplicate_for_add(chat_id, chat_type, agent_name)
    if warnings:
        print(f"\n⚠️  警告: 发现潜在配置冲突:")
        for w in warnings:
            print(f"   • {w['message']}")
            print(f"     {w['detail']}")
        print(f"\n   确定要继续添加吗？")
        # 自动化环境中不等待输入，继续但给出警告
    
    config = AgentConfig.load()
    if 'agents' not in config:
        config['agents'] = {}
    
    existing = config['agents'].get(agent_name)
    
    if existing is None:
        # 全新 Agent，单场景配置
        config['agents'][agent_name] = {'chat_id': chat_id, 'chat_type': chat_type}
    elif isinstance(existing, dict) and ('p2p' in existing or 'group' in existing):
        # 已有多场景配置，更新/添加指定场景
        existing[chat_type] = {'chat_id': chat_id}
    elif isinstance(existing, dict) and 'chat_id' in existing:
        # 已有单场景配置，升级为多场景
        old_chat_id = existing.get('chat_id')
        old_type = existing.get('chat_type', 'p2p')
        config['agents'][agent_name] = {
            old_type: {'chat_id': old_chat_id},
            chat_type: {'chat_id': chat_id}
        }
    else:
        # 异常结构，直接覆盖
        config['agents'][agent_name] = {'chat_id': chat_id, 'chat_type': chat_type}
    
    AgentConfig.save(config)
    print(f"✅ 已添加 {agent_name} ({chat_type}): {chat_id[:20]}...")
    
    if warnings:
        print(f"\n⚠️  注意: 添加完成但存在警告（见上方），建议检查配置")


if __name__ == '__main__':
    main()
