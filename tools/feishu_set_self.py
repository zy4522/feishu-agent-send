#!/usr/bin/env python3
"""
feishu_set_self.py - 设置当前 Agent 的 self 信息 + 检查 openclaw.json 绑定

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

KNOWN_AGENTS = ['main', 'ying', 'kfj', 'zz', 'ayy', 'iio', 'cpaas']
OPENCLAW_CONFIG = os.path.expanduser('~/.openclaw/openclaw.json')


def check_openclaw_routes():
    """检查 openclaw.json 中的 feishu 路由绑定"""
    if not os.path.exists(OPENCLAW_CONFIG):
        print(f"\n⚠️  未找到配置文件: {OPENCLAW_CONFIG}")
        return

    try:
        with open(OPENCLAW_CONFIG, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"\n⚠️  读取 openclaw.json 失败: {e}")
        return

    channels = config.get('channels', {})
    feishu = channels.get('feishu', {})
    accounts = feishu.get('accounts', {})

    if not accounts:
        print("\n⚠️  openclaw.json 中未找到 feishu accounts 配置")
        return

    print(f"\n📡 openclaw.json Feishu Accounts 状态:")
    print(f"  默认账号: {feishu.get('defaultAccount', '未设置')}")

    for agent in KNOWN_AGENTS:
        if agent in accounts:
            app_id = accounts[agent].get('appId', '')[:16]
            print(f"  ✅ {agent}: appId={app_id}...")
        else:
            print(f"  ❌ {agent}: 未配置")


def check_duplicate_chat_id(chat_id, exclude_agent=None):
    """检查 chat_id 是否已被其他 Agent 使用"""
    config = AgentConfig.load()
    agents = config.get('agents', {})
    self_by_agent = config.get('self_by_agent', {})
    
    duplicates = []
    
    # 检查 agents 配置
    for agent_name, agent_config in agents.items():
        if agent_name == exclude_agent:
            continue
            
        if isinstance(agent_config, dict):
            # 多场景配置
            for scene in ['p2p', 'group']:
                if scene in agent_config and isinstance(agent_config[scene], dict):
                    if agent_config[scene].get('chat_id') == chat_id:
                        duplicates.append({
                            'agent': agent_name,
                            'scene': scene,
                            'type': 'agent'
                        })
            # 单场景配置（旧格式）
            if 'chat_id' in agent_config and agent_config['chat_id'] == chat_id:
                duplicates.append({
                    'agent': agent_name,
                    'scene': agent_config.get('chat_type', 'p2p'),
                    'type': 'agent'
                })
    
    # 检查 self 配置
    for self_name, self_info in self_by_agent.items():
        if self_name == exclude_agent:
            continue
        if self_info.get('chat_id') == chat_id:
            duplicates.append({
                'agent': self_name,
                'scene': 'self',
                'type': 'self'
            })
    
    return duplicates


def main():
    if len(sys.argv) < 3:
        print("用法: python3 feishu_set_self.py <Agent名称> <chat_id>")
        print("示例: python3 feishu_set_self.py kfj oc_xxx")
        print("\n说明:")
        print("  - Agent名称: main, ying, kfj, zz, ayy, iio, cpaas")
        print("  - chat_id: 该 Agent 的飞书会话 ID (oc_xxx 格式)")
        sys.exit(1)

    agent_name = sys.argv[1].lower()
    chat_id = sys.argv[2]
    
    # 检查重复
    duplicates = check_duplicate_chat_id(chat_id, exclude_agent=agent_name)
    if duplicates:
        print(f"\n⚠️  警告: chat_id {chat_id[:20]}... 已被以下 Agent 使用:")
        for dup in duplicates:
            if dup['type'] == 'self':
                print(f"   • {dup['agent']} (self配置)")
            else:
                print(f"   • {dup['agent']} ({dup['scene']})")
        print(f"\n   确定要继续设置吗？这可能导致配置混淆。")
        # 注意：在自动化环境中不等待用户输入，直接继续但给出警告

    AgentConfig.set_self(agent_name, chat_id)
    print(f"✅ 已设置 {agent_name} 的 self 信息: {chat_id[:20]}...")

    all_self = AgentConfig.get_all_self()
    if len(all_self) > 1:
        print("\n已配置的 Agent self 列表:")
        for name, info in all_self.items():
            cid = info.get('chat_id', '')[:20]
            print(f"  • {name}: {cid}...")

    check_openclaw_routes()

    if len(all_self) == 1:
        print(f"\n💡 首次设置完成！接下来：")
        print(f"  1. 确认 openclaw.json 中 {agent_name} 的 account 已配置（见上方检查）")
        print(f"  2. 添加其他 Agent: python3 feishu_add.py <目标Agent> <chat_id>")
        print(f"  3. 发送测试消息: python3 feishu_send.py <目标> '你好' --deliver")


if __name__ == '__main__':
    main()
