#!/usr/bin/env python3
"""
feishu_scan_group.py - 扫描群成员，自动采集 Agent 的 app_id

用法：
  python3 feishu_scan_group.py <群chat_id>

流程：
  1. 调用 feishu_chat_members 获取群成员列表
  2. 识别已配置的 Agent（匹配名称）
  3. 提取 app_id 并存入 config.json

示例：
  python3 feishu_scan_group.py oc_0a2add62314f45768b5c4732df855391
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig, list_known_agents


def main():
    args = sys.argv[1:]
    
    if len(args) < 1:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_scan_group.py <群chat_id>',
            'example': 'python3 feishu_scan_group.py oc_xxx'
        }, ensure_ascii=False))
        sys.exit(1)
    
    chat_id = args[0]
    
    # 获取已配置的 Agent 列表
    known_agents = list_known_agents()
    if not known_agents:
        print(json.dumps({
            'success': False,
            'error': '没有已配置的 Agent',
            'hint': '请先使用 feishu_add.py 添加 Agent 配置'
        }, ensure_ascii=False))
        sys.exit(1)
    
    print(f"🔍 开始扫描群 {chat_id} 的成员信息...")
    print(f"   已配置 Agent: {', '.join(known_agents)}")
    print()
    
    # 输出 feishu_chat_members 调用指令（供用户执行）
    print("📋 请执行以下命令获取群成员列表：")
    print()
    print(f"feishu_chat_members(")
    print(f"    chat_id='{chat_id}',")
    print(f"    page_size=200")
    print(f")")
    print()
    print("然后将返回结果保存到 /tmp/group_members.json，再运行：")
    print(f"python3 feishu_scan_group.py {chat_id} --import /tmp/group_members.json")
    print()
    
    # 检查是否有导入文件
    if len(args) >= 3 and args[1] == '--import':
        import_path = args[2]
        if not os.path.exists(import_path):
            print(json.dumps({
                'success': False,
                'error': f'找不到导入文件: {import_path}'
            }, ensure_ascii=False))
            sys.exit(1)
        
        with open(import_path, 'r', encoding='utf-8') as f:
            members_data = json.load(f)
        
        # 解析成员列表
        members = members_data.get('members', [])
        if not members:
            # 尝试其他可能的字段名
            members = members_data.get('data', {}).get('members', [])
        
        if not members:
            print(json.dumps({
                'success': False,
                'error': '无法解析群成员数据',
                'hint': '请确认 JSON 格式正确'
            }, ensure_ascii=False))
            sys.exit(1)
        
        print(f"✅ 成功导入 {len(members)} 个群成员")
        print()
        
        # 匹配 Agent 并提取 app_id
        matched = []
        unmatched = []
        
        for member in members:
            member_id = member.get('member_id', '')
            name = member.get('name', '')
            
            # 只处理机器人（app_id 格式为 cli_xxx）
            if not member_id.startswith('cli_'):
                continue
            
            # 尝试匹配已配置的 Agent（支持多对一映射）
            matched_agent = None
            name_lower = name.lower()
            
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
            
            # 先尝试配置文件映射
            matched_agent = None
            name_lower = name.lower()
            
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
                # 保存 app_id 到配置
                AgentConfig.set_agent_app_id(matched_agent, member_id, 'group')
                matched.append({
                    'agent': matched_agent,
                    'app_id': member_id,
                    'name': name
                })
            else:
                unmatched.append({
                    'app_id': member_id,
                    'name': name
                })
        
        # 输出结果
        print("=" * 50)
        print("📊 扫描结果")
        print("=" * 50)
        
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
        print(f"\n📝 后续群聊发送时将自动使用 post 消息类型并 @{matched_agent}")
        
    else:
        # 显示帮助信息
        print("💡 提示：")
        print("   1. 先在群里 @ 各 Agent 发一条消息（确保机器人在群里）")
        print("   2. 执行上面的 feishu_chat_members 命令获取成员列表")
        print("   3. 保存结果后使用 --import 参数导入")
        print()


if __name__ == '__main__':
    main()
