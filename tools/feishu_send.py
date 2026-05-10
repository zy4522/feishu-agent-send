#!/usr/bin/env python3
"""
feishu_send.py - 发送消息给飞书 Agent v3.10.3

⚠️ 【铁律】所有Agent之间通信必须使用标准代理格式，本工具已强制自动生成，无需手动编写

v3.10.3 (2026-05-10):
  - 群聊 post 消息去掉冗余 title，消息更简洁
  - 新增 get_group_info_by_chat_id() 根据 chat_id 反查群信息
  - parse_agent_message() 优先从 at 标签提取目标 Agent
  - 支持 chat_id 参数自动识别群聊上下文

v3.10.2 (2026-05-10):
  - 统一 --execute 与 --deliver 消息格式（gcz审查P0）
  - --execute 现在使用 feishu_agent_send_and_deliver 生成的格式
  - 群聊统一使用 post 富文本（含@标签）
  - from_chat_id 统一使用发送者自己的 chat_id

v3.10.1 (2026-05-10):
  - 修复 from_chat_id 硬编码问题（gcz审查P0）
  - 版本号统一从 _version.py 引用

v3.10.0 (2026-05-04):
  - ✅ 强制自动生成标准代理格式，从技术层面杜绝忘记格式的问题
  - 集成幂等性重试机制，彻底解决重复发送问题
  - 支持指数退避重试，网络波动时自动恢复
  - 重复消息自动拦截，避免打扰用户

v3.9.2 (2026-05-01):
  - 修复 _refresh_token 兼容飞书 API v2 扁平格式
  - 修复 _decrypt_token/_save_token 硬编码 userOpenId 问题
  - 5个Agent需重新授权：main/cpaas/iio/ayy/gcz

v3.9.1 (2026-04-27):
  - 修复私聊发送bug：统一使用chat_id，避免open_id cross app错误

用法：
  python3 feishu_send.py <目标Agent> <消息内容> [选项]
  python3 feishu_send.py "Agent1,Agent2,Agent3" <消息内容> [选项]  # 批量发送

选项：
  --from            发送者名称（自动检测，单配置时可选）
  --chat-type       p2p 或 group，强制指定类型
  --actual-sender   实际发送者（人类身份，与AI代理区分）
  --execute         直接执行发送（默认模式）
  --no-retry        禁用自动重试机制

示例：
  # 单个目标
  python3 feishu_send.py ying "你好" --execute
  
  # 批量发送（逗号分隔多个目标）
  python3 feishu_send.py "kfj,ying,zz" "会议通知" --chat-type group --execute
  
  # 代理发送（人类经由AI发送）
  python3 feishu_send.py kfj "消息" --from kfj --actual-sender kclaw --execute
"""

import sys
import os
import json
import time

# 导入版本号
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _version import __version__

# 导入重试机制
sys.path.insert(0, os.path.expanduser('~/.openclaw/tools'))
from retry_mechanism import retry_with_backoff, is_already_sent, get_request_id

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig, feishu_agent_send_and_deliver, list_known_agents
from feishu_direct_send import get_valid_token, send_message as direct_api_send


