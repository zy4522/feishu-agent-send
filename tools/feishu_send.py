#!/usr/bin/env python3
"""
feishu_send.py - 发送消息给飞书 Agent v3.6.0

用法：
  python3 feishu_send.py <目标Agent> <消息内容> [选项]

选项：
  --from            发送者名称（自动检测）
  --chat-type       p2p 或 group，强制指定类型
  --deliver         输出调用指令（推荐）

示例：
  # 预览模式（输出 JSON，不调用发送）
  python3 feishu_send.py ying "你好"
  
  # 一站式发送（输出 feishu_im_user_message 调用指令）
  python3 feishu_send.py ying "你好" --deliver
"""

import sys
import os
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig, feishu_agent_send_and_deliver, list_known_agents


def main():
    args = sys.argv[1:]
    
    if len(args) < 2:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_send.py <目标Agent> <消息> [--from 发送者] [--chat-type p2p|group] [--deliver]',
            'v3.6.0': '推荐使用 --deliver 一站式发送'
        }, ensure_ascii=False))
        sys.exit(1)
    
    to_agent = args[0]
    message = args[1]
    
    from_agent = None
    chat_type_override = None
    deliver_mode = False
    
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
            'v3.6.0_help': '首次使用请运行：python3 feishu_set_self.py <你的Agent名> <你的chat_id>'
        }, ensure_ascii=False))
        sys.exit(1)
    
    # 获取目标 Agent 信息
    agent_info = AgentConfig.get_agent_info(to_agent, chat_type_override)
    if not agent_info:
        agent_info = AgentConfig.get_agent_info(to_agent)
    
    if not agent_info:
        all_agents = list_known_agents()
        print(json.dumps({
            'success': False,
            'error': f"找不到 Agent '{to_agent}'",
            'available_agents': all_agents[:10],
            'v3.6.0_help': f'请先添加：python3 feishu_add.py {to_agent} oc_xxx'
        }, ensure_ascii=False))
        sys.exit(1)
    
    chat_id = agent_info.get('chat_id')
    # Bug 修复：验证 chat_type 只能是 p2p 或 group
    valid_chat_types = ['p2p', 'group']
    if chat_type_override and chat_type_override not in valid_chat_types:
        print(json.dumps({
            'success': False,
            'error': f"无效的 chat_type: '{chat_type_override}'",
            'valid_options': valid_chat_types,
            'hint': '请使用 --chat-type p2p 或 --chat-type group'
        }, ensure_ascii=False))
        sys.exit(1)
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
    
    if ct == 'group' and to_app_id:
        # 群聊：使用 post 富文本格式
        from feishu_agent_send import build_post_content
        content_obj = build_post_content(message, from_agent, to_agent, to_app_id)
        content = json.dumps(content_obj, ensure_ascii=False)
        msg_type = 'post'
        preview = content
    else:
        # 私聊：使用 text 纯文本格式（v3.6.0: JSON 元数据）
        type_label = '私信'
        
        # JSON 元数据块
        metadata = {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'from_chat_id': my_chat_id,
            'chat_type': 'p2p',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '3.6.0'
        }
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        formatted = (
            f'📨【{type_label}】【代理】【{from_agent}→{to_agent}】\n\n'
            f'{message}\n\n'
            f'---\n'
            f'实际发送者：{from_agent}\n'
            f'代理发送者：用户\n'
            f'元数据：{metadata_json}\n'
            f'---'
        )
        content = json.dumps({'text': formatted}, ensure_ascii=False)
        msg_type = 'text'
        preview = formatted
    
    send_params = {
        'action': 'send',
        'receive_id_type': 'chat_id',
        'receive_id': chat_id,
        'msg_type': msg_type,
        'content': content
    }
    
    if deliver_mode:
        # v3.6.0: 一站式发送 - 调用 feishu_agent_send_and_deliver
        result = feishu_agent_send_and_deliver(to_agent, message, from_agent, chat_type_override)
        if result.get('success'):
            print(f"\n✅ 消息已准备好，发送给 {to_agent}（{'群聊' if ct == 'group' else '私聊'}）")
            if multi_scene:
                print(f"   注意：该 Agent 有多个场景，当前选择 {'群聊' if ct == 'group' else '私聊'}")
            if ct == 'group':
                if to_app_id:
                    print(f"   📎 包含 @{to_agent} 的 @ 提醒")
            print(f"\n📋 {result.get('instruction', '')}")
        else:
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)
    else:
        # 预览模式
        result = {
            'success': True,
            'send_params': send_params,
            'preview': preview,
            'chat_id': chat_id,
            'chat_type': ct,
            'msg_type': msg_type,
            'to': to_agent,
            'from_agent': from_agent,
            'to_app_id': to_app_id,
            'v3.6.0_hint': '使用 --deliver 获取完整发送指令'
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
