#!/usr/bin/env python3
"""
feishu_agent_send 命令行工具
简化在群里使用 feishu_agent_send 的流程

使用方法:
  python3 send_message.py --to "大总管" --message "内容" --from "我"
  python3 send_message.py --to "大总管" --message "内容" --from "我" --group
  python3 send_message.py --list-targets
"""

import sys
import argparse

# 添加skill目录到路径
sys.path.insert(0, '/root/.openclaw/workspace/skills/feishu_agent_send')

try:
    from feishu_agent_send import feishu_agent_send, feishu_agent_send_and_deliver, list_known_agents
except ImportError as e:
    print(f"❌ 错误: 无法导入 feishu_agent_send: {e}")
    print("请确保 skill 已正确安装到 /root/.openclaw/workspace/skills/feishu_agent_send/")
    sys.exit(1)


def list_targets():
    """列出所有可发送的目标"""
    print("📋 可发送目标列表：")
    print("-" * 50)
    agents = list_known_agents()
    for name in agents:
        print(f"  • {name}")
    print("-" * 50)
    print(f"\n💡 群聊 chat_id: oc_9d8e4a53e3f558d3457dad06f1e0a275")
    print(f"💡 使用 --group 参数获取群聊发送参数")


def format_message(to, message, from_agent, force_group=False):
    """
    格式化消息并输出发送参数
    
    Args:
        to: 接收方名称
        message: 消息内容
        from_agent: 发送方名称
        force_group: 强制使用群聊chat_id
    """
    # 格式化消息
    result = feishu_agent_send(
        to=to,
        message=message,
        from_agent=from_agent
    )
    
    if not result['success']:
        print(f"❌ 格式化失败: {result.get('error', '未知错误')}")
        return False
    
    # 确定chat_id
    if force_group:
        chat_id = "oc_9d8e4a53e3f558d3457dad06f1e0a275"
        chat_type = "群聊（强制）"
    else:
        chat_id = result.get('chat_id', '未知')
        chat_type = result.get('chat_type', '未知')
    
    print("✅ 消息格式化成功！")
    print("-" * 50)
    print(f"📨 格式化消息：")
    print(result['formatted_message'])
    print("-" * 50)
    print(f"\n📤 发送参数：")
    print(f"   receive_id_type: chat_id")
    print(f"   receive_id: {chat_id} ({chat_type})")
    print(f"   msg_type: text")
    print(f"\n💡 Python代码：")
    print("-" * 50)
    escaped_message = result['formatted_message'].replace('\n', '\\n').replace("'", "\\'")
    print(f"""feishu_im_user_message(
    action="send",
    receive_id_type="chat_id",
    receive_id="{chat_id}",
    msg_type="text",
    content='{{"text": "{escaped_message}"}}'
)""")
    print("-" * 50)
    
    if not force_group and chat_type == "私聊":
        print(f"\n⚠️  警告：当前chat_id是私聊，如需发送到群聊，请使用 --group 参数")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='feishu_agent_send 命令行工具 - 简化Agent群聊通信',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚨 重要提示：在群里与其他Agent通信时，必须使用 feishu_agent_send！

示例:
  # 列出所有可发送目标
  python3 send_message.py --list-targets
  
  # 格式化消息（自动查找chat_id）
  python3 send_message.py --to "大总管" --message "你好" --from "我"
  
  # 强制使用群聊chat_id（推荐）
  python3 send_message.py --to "大总管" --message "你好" --from "我" --group

提示:
  • 此工具只提供消息格式化和参数输出
  • 实际发送需要使用 feishu_im_user_message 工具
  • 使用 --group 确保消息发到群里而不是私信
        """
    )
    
    parser.add_argument('--to', '-t', help='接收方名称（如：大总管）')
    parser.add_argument('--message', '-m', help='消息内容')
    parser.add_argument('--from-agent', '-f', help='发送方名称（如：软件开发组长）')
    parser.add_argument('--group', '-g', action='store_true', 
                        help='强制使用群聊chat_id（推荐在群里使用）')
    parser.add_argument('--list-targets', '-l', action='store_true',
                        help='列出所有可发送的目标')
    
    args = parser.parse_args()
    
    # 列出目标
    if args.list_targets:
        list_targets()
        return
    
    # 验证必需参数
    if not args.to or not args.message or not args.from_agent:
        print("❌ 错误: 缺少必需参数")
        print("\n使用示例:")
        print(f'  python3 send_message.py --to "大总管" --message "你好" --from "我" --group')
        print(f"\n或者查看帮助:")
        print(f"  python3 send_message.py --help")
        sys.exit(1)
    
    # 格式化消息
    success = format_message(
        to=args.to,
        message=args.message,
        from_agent=args.from_agent,
        force_group=args.group
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
