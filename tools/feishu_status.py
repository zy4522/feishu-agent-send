#!/usr/bin/env python3
"""
feishu_status.py - 飞书 Agent 配置诊断工具 v3.9.0

用法：
  python3 feishu_status.py [选项]

选项：
  --check <Agent名>    检查指定 Agent 的配置
  --fix                尝试修复发现的问题

示例：
  # 检查所有配置
  python3 feishu_status.py
  
  # 检查指定 Agent
  python3 feishu_status.py --check kfj
  
  # 检查并尝试修复
  python3 feishu_status.py --fix
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig, list_known_agents


def check_version(config):
    """检查版本号一致性"""
    file_version = "3.9.0"  # 代码中的版本
    config_version = config.get('version', 'unknown')
    
    if config_version != file_version:
        return {
            'status': 'warning',
            'message': f'版本号不一致: 配置={config_version}, 代码={file_version}',
            'fix': f'更新 config.json 中的 version 为 "{file_version}"'
        }
    return {'status': 'ok', 'message': f'版本号一致: {file_version}'}


def check_self_config(config):
    """检查 self 配置"""
    self_by_agent = config.get('self_by_agent', {})
    
    if not self_by_agent:
        return {
            'status': 'error',
            'message': '缺少 self 配置，无法发送消息',
            'fix': '运行: python3 feishu_set_self.py <Agent名> <chat_id>'
        }
    
    results = []
    for agent_name, info in self_by_agent.items():
        chat_id = info.get('chat_id', '')
        if not chat_id:
            results.append({
                'status': 'error',
                'agent': agent_name,
                'message': f'{agent_name} 缺少 chat_id',
                'fix': f'运行: python3 feishu_set_self.py {agent_name} oc_xxx'
            })
        elif not chat_id.startswith('oc_'):
            results.append({
                'status': 'warning',
                'agent': agent_name,
                'message': f'{agent_name} 的 chat_id 格式可能不正确: {chat_id[:20]}...',
                'fix': '确认 chat_id 以 oc_ 开头'
            })
        else:
            results.append({
                'status': 'ok',
                'agent': agent_name,
                'message': f'{agent_name}: {chat_id[:20]}...'
            })
    
    return results


def check_agents_config(config):
    """检查 agents 配置"""
    agents = config.get('agents', {})
    
    if not agents:
        return {
            'status': 'warning',
            'message': '没有配置任何 Agent 联系人',
            'fix': '运行: python3 feishu_add.py <Agent名> <chat_id>'
        }
    
    results = []
    for agent_name, agent_config in agents.items():
        # 检查是否是多场景配置
        if isinstance(agent_config, dict) and ('p2p' in agent_config or 'group' in agent_config):
            # 多场景配置
            for scene in ['p2p', 'group']:
                if scene in agent_config:
                    scene_config = agent_config[scene]
                    chat_id = scene_config.get('chat_id', '')
                    app_id = scene_config.get('app_id', '')
                    
                    if not chat_id:
                        results.append({
                            'status': 'error',
                            'agent': agent_name,
                            'scene': scene,
                            'message': f'{agent_name} ({scene}) 缺少 chat_id',
                            'fix': f'运行: python3 feishu_add.py {agent_name} oc_xxx --chat-type {scene}'
                        })
                    elif scene == 'group' and not app_id:
                        results.append({
                            'status': 'warning',
                            'agent': agent_name,
                            'scene': scene,
                            'message': f'{agent_name} (群聊) 缺少 app_id，无法@提醒',
                            'fix': f'运行: python3 feishu_add.py {agent_name} {chat_id} --chat-type group，然后添加 app_id'
                        })
                    else:
                        status = 'ok'
                        msg = f'{agent_name} ({scene}): {chat_id[:20]}...'
                        if app_id:
                            msg += f', app_id={app_id[:20]}...'
                        results.append({
                            'status': status,
                            'agent': agent_name,
                            'scene': scene,
                            'message': msg
                        })
        else:
            # 单场景配置（旧格式）
            chat_id = agent_config.get('chat_id', '')
            chat_type = agent_config.get('chat_type', 'p2p')
            app_id = agent_config.get('app_id', '')
            
            if not chat_id:
                results.append({
                    'status': 'error',
                    'agent': agent_name,
                    'message': f'{agent_name} 缺少 chat_id',
                    'fix': f'运行: python3 feishu_add.py {agent_name} oc_xxx'
                })
            else:
                status = 'ok'
                msg = f'{agent_name} ({chat_type}): {chat_id[:20]}...'
                if app_id:
                    msg += f', app_id={app_id[:20]}...'
                results.append({
                    'status': status,
                    'agent': agent_name,
                    'message': msg
                })
    
    return results


def check_config_consistency(config):
    """检查配置一致性（v3.9.0 修复误报）"""
    issues = []
    
    # 群聊 chat_id 允许多个 Agent 使用（正常），只检查私聊重复
    p2p_chat_ids = {}
    agents = config.get('agents', {})
    
    for agent_name, agent_config in agents.items():
        if isinstance(agent_config, dict):
            if 'chat_id' in agent_config:
                cid = agent_config['chat_id']
                # oc_ 开头的是群聊，不检查重复
                if not cid.startswith('oc_'):
                    if cid in p2p_chat_ids:
                        issues.append({
                            'status': 'warning',
                            'message': f'私聊 chat_id {cid[:20]}... 被多个 Agent 使用: {p2p_chat_ids[cid]} 和 {agent_name}'
                        })
                    else:
                        p2p_chat_ids[cid] = agent_name
            
            for scene in ['p2p', 'group']:
                if scene in agent_config and isinstance(agent_config[scene], dict):
                    cid = agent_config[scene].get('chat_id', '')
                    if cid:
                        # 只检查私聊重复，群聊不检查
                        if scene == 'p2p' and not cid.startswith('oc_'):
                            if cid in p2p_chat_ids:
                                issues.append({
                                    'status': 'warning',
                                    'message': f'私聊 chat_id {cid[:20]}... 被多个 Agent 使用: {p2p_chat_ids[cid]} 和 {agent_name} (p2p)'
                                })
                            else:
                                p2p_chat_ids[cid] = f'{agent_name} (p2p)'
    
    # 检查 self 配置是否和 agents 配置冲突（v3.9.0 修复误报）
    self_by_agent = config.get('self_by_agent', {})
    for self_name, self_info in self_by_agent.items():
        self_chat_id = self_info.get('chat_id', '')
        # 只检查私聊 chat_id 冲突，群聊忽略
        if self_chat_id and not self_chat_id.startswith('oc_'):
            if self_chat_id in p2p_chat_ids:
                agent_with_chat = p2p_chat_ids[self_chat_id]
                if agent_with_chat == self_name or agent_with_chat == f'{self_name} (p2p)':
                    continue  # 正常的自我引用，跳过
                issues.append({
                    'status': 'warning',
                    'message': f'self 配置 {self_name} 的私聊 chat_id 与 agent {agent_with_chat} 重复'
                })
    
    if not issues:
        return [{'status': 'ok', 'message': '配置一致性检查通过'}]
    
    return issues

def generate_report(check_results):
    """生成诊断报告"""
    print("\n" + "="*60)
    print("📊 feishu-agent-send 配置诊断报告")
    print("="*60)
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"配置文件: {AgentConfig._config_path()}")
    print("-"*60)
    
    total_ok = 0
    total_warning = 0
    total_error = 0
    
    for section, results in check_results.items():
        print(f"\n【{section}】")
        
        if isinstance(results, list):
            for result in results:
                status = result.get('status', 'unknown')
                message = result.get('message', '')
                fix = result.get('fix', '')
                
                if status == 'ok':
                    print(f"  ✅ {message}")
                    total_ok += 1
                elif status == 'warning':
                    print(f"  ⚠️  {message}")
                    if fix:
                        print(f"     修复: {fix}")
                    total_warning += 1
                elif status == 'error':
                    print(f"  ❌ {message}")
                    if fix:
                        print(f"     修复: {fix}")
                    total_error += 1
        else:
            status = results.get('status', 'unknown')
            message = results.get('message', '')
            fix = results.get('fix', '')
            
            if status == 'ok':
                print(f"  ✅ {message}")
                total_ok += 1
            elif status == 'warning':
                print(f"  ⚠️  {message}")
                if fix:
                    print(f"     修复: {fix}")
                total_warning += 1
            elif status == 'error':
                print(f"  ❌ {message}")
                if fix:
                    print(f"     修复: {fix}")
                total_error += 1
    
    print("\n" + "="*60)
    print(f"诊断结果: ✅ {total_ok} 正常 | ⚠️ {total_warning} 警告 | ❌ {total_error} 错误")
    print("="*60)
    
    if total_error > 0:
        print("\n⚠️  发现错误，建议立即修复")
        return 1
    elif total_warning > 0:
        print("\n💡 发现警告，建议检查优化")
        return 0
    else:
        print("\n🎉 所有检查通过，配置健康！")
        return 0


def fix_issues(config, check_results):
    """尝试修复发现的问题"""
    fixed = []
    
    # 修复版本号
    version_check = check_results.get('版本检查', {})
    if isinstance(version_check, dict) and version_check.get('status') == 'warning':
        config['version'] = '3.9.0'
        fixed.append('更新版本号为 3.9.0')
    
    # 保存修复后的配置
    if fixed:
        AgentConfig.save(config)
        print(f"\n✅ 已自动修复 {len(fixed)} 个问题:")
        for fix in fixed:
            print(f"  - {fix}")
    else:
        print("\n💡 没有可自动修复的问题")
    
    return fixed


def main():
    args = sys.argv[1:]
    
    check_agent = None
    fix_mode = False
    
    i = 0
    while i < len(args):
        if args[i] == '--check' and i + 1 < len(args):
            check_agent = args[i + 1]
            i += 2
        elif args[i] == '--fix':
            fix_mode = True
            i += 1
        else:
            i += 1
    
    # 加载配置
    config = AgentConfig.load()
    
    # 执行检查
    check_results = {}
    
    # 1. 版本检查
    check_results['版本检查'] = check_version(config)
    
    # 2. Self 配置检查
    check_results['Self 配置'] = check_self_config(config)
    
    # 3. Agents 配置检查
    check_results['Agents 配置'] = check_agents_config(config)
    
    # 4. 一致性检查
    check_results['一致性检查'] = check_config_consistency(config)
    
    # 生成报告
    exit_code = generate_report(check_results)
    
    # 尝试修复
    if fix_mode:
        print("\n" + "-"*60)
        print("🔧 自动修复模式")
        print("-"*60)
        fix_issues(config, check_results)
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
