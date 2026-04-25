#!/usr/bin/env python3
"""
feishu_scan_group.py - 全自动扫描群消息历史，采集 Agent 的 app_id v3.9.0

用法：
  python3 feishu_scan_group.py <群chat_id>

流程：
  1. 调用 feishu_im_user_get_messages 获取群消息历史
  2. 筛选机器人消息（sender_id.id_type == 'app_id'）
  3. 提取 app_id 和名称，与已知 Agent 匹配
  4. 自动保存到 config.json

示例：
  python3 feishu_scan_group.py oc_0a2add62314f45768b5c4732df855391
"""

import sys
import os
import json
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig, list_known_agents


def get_chat_messages(chat_id, limit=100):
    """获取群消息历史，适配 OpenClaw 环境"""
    # 方式1：直接导入工具（如果在 OpenClaw 环境中）
    try:
        # 尝试通过 OpenClaw 工具调用
        import openclaw
        # 使用 feishu_im_user_get_messages 工具
        result = openclaw.tools.feishu_im_user_get_messages(
            chat_id=chat_id,
            page_size=limit,
            relative_time='last_7_days'
        )
        return result.get('messages', [])
    except (ImportError, AttributeError):
        pass
    
    # 方式2：子进程调用 openclaw CLI
    try:
        cmd = [
            'openclaw', 'run', 'feishu_im_user_get_messages',
            '--chat_id', chat_id,
            '--page_size', str(limit),
            '--relative_time', 'last_7_days'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('messages', [])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        pass
    
    # 方式3：提示用户手动执行
    return None


def extract_bots_from_messages(messages):
    """从消息中提取机器人 sender"""
    bots = {}
    for msg in messages:
        sender = msg.get('sender', {})
        
        # 只处理机器人消息（sender_type == 'app'）
        if sender.get('sender_type') == 'app':
            app_id = sender.get('id', '')
            name = sender.get('name', 'Unknown')
            if app_id and app_id.startswith('cli_'):
                bots[app_id] = name
    
    return bots


def match_agents(bots, known_agents):
    """匹配机器人与已知 Agent"""
    matched = []
    unmatched = []
    
    # 从配置文件读取名称映射规则
    config = AgentConfig.load()
    name_mappings = config.get('name_mappings', {})
    
    # 如果没有配置，使用默认映射
    if not name_mappings:
        name_mappings = {
            'ying': ['颖', 'ying'],
            'main': ['大总管', 'main'],
            'iio': ['信息官', 'iio'],
            'kfj': ['开发机', 'kfj'],
            'zz': ['组长', 'zz'],
            'ayy': ['啊呀呀', 'ayy'],
            'cpaas': ['cpa', 'cpaas', '学助'],
        }
    
    for app_id, name in bots.items():
        name_lower = name.lower()
        matched_agent = None
        
        # 先尝试配置文件映射
        for agent_name, aliases in name_mappings.items():
            for alias in aliases:
                if alias.lower() in name_lower:
                    matched_agent = agent_name
                    break
            if matched_agent:
                break
        
        # 再尝试模糊匹配
        if not matched_agent:
            for agent_name in known_agents:
                if agent_name.lower() in name_lower or name_lower in agent_name.lower():
                    matched_agent = agent_name
                    break
        
        if matched_agent:
            matched.append({
                'agent': matched_agent,
                'app_id': app_id,
                'name': name
            })
        else:
            unmatched.append({
                'app_id': app_id,
                'name': name
            })
    
    return matched, unmatched


def scan_from_history(chat_id):
    """全自动扫描：从消息历史 → 提取机器人 → 匹配 Agent → 保存配置"""
    known_agents = list_known_agents()
    
    if not known_agents:
        return {
            'success': False,
            'error': '没有已配置的 Agent',
            'hint': '请先使用 feishu_add.py 添加 Agent 配置'
        }
    
    # 获取群消息历史
    messages = get_chat_messages(chat_id)
    
    if messages is None:
        # 无法自动获取，提示手动方式
        return {
            'success': False,
            'error': '无法自动获取群消息历史',
            'manual_mode': True,
            'hint': '请手动执行以下命令获取消息历史，然后保存到 /tmp/chat_messages.json：',
            'instruction': f"""
feishu_im_user_get_messages(
    chat_id='{chat_id}',
    page_size=100,
    relative_time='last_7_days'
)

然后运行：
python3 feishu_scan_group.py {chat_id} --manual /tmp/chat_messages.json
"""
        }
    
    if not messages:
        return {
            'success': False,
            'error': '群消息历史为空',
            'hint': '请先在群里 @ 各 Agent 发一条消息，确保机器人在群里有发言记录'
        }
    
    # 提取机器人
    bots = extract_bots_from_messages(messages)
    
    if not bots:
        return {
            'success': False,
            'error': '未发现任何机器人消息',
            'hint': '请先在群里 @ 各 Agent 发一条消息，确保机器人在群里有发言记录'
        }
    
    # 匹配 Agent
    matched, unmatched = match_agents(bots, known_agents)
    
    # 保存配置
    for item in matched:
        AgentConfig.set_agent_app_id(item['agent'], item['app_id'], 'group')
    
    return {
        'success': True,
        'total_messages': len(messages),
        'total_bots': len(bots),
        'matched': matched,
        'unmatched': unmatched
    }


def main():
    args = sys.argv[1:]
    
    if len(args) < 1:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_scan_group.py <群chat_id> [--auto]',
            'example': 'python3 feishu_scan_group.py oc_xxx',
            'modes': {
                'auto': '全自动模式（默认）：自动调用API获取消息历史',
                'manual': '手动模式：从已保存的JSON文件导入消息'
            }
        }, ensure_ascii=False))
        sys.exit(1)
    
    chat_id = args[0]
    
    print(f"🔍 开始扫描群 {chat_id} 的消息历史...")
    print(f"   模式: 自动检测（--auto 参数已废弃，默认即为自动模式）")
    print()
    
    # 检查是否有手动导入模式
    if len(args) >= 3 and args[1] == '--manual':
        import_path = args[2]
        if not os.path.exists(import_path):
            print(json.dumps({
                'success': False,
                'error': f'找不到导入文件: {import_path}'
            }, ensure_ascii=False))
            sys.exit(1)
        
        with open(import_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = data.get('messages', [])
        if not messages:
            messages = data.get('items', [])
        
        print(f"✅ 成功导入 {len(messages)} 条消息")
        
        bots = extract_bots_from_messages(messages)
        known_agents = list_known_agents()
        matched, unmatched = match_agents(bots, known_agents)
        
        for item in matched:
            AgentConfig.set_agent_app_id(item['agent'], item['app_id'], 'group')
        
        result = {
            'success': True,
            'mode': 'manual',
            'total_bots': len(bots),
            'matched': matched,
            'unmatched': unmatched
        }
    else:
        # 全自动模式（默认）
        result = scan_from_history(chat_id)
    
    # 输出结果
    if result.get('success'):
        print("=" * 50)
        print("📊 扫描结果")
        print("=" * 50)
        
        if result.get('total_messages'):
            print(f"\n📨 分析了 {result['total_messages']} 条消息")
        print(f"🤖 发现 {result['total_bots']} 个机器人")
        
        matched = result.get('matched', [])
        unmatched = result.get('unmatched', [])
        
        if matched:
            print(f"\n✅ 成功匹配 {len(matched)} 个 Agent：")
            for item in matched:
                print(f"   • {item['agent']}: app_id={item['app_id']}, 名称={item['name']}")
        
        if unmatched:
            print(f"\n⚠️ 未匹配的机器人（{len(unmatched)} 个）：")
            for item in unmatched:
                print(f"   • app_id={item['app_id']}, 名称={item['name']}")
            print(f"\n   如需添加，请使用：")
            print(f"   python3 feishu_add.py <Agent名> {chat_id} --chat-type group")
        
        print(f"\n💾 配置已自动保存到 {AgentConfig._config_path()}")
        print(f"\n📝 后续群聊发送时将自动使用 post 消息类型并 @Agent")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == '__main__':
    main()