def send_to_agent(to_agent, message, from_agent, chat_type_override, actual_sender, execute_mode, chat_id_override=None):
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
            'v3.10.3_help': '新增：群聊消息去title、chat_id反查群信息、at标签优先解析',
            'v3.10.2_help': f'请先添加：python3 feishu_add.py {to_agent} oc_xxx'
        }
    
    chat_id = chat_id_override or agent_info.get('chat_id')
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
    
    # 获取目标 Agent 的 open_id（群聊 @ 用）
    to_open_id = AgentConfig.get_agent_open_id(to_agent) if ct == 'group' else None
    
    # 调用 feishu_agent_send_and_deliver（统一格式）
    result = feishu_agent_send_and_deliver(to_agent, message, from_agent, chat_type_override, actual_sender)
    
    if execute_mode:
        if result.get('success'):
            print(f"\n✅ 消息已准备好，发送给 {to_agent}（{'群聊' if ct == 'group' else '私聊'}）")
            if multi_scene:
                print(f"   注意：该 Agent 有多个场景，当前选择 {'群聊' if ct == 'group' else '私聊'}")
            if ct == 'group':
                if to_open_id:
                    print(f"   📎 包含 @{to_agent} 的 @ 提醒")
            if actual_sender:
                print(f"   👤 实际发送者：{actual_sender}（代理执行者：{from_agent}）")
            
            # 🚀 直接调飞书 API
            print(f"\n🚀 正在直接调用飞书 API 发送消息...")
            
            access_token = get_valid_token(from_agent)
            if not access_token:
                print(f"\n❌ 无法获取有效的 Access Token")
                print(f"   请在飞书中重新授权该 Agent")
                return result
            
            # v3.10.2: 统一使用 feishu_agent_send_and_deliver 生成的格式
            # 从 send_params 中获取 content 和 msg_type
            send_params = result.get('send_params', {})
            content = send_params.get('content', '')
            msg_type = send_params.get('msg_type', 'text')
            
            # v3.10.3: 如果指定了 chat_id_override，覆盖目标 chat_id
            if chat_id_override:
                receive_id = chat_id_override
            else:
                receive_id = chat_id
            
            # P1: 群聊消息路由检查 - 检查from_agent和to_agent的群ID是否一致
            if ct == 'group' and not chat_id_override:
                from_group_id = AgentConfig.get_agent_group_chat_id(from_agent)
                to_group_id = AgentConfig.get_agent_group_chat_id(to_agent)
                if from_group_id and to_group_id and from_group_id != to_group_id:
                    print(f"⚠️ 群聊路由警告: from_agent({from_agent})的群ID({from_group_id})与to_agent({to_agent})的群ID({to_group_id})不一致")
                    print(f"   消息将发送到to_agent配置的群: {to_group_id}")
                    print(f"   如需发送到其他群，请使用 --chat-id 参数指定")
            
            # Bug修复: post消息的content是dict，需要转为JSON字符串
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            elif not isinstance(content, str):
                # P2: 更严格的content类型检查
                return {
                    'success': False,
                    'error': f'content类型错误: {type(content).__name__}，必须是dict或str',
                    'hint': '请检查feishu_agent_send_and_deliver返回的content格式'
                }
            
            # P2: 验证content是否为有效的JSON字符串（post类型时）
            if msg_type == 'post':
                try:
                    parsed = json.loads(content)
                    if not isinstance(parsed, dict) or 'zh_cn' not in parsed:
                        return {
                            'success': False,
                            'error': 'post消息content格式错误：缺少zh_cn字段',
                            'hint': '请检查build_post_content返回的格式'
                        }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'post消息content不是有效的JSON字符串',
                        'hint': 'content必须是JSON字符串格式'
                    }
            
            receive_id_type = 'chat_id'
            
            # 构建发送参数，用于幂等性检测
            send_payload = {
                'from_agent': from_agent,
                'to_agent': to_agent,
                'receive_id_type': receive_id_type,
                'receive_id': receive_id,
                'msg_type': msg_type,
                'content': content,
                'timestamp': int(time.time())  # 加入时间戳避免相同内容重复被拦截
            }
            
            # 幂等性检查：如果已经发送过，直接跳过
            request_id = get_request_id(send_payload)
            if is_already_sent(request_id):
                print(f"⚠️ 检测到重复发送请求，已自动拦截（请求ID: {request_id[:8]}）")
                print(f"   若确实需要重发，请修改消息内容后再试")
                return {'success': True, 'api_result': {'status': 'duplicate', 'request_id': request_id}}
            
            # 定义发送函数，用于重试机制
            def _send():
                return direct_api_send(
                    access_token=access_token,
                    receive_id_type=receive_id_type,
                    receive_id=receive_id,
                    msg_type=msg_type,
                    content=content,
                )
            
            # 使用带指数退避的重试机制发送
            api_result = retry_with_backoff(
                _send,
                send_payload,
                max_retries=3,  # 最多重试3次
                initial_delay=1  # 初始间隔1秒
            )
            
            if api_result is None:
                print(f"❌ 所有重试均失败，消息未发送")
                return {'success': False, 'api_result': {'error': 'all retries failed'}}
            elif api_result.get('success'):
                print(f"✅ 消息发送成功！")
                print(f"   消息ID: {api_result.get('message_id')}")
                print(f"   目标: {to_agent} ({receive_id})")
                print(f"   时间: {api_result.get('create_time', '')}")
                return {'success': True, 'api_result': api_result}
            else:
                print(f"❌ 发送失败: {api_result.get('error')}")
                return {'success': False, 'api_result': api_result}
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
            'to_open_id': to_open_id,
            'v3.10.2_hint': '使用 --execute 直接执行发送'
        }
    
    return result


def main():
    args = sys.argv[1:]
    
    if len(args) < 2:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_send.py <目标Agent> <消息> [--from 发送者] [--chat-type p2p|group] [--chat-id oc_xxx] [--actual-sender 实际发送者] [--execute] [--no-retry]',
            'v3.10.3': '新增：群聊消息去title、chat_id反查群信息、at标签优先解析',
            'v3.10.2': '统一--execute与--deliver消息格式',
            'v3.10.0': '新增幂等性重试机制，自动拦截重复消息',
            'v3.9.0': '支持批量发送：python3 feishu_send.py "Agent1,Agent2" "消息" --execute'
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
    chat_id_override = None
    execute_mode = True  # v3.10.2: 默认执行模式
    actual_sender = None
    
    i = 2
    while i < len(args):
        if args[i] == '--from' and i + 1 < len(args):
            from_agent = args[i + 1]
            i += 2
        elif args[i] == '--chat-type' and i + 1 < len(args):
            chat_type_override = args[i + 1]
            i += 2
        elif args[i] == '--chat-id' and i + 1 < len(args):
            chat_id_override = args[i + 1]
            i += 2
        elif args[i] == '--deliver':
            print("⚠️ --deliver 已废弃，自动切换为 --execute")
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
            'v3.10.3_help': '新增：群聊消息去title、chat_id反查群信息、at标签优先解析',
            'v3.10.2_help': '首次使用请运行：python3 feishu_set_self.py <你的Agent名> <你的chat_id>'
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
            result = send_to_agent(to_agent, message, from_agent, chat_type_override, actual_sender, execute_mode, chat_id_override)
            
            if result.get('success') and result.get('api_result', {}).get('success'):
                success_count += 1
                print(f"   ✅ 成功")
            else:
                failed_count += 1
                error = result.get('error') or result.get('api_result', {}).get('error', '未知错误')
                print(f"   ❌ 失败: {error}")
        
        print("\n" + "=" * 50)
        print(f"📊 批量发送完成：成功 {success_count}，失败 {failed_count}")
        return
    
    # 单个发送
    result = send_to_agent(to_agents[0], message, from_agent, chat_type_override, actual_sender, execute_mode, chat_id_override)
    
    if not result.get('success'):
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 如果是预览模式，输出详细信息
    if not execute_mode:
        print(json.dumps({
            'success': True,
            'preview': {
                'to': result.get('to'),
                'chat_type': result.get('chat_type'),
                'msg_type': result.get('msg_type'),
                'from_agent': result.get('from_agent'),
                'actual_sender': result.get('actual_sender'),
            },
            'hint': '使用 --execute 直接执行发送'
        }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
