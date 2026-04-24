#!/usr/bin/env python3
"""
feishu_send.py - 发送消息给飞书 Agent v3.8.0

用法：
  python3 feishu_send.py <目标Agent> <消息内容> [选项]
  python3 feishu_send.py "Agent1,Agent2,Agent3" <消息内容> [选项]  # 批量发送

选项：
  --from            发送者名称（自动检测，单配置时可选）
  --chat-type       p2p 或 group，强制指定类型
  --actual-sender   实际发送者（人类身份，与AI代理区分）
  --deliver         输出调用指令（推荐）
  --execute         尝试直接执行发送（需要OpenClaw环境）

示例：
  # 单个目标
  python3 feishu_send.py ying "你好" --deliver
  
  # 批量发送（逗号分隔多个目标）
  python3 feishu_send.py "kfj,ying,zz" "会议通知" --chat-type group --deliver
  
  # 代理发送（人类经由AI发送）
  python3 feishu_send.py kfj "消息" --from kfj --actual-sender kclaw --deliver
"""

import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig, feishu_agent_send_and_deliver, list_known_agents


def send_to_agent(to_agent, message, from_agent, chat_type_override, actual_sender, deliver_mode, execute_mode):
    """发送消息给单个 Agent"""
    
    # 获取目标 Agent 信息
    agent_info = AgentConfig.get_agent_info(to_agent, chat_type_override)
    if not agent_info:
        agent_info = AgentConfig.get_agent_info(to_agent)
    
    if not agent_info:
        return {
            'success': False,
            'error': f"找不到 Agent '{to_agent}'",
            'available_agents': list_known_agents()[:10],
            'v3.8.0_help': f'请先添加：python3 feishu_add.py {to_agent} oc_xxx'
        }
    
    chat_id = agent_info.get('chat_id')
    # Bug 修复：验证 chat_type 只能是 p2p 或 group
    valid_chat_types = ['p2p', 'group']
    if chat_type_override and chat_type_override not in valid_chat_types:
        return {
            'success': False,
            'error': f"无效的 chat_type: '{chat_type_override}'",
            'valid_options': valid_chat_types,
            'hint': '请使用 --chat-type p2p 或 --chat-type group'
        }
    chat_type = chat_type_override or agent_info.get('chat_type', 'p2p')
    
    # 检查多场景配置
    config = AgentConfig.load()
    agent_config = config.get('agents', {}).get(to_agent)
    
    multi_scene = False
    if isinstance(agent_config, dict) and ('p2p' in agent_config or 'group' in agent_config):
        available = [k for k in ['p2p', 'group'] if k in agent_config]
        if len(available) > 1 and not chat_type_override:
            multi_scene = True
            chosen = '私聊' if chat_type == 'p2p' else '群聊'
            print(f"⚠️ Agent '{to_agent}' 有多个配置：私聊、群聊")
            print(f"   已自动选择：{chosen}")
            print(f"   如需切换，请使用：--chat-type {'group' if chat_type == 'p2p' else 'p2p'}")
    
    # 格式化消息（根据聊天类型选择格式）
    ct = chat_type_override or agent_info.get('chat_type', 'p2p')
    
    # 获取目标 Agent 的 app_id（群聊 @ 用）
    to_app_id = AgentConfig.get_agent_app_id(to_agent) if ct == 'group' else None
    
    # 调用 feishu_agent_send_and_deliver
    result = feishu_agent_send_and_deliver(to_agent, message, from_agent, chat_type_override, actual_sender)
    
    if deliver_mode:
        if result.get('success'):
            print(f"\n✅ 消息已准备好，发送给 {to_agent}（{'群聊' if ct == 'group' else '私聊'}）")
            if multi_scene:
                print(f"   注意：该 Agent 有多个场景，当前选择 {'群聊' if ct == 'group' else '私聊'}")
            if ct == 'group':
                if to_app_id:
                    print(f"   📎 包含 @{to_agent} 的 @ 提醒")
            if actual_sender:
                print(f"   👤 实际发送者：{actual_sender}（代理执行者：{from_agent}）")
            print(f"\n📋 {result.get('instruction', '')}")
        else:
            return result
    elif execute_mode:
        if result.get('success'):
            send_params = result.get('send_params', {})
            print(f"\n✅ 消息已准备好，发送给 {to_agent}（{'群聊' if ct == 'group' else '私聊'}）")
            if multi_scene:
                print(f"   注意：该 Agent 有多个场景，当前选择 {'群聊' if ct == 'group' else '私聊'}")
            if ct == 'group':
                if to_app_id:
                    print(f"   📎 包含 @{to_agent} 的 @ 提醒")
            if actual_sender:
                print(f"   👤 实际发送者：{actual_sender}（代理执行者：{from_agent}）")
            
            print(f"\n⚠️ --execute 模式仅生成指令，不会真正发送")
            print(f"📋 请使用 --deliver 并手动执行输出指令")
            print(f"\n📋 发送指令：")
            print(result.get('instruction', ''))
        else:
            return result
    else:
        # 预览模式
        return {
            'success': True,
            'to': to_agent,
            'chat_id': chat_id,
            'chat_type': ct,
            'msg_type': result.get('msg_type', 'text'),
            'from_agent': from_agent,
            'actual_sender': actual_sender,
            'to_app_id': to_app_id,
            'v3.8.0_hint': '使用 --deliver 获取完整发送指令，使用 --execute 直接执行'
        }
    
    return result


