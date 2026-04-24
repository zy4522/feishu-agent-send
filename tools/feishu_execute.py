#!/usr/bin/env python3
"""
feishu_execute.py - 直接执行飞书消息发送 v3.6.0

用法：
  python3 feishu_execute.py '<json格式的发送参数>'

示例：
  python3 feishu_execute.py '{"action":"send","receive_id_type":"chat_id","receive_id":"oc_xxx","msg_type":"post","content":"..."}'

注意：此工具需要 OpenClaw 环境支持，会生成执行日志
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
            'error': f'JSON解析错误: {str(e)}'
        }
    
    # 验证必要参数
    required = ['action', 'receive_id_type', 'receive_id', 'msg_type', 'content']
    missing = [r for r in required if r not in params]
    if missing:
        return {
            'success': False,
            'error': f'缺少必要参数: {missing}'
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
        'mode': 'execute',
        'instruction': instruction,
        'params': params,
        'log': log_entry,
        'note': '请复制上方指令到 OpenClaw 会话中执行'
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_execute.py \'<json参数>\''
        }, ensure_ascii=False))
        sys.exit(1)
    
    send_params_json = sys.argv[1]
    result = execute_feishu_send(send_params_json)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
