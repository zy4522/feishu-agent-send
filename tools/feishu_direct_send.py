#!/usr/bin/env python3
"""
feishu_direct_send.py - 直接通过飞书 API 发送消息 v3.9.0

一站式发送工具：解密本地 UAT → 自动续期 → 直接调用飞书 IM API 发送消息
无需依赖 OpenClaw 会话，脚本独立完成全部发送流程。

用法：
  # 从 feishu_send.py 调用（推荐）
  python3 feishu_send.py kfj "消息内容" --chat-type group --execute

  # 直接使用（适合脚本调用）
  python3 feishu_direct_send.py --receive-id-type chat_id --receive-id oc_xxx --msg-type text --content '{"text":"你好"}'

  # 交互模式
  python3 feishu_direct_send.py --interactive

Token 管理：
  - 本地存储：~/.local/share/openclaw-feishu-uat/（AES-256-GCM 加密）
  - Access Token：有效期 2 小时，自动续期
  - Refresh Token：有效期 30 天，过期后需重新授权
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Optional, Dict, Any


# ============================================================================
# Token 解密模块
# ============================================================================

UAT_DIR = os.path.expanduser('~/.local/share/openclaw-feishu-uat')
MASTER_KEY_PATH = os.path.join(UAT_DIR, 'master.key')


def _load_master_key() -> bytes:
    """读取 AES-256 主密钥"""
    with open(MASTER_KEY_PATH, 'rb') as f:
        return f.read()


def _decrypt_token(agent_name: str) -> Optional[Dict[str, Any]]:
    """
    解密指定 Agent 的 UAT（User Access Token）
    
    存储格式：IV(12 bytes) + Tag(16 bytes) + Ciphertext
    加密方式：AES-256-GCM
    """
    try:
        # 优先尝试 agent 自己的 token，fallback 到 default
        # 动态扫描 UAT_DIR 下所有 .enc 文件，不再硬编码路径
        enc_files = []
        if os.path.exists(UAT_DIR):
            enc_files = [
                os.path.join(UAT_DIR, f)
                for f in os.listdir(UAT_DIR)
                if f.endswith('.enc')
            ]
        
        # 也尝试从 self_by_agent 配置中查找
        try:
            config_path = os.path.expanduser('~/.feishu_agent_send/config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self_info = config.get('self_by_agent', {}).get(agent_name, {})
                self_chat_id = self_info.get('chat_id', '')
                # 从 agents 配置中找 appId
                agents = config.get('agents', {})
                agent_cfg = agents.get(agent_name, {})
                if isinstance(agent_cfg, dict):
                    for scene in ['group', 'p2p']:
                        if scene in agent_cfg and isinstance(agent_cfg[scene], dict):
                            app_id = agent_cfg[scene].get('app_id')
                            if app_id:
                                safe = app_id + '_ou_a4484a2d373b28bf1baf7f114352041e'
                                safe = safe.replace('-', '_').replace('.', '_')
                                enc_path = os.path.join(UAT_DIR, safe + '.enc')
                                if os.path.exists(enc_path):
                                    enc_files.insert(0, enc_path)
                                break
        except Exception:
            pass
        
        master_key = _load_master_key()
        
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        for enc_path in enc_files:
            if not os.path.exists(enc_path):
                continue
            try:
                with open(enc_path, 'rb') as f:
                    data = f.read()
                
                # 文件格式: IV(12) + Tag(16) + Ciphertext
                iv = data[:12]
                tag = data[12:28]
                ct = data[28:]
                
                # Python cryptography 期望 Ciphertext + Tag
                aesgcm = AESGCM(master_key)
                plaintext = aesgcm.decrypt(iv, ct + tag, None)
                
                token_data = json.loads(plaintext.decode('utf-8'))
                return token_data
            except Exception:
                continue
        
        return None
    except Exception as e:
        print(f"⚠️ 无法解密 token: {e}", file=sys.stderr)
        return None


# ============================================================================
# Token 续期模块
# ============================================================================

OPENCLAW_CONFIG = '/root/.openclaw/openclaw.json'


def get_app_secret_from_openclaw(app_id: str) -> Optional[str]:
    """从 openclaw.json 动态读取 app_secret，避免硬编码"""
    try:
        if not os.path.exists(OPENCLAW_CONFIG):
            return None
        with open(OPENCLAW_CONFIG, 'r') as f:
            oc = json.load(f)
        accounts = oc.get('accounts', {})
        for acc_id, acc in accounts.items():
            plugins = acc.get('plugins', [])
            for plugin in plugins:
                if plugin.get('id') == 'openclaw-lark':
                    instances = plugin.get('instances', [])
                    for inst in instances:
                        if inst.get('appId') == app_id:
                            return inst.get('appSecret')
    except Exception:
        pass
    return None

REFRESH_TOKEN_URL = 'https://open.feishu.cn/open-apis/authen/v2/oauth/token'


def _is_token_expired(token_data: Dict[str, Any]) -> bool:
    """检查 token 是否过期或即将过期（5分钟内）"""
    now = time.time() * 1000  # 毫秒
    expires_at = token_data.get('expiresAt', 0)
    return now >= expires_at - 300000  # 5 分钟提前量


def _refresh_token(token_data: Dict[str, Any], agent_name: str = 'kfj') -> Optional[Dict[str, Any]]:
    """
    使用 Refresh Token 获取新的 Access Token
    
    POST https://open.feishu.cn/open-apis/authen/v2/oauth/token
    Body: grant_type=refresh_token&refresh_token=XXX&client_id=APP_ID&client_secret=APP_SECRET
    """
    app_id = token_data.get('appId', '')
    refresh_token = token_data.get('refreshToken', '')
    
    if not app_id or not refresh_token:
        return None
    
    app_secret = get_app_secret_from_openclaw(app_id)
    
    if not app_secret:
        print(f"⚠️ 找不到 app_id={app_id} 的 appSecret", file=sys.stderr)
        return None
    
    body = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': app_id,
        'client_secret': app_secret,
    }).encode('utf-8')
    
    req = urllib.request.Request(
        REFRESH_TOKEN_URL,
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        
        # 飞书 v2 token 接口返回 code: 0 表示成功
        if result.get('code') != 0:
            print(f"⚠️ Token 续期失败: {result}", file=sys.stderr)
            return None
        
        # 更新 token 数据
        now = time.time() * 1000
        new_token = {
            **token_data,
            'accessToken': result['data']['access_token'],
            'refreshToken': result['data']['refresh_token'],
            'expiresAt': now + result['data']['expires_in'] * 1000,
            'refreshExpiresAt': now + result['data']['refresh_expires_in'] * 1000,
            'scope': result['data'].get('scope', token_data.get('scope', '')),
        }
        
        # 写回加密存储（使用 agent_name 确保写到正确的文件）
        _save_token(new_token, agent_name)
        
        return new_token
    except urllib.error.HTTPError as e:
        print(f"⚠️ HTTP 错误: {e.code} {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️ Token 续期异常: {e}", file=sys.stderr)
        return None


def _save_token(token_data: Dict[str, Any], agent_name: str = 'kfj') -> bool:
    """保存加密后的 token 到本地"""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import secrets
        
        master_key = _load_master_key()
        plaintext = json.dumps(token_data, ensure_ascii=False).encode('utf-8')
        
        aesgcm = AESGCM(master_key)
        iv = secrets.token_bytes(12)
        ciphertext_with_tag = aesgcm.encrypt(iv, plaintext, None)
        
        # ciphertext_with_tag = ciphertext + tag(16 bytes)
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        # 存储格式: IV(12) + Tag(16) + Ciphertext
        enc_data = iv + tag + ciphertext
        
        # 根据 agent_name 动态生成文件名，避免硬编码
        app_id = token_data.get('appId', 'cli_a93af13bf5f8dbcb')
        safe_name = app_id + '_ou_a4484a2d373b28bf1baf7f114352041e'
        safe_name = safe_name.replace('-', '_').replace('.', '_')
        enc_path = os.path.join(UAT_DIR, safe_name + '.enc')
        
        os.makedirs(UAT_DIR, exist_ok=True)
        with open(enc_path, 'wb') as f:
            f.write(enc_data)
        os.chmod(enc_path, 0o600)
        
        return True
    except Exception as e:
        print(f"⚠️ 保存 token 失败: {e}", file=sys.stderr)
        return False


def get_valid_token(agent_name: str = 'kfj') -> Optional[str]:
    """获取有效的 Access Token，必要时自动续期"""
    # 校验 agent_name 格式，防止路径遍历（P1 修复）
    import re
    if not re.match(r'^[a-zA-Z0-9_]{1,32}$', str(agent_name)):
        print(f"⚠️ agent_name 格式不合法: {agent_name}", file=sys.stderr)
        return None
    token_data = _decrypt_token(agent_name)
    if not token_data:
        return None
    
    if _is_token_expired(token_data):
        print("🔄 Access Token 已过期，正在续期...", file=sys.stderr)
        token_data = _refresh_token(token_data)
        if not token_data:
            return None
    
    return token_data.get('accessToken')


# ============================================================================
# 消息发送模块
# ============================================================================

FEISHU_API_BASE = 'https://open.feishu.cn/open-apis'


def send_message(
    access_token: str,
    receive_id_type: str,
    receive_id: str,
    msg_type: str,
    content: str,
) -> Dict[str, Any]:
    """
    通过飞书 IM API 发送消息
    
    POST /open-apis/im/v1/messages?receive_id_type={type}
    """
    url = f'{FEISHU_API_BASE}/im/v1/messages?receive_id_type={receive_id_type}'
    
    body = json.dumps({
        'receive_id': receive_id,
        'msg_type': msg_type,
        'content': content,
    }).encode('utf-8')
    
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        
        if result.get('code') == 0:
            data = result.get('data', {})
            return {
                'success': True,
                'message_id': data.get('message_id'),
                'chat_id': data.get('chat_id'),
                'create_time': data.get('create_time'),
                'update_time': data.get('update_time'),
            }
        else:
            return {
                'success': False,
                'error': result.get('msg', 'unknown error'),
                'code': result.get('code'),
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace') if e.fp else ''
        return {
            'success': False,
            'error': f'HTTP {e.code}: {e.reason}',
            'detail': error_body[:500],
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }


# ============================================================================
# CLI 入口
# ============================================================================

def build_post_content(title: str, text: str, at_user_id: Optional[str] = None, at_name: Optional[str] = None) -> str:
    """构建飞书 post 消息的 content JSON"""
    content_elements = []
    
    if at_user_id:
        content_elements.append([
            {"tag": "at", "user_id": at_user_id, "user_name": at_name or ''},
            {"tag": "text", "text": f"\n\n{text}"}
        ])
    else:
        content_elements.append([
            {"tag": "text", "text": text}
        ])
    
    post_content = {
        "zh_cn": {
            "title": title,
            "content": content_elements
        }
    }
    return json.dumps(post_content, ensure_ascii=False)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='直接通过飞书 API 发送消息')
    parser.add_argument('--receive-id-type', choices=['open_id', 'chat_id', 'email', 'union_id'],
                        help='接收者 ID 类型')
    parser.add_argument('--receive-id', help='接收者 ID')
    parser.add_argument('--msg-type', choices=['text', 'post', 'image', 'file'],
                        help='消息类型')
    parser.add_argument('--content', help='消息内容（JSON 字符串）')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    parser.add_argument('--agent', default='kfj', help='当前 Agent 名称')
    
    args = parser.parse_args()
    
    if args.interactive:
        print("🚀 feishu_direct_send.py 交互模式")
        print("-" * 50)
        print("请输入参数：")
        args.receive_id_type = input("receive_id_type [chat_id]: ") or 'chat_id'
        args.receive_id = input("receive_id: ")
        args.msg_type = input("msg_type [text]: ") or 'text'
        args.content = input("content (JSON): ")
    
    if not all([args.receive_id_type, args.receive_id, args.msg_type, args.content]):
        print(json.dumps({
            'success': False,
            'error': '参数不足',
            'usage': 'python3 feishu_direct_send.py --receive-id-type chat_id --receive-id oc_xxx --msg-type text --content "{...}"',
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 1. 获取有效 token
    access_token = get_valid_token(args.agent)
    if not access_token:
        print(json.dumps({
            'success': False,
            'error': '无法获取有效的 Access Token',
            'hint': '请在飞书中重新授权',
        }, ensure_ascii=False, indent=2))
        sys.exit(1)
    
    # 2. 发送消息
    result = send_message(
        access_token=access_token,
        receive_id_type=args.receive_id_type,
        receive_id=args.receive_id,
        msg_type=args.msg_type,
        content=args.content,
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result.get('success'):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