def main():
    args = sys.argv[1:]
    
    if len(args) < 2:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_send.py <目标Agent> <消息> [--from 发送者] [--chat-type p2p|group] [--actual-sender 实际发送者] [--deliver|--execute]',
            'v3.8.0': '支持批量发送：python3 feishu_send.py "Agent1,Agent2" "消息" --deliver',
            'v3.6.0': '推荐使用 --deliver 输出指令，或 --execute 直接执行'
        }, ensure_ascii=False))
        sys.exit(1)
    
    # 支持逗号分隔多个目标
    to_agents_str = args[0]
    message = args[1]
    
    # 解析多个目标
    to_agents = [agent.strip() for agent in to_agents_str.split(',') if agent.strip()]
    is_batch = len(to_agents) > 1
    
    from_agent = None
    chat_type_override = None
    deliver_mode = False
    execute_mode = False
    actual_sender = None
    
    i = 2
    while i < len(args):
        if args[i] == '--from' and i + 1 < len(args):
            from_agent = args[i + 1]
            i += 2
        elif args[i] == '--chat-type' and i + 1 < len(args):
            chat_type_override = args[i + 1]
            i += 2
        elif args[i] == '--deliver':
            deliver_mode = True
            i += 1
        elif args[i] == '--execute':
            execute_mode = True
            i += 1
        elif args[i] == '--actual-sender' and i + 1 < len(args):
            actual_sender = args[i + 1]
            i += 2
        else:
            i += 1
    
    # 自动检测当前 agent
    if not from_agent:
        from_agent = AgentConfig.detect_current_agent()
        if from_agent:
            print(f'📝 自动检测发送者：{from_agent}')
    
    # 获取发送者的 chat_id
    self_info = AgentConfig.get_self(from_agent) if from_agent else None
    my_chat_id = self_info.get('chat_id') if self_info else None
    
    if not from_agent or not my_chat_id:
        all_self = AgentConfig.get_all_self()
        hint = f'请设置 {from_agent or "当前 Agent"} 的发送者信息：'
        hint += f'\n   python3 feishu_set_self.py {from_agent or "Agent名"} oc_xxx'
        if all_self:
            hint += '\n\n已配置的 Agent：'
            for name, info in list(all_self.items())[:5]:
                cid = info.get('chat_id', '')[:20]
                hint += f'\n   • {name}: {cid}...'
        
        print(json.dumps({
            'success': False,
            'error': '缺少发送者信息',
            'hint': hint,
            'v3.8.0_help': '首次使用请运行：python3 feishu_set_self.py <你的Agent名> <你的chat_id>'
        }, ensure_ascii=False))
        sys.exit(1)
    
    # 批量发送
    if is_batch:
        print(f"\n📨 批量发送模式：{len(to_agents)} 个目标")
        print(f"目标列表: {', '.join(to_agents)}")
        print("=" * 50)
        
        success_count = 0
        failed_count = 0
        
        for i, to_agent in enumerate(to_agents, 1):
            print(f"\n[{i}/{len(to_agents)}] 发送给 {to_agent}...")
            result = send_to_agent(to_agent, message, from_agent, chat_type_override, actual_sender, deliver_mode, execute_mode)
            
            if result.get('success'):
                success_count += 1
            else:
                failed_count += 1
                print(f"❌ 发送给 {to_agent} 失败: {result.get('error', '未知错误')}")
        
        print("\n" + "=" * 50)
        print(f"📊 批量发送结果: ✅ {success_count} 成功 | ❌ {failed_count} 失败")
        
        if failed_count > 0:
            sys.exit(1)
    else:
        # 单个目标
        to_agent = to_agents[0]
        result = send_to_agent(to_agent, message, from_agent, chat_type_override, actual_sender, deliver_mode, execute_mode)
        
        if not result.get('success'):
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
        elif not deliver_mode and not execute_mode:
            # 预览模式
            print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
