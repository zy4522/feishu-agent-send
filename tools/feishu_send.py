#!/usr/bin/env python3
"""
feishu_send.py - 发送消息给飞书 Agent v3.1.0

用法：
  python3 feishu_send.py <目标Agent> <消息内容> [选项]

选项：
  --from            发送者名称（自动检测）
  --chat-type       p2p 或 group，强制指定类型
  --deliver         一站式发送（输出调用指令）

示例：
  # 预览模式
  python3 feishu_send.py 颖小兔 "你好"
  
  # 一站式发送（推荐）
  python3 feishu_send.py 颖小兔 "你好" --deliver
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import (
    AgentConfig,
    feishu_agent_send,
    feishu_agent_send_and_deliver,
    list_known_agents
)


def main():
    args = sys.argv[1:]
    
    if len(args) < 2:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_send.py <目标Agent> <消息> [--from 发送者] [--chat-type p2p|group] [--deliver]',
            'v3.1.0': '推荐使用 --deliver 一站式发送'
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
            'v3.1.0_help': '首次使用请运行：python3 feishu_set_self.py <你的Agent名> <你的chat_id>'
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
            'v3.1.0_help': f'请先添加：python3 feishu_add.py {to_agent} oc_xxx'
        }, ensure_ascii=False))
        sys.exit(1)
    
    chat_id = agent_info.get('chat_id')
    # 验证 chat_type
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
    scene_hint = None
    if isinstance(agent_config, dict) and ('p2p' in agent_config or 'group' in agent_config):
        available = [k for k in ['p2p', 'group'] if k in agent_config]
        if len(available) > 1 and not chat_type_override:
            multi_scene = True
            chosen = '私聊' if chat_type == 'p2p' else '群聊'
            scene_hint = (
                f"Agent '{to_agent}' 有多个配置：私聊、群聊。"
                f"已自动选择：{chosen}。"
                f"如需切换，请使用：--chat-type {'group' if chat_type == 'p2p' else 'p2p'}"
            )
    
    type_label = '私信' if chat_type == 'p2p' else '群'
    
    if deliver_mode:
        # v3.1.0: 使用 feishu_agent_send_and_deliver 统一处理
        result = feishu_agent_send_and_deliver(to_agent, message, from_agent, chat_type_override)
        if result.get('success'):
            # 追加多场景提示到结果
            if multi_scene:
                result['scene_hint'] = scene_hint
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)
    else:
        # 预览模式
        result = feishu_agent_send(to_agent, message, from_agent, chat_type_override)
        if result.get('success'):
            # 构造预览输出（兼容旧格式）
            output = {
                'success': True,
                'send_params': {
                    'action': 'send',
                    'receive_id_type': 'chat_id',
                    'receive_id': result['chat_id'],
                    'msg_type': 'text',
                    'content': json.dumps({'text': result['formatted_message']}, ensure_ascii=False)
                },
                'preview': result['formatted_message'],
                'chat_id': result['chat_id'],
                'chat_type': result['chat_type'],
                'to': to_agent,
                'from_agent': from_agent,
                'v3.1.0_hint': '使用 --deliver 获取完整发送指令'
            }
            if multi_scene:
                output['scene_hint'] = scene_hint
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(1)


if __name__ == '__main__':
    main()
