#!/usr/bin/env python3
"""
feishu_execute.py - 生成飞书消息发送指令 v3.8.0

用法：
  # 方式一：直接传 JSON（适合脚本调用）
  python3 feishu_execute.py '<json格式的发送参数>'
  
  # 方式二：交互式输入（适合手动使用）
  python3 feishu_execute.py --interactive
  
  # 方式三：从文件读取（适合批量发送）
  python3 feishu_execute.py --file /tmp/send_params.json

示例：
  python3 feishu_execute.py '{"action":"send","receive_id_type":"chat_id","receive_id":"oc_xxx","msg_type":"post","content":"..."}'

注意：本工具仅生成指令，不会真正发送！需要手动复制到 OpenClaw 会话执行
"""

import sys
import os
import json
import subprocess
from datetime import datetime

def execute_feishu_send(send_params_json):
    """
    执行飞书消息发送
    
    由于无法直接调用 feishu_im_user_message 工具，
    我们生成一个执行脚本并输出到控制台
    """
    try:
        params = json.loads(send_params_json)
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'JSON解析错误: {str(e)}',
            'hint': '请确保传入的是有效的 JSON 字符串'
        }
    
    # 验证必要参数
    required = ['action', 'receive_id_type', 'receive_id', 'msg_type', 'content']
    missing = [r for r in required if r not in params]
    if missing:
        return {
            'success': False,
            'error': f'缺少必要参数: {missing}',
            'hint': f'必要参数: {required}'
        }
    
    # 生成执行日志
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'params': params,
        'status': 'ready_to_execute'
    }
    
    # 生成 feishu_im_user_message 调用格式
    content_escaped = params['content'].replace("'", "'\"'\"'")
    
    instruction = f"""feishu_im_user_message(
    action='{params['action']}',
    receive_id_type='{params['receive_id_type']}',
    receive_id='{params['receive_id']}',
    msg_type='{params['msg_type']}',
    content='{content_escaped}'
)"""
    
    return {
        'success': True,
        'mode': 'instruction_generator',
        'instruction': instruction,
        'params': params,
        'log': log_entry,
        'note': '⚠️ 本工具仅生成指令，不会真正发送。请复制上方指令到 OpenClaw 会话中执行。'
    }


def interactive_mode():
    """交互式输入模式"""
    print("🚀 feishu_execute.py 交互式模式")
    print("-" * 50)
    print("请输入发送参数（JSON格式），或按 Ctrl+C 退出:")
    print("示例: '{\"action\":\"send\",\"receive_id_type\":\"chat_id\",\"receive_id\":\"oc_xxx\",\"msg_type\":\"text\",\"content\":\"{\\\"text\\\":\\\"你好\\\"}\"}'")
    print()
    
    try:
        user_input = input("> ")
        result = execute_feishu_send(user_input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except KeyboardInterrupt:
        print("\n👋 已退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)


def file_mode(file_path):
    """从文件读取模式"""
    if not os.path.exists(file_path):
        return {
            'success': False,
            'error': f'找不到文件: {file_path}'
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试解析为 JSON
        try:
            params = json.loads(content)
            # 如果是单个对象，直接执行
            if isinstance(params, dict):
                return execute_feishu_send(content)
            # 如果是数组，批量执行
            elif isinstance(params, list):
                results = []
                for i, item in enumerate(params):
                    print(f"\n📨 执行第 {i+1}/{len(params)} 条消息...")
                    result = execute_feishu_send(json.dumps(item, ensure_ascii=False))
                    results.append(result)
                return {
                    'success': True,
                    'mode': 'batch',
                    'total': len(params),
                    'results': results
                }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': '文件内容不是有效的 JSON'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'读取文件失败: {str(e)}'
        }


def main():
    args = sys.argv[1:]
    
    if len(args) < 1:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_execute.py [选项]',
            'options': {
                '<json>': '直接传入 JSON 参数',
                '--interactive': '交互式输入模式',
                '--file <path>': '从文件读取参数（支持批量）'
            },
            'examples': [
                'python3 feishu_execute.py \'{...}\'',
                'python3 feishu_execute.py --interactive',
                'python3 feishu_execute.py --file /tmp/send.json'
            ]
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    if args[0] == '--interactive':
        interactive_mode()
    elif args[0] == '--file' and len(args) >= 2:
        result = file_mode(args[1])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 直接传入 JSON
        send_params_json = args[0]
        result = execute_feishu_send(send_params_json)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
