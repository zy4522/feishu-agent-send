#!/usr/bin/env python3
"""
feishu-agent-send 使用反馈收集工具 v3.10.3
版本：1.0
功能：收集各Agent使用feishu-agent-send的反馈信息
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

def collect_usage_feedback():
    """收集feishu-agent-send使用反馈"""
    
    # 基础信息
    feedback = {
        "timestamp": datetime.now().isoformat(),
        "agent": os.environ.get("AGENT_NAME", "unknown"),
        "session_id": os.environ.get("SESSION_ID", "unknown"),
        "config": {
            "skill_configured": False,
            "self_configured": False,
            "agents_configured": []
        },
        "usage": {
            "rules_read": False,
            "skill_used_today": False,
            "last_used": None,
            "total_usage": 0,
            "errors": []
        },
        "feedback": {
            "difficulty": 0,  # 1-5，越高越难
            "usefulness": 0,  # 1-5，越高越有用
            "suggestions": []
        }
    }
    
    # 配置文件路径
    config_path = Path.home() / ".feishu_agent_send" / "config.json"
    log_dir = Path("/tmp/openclaw")
    
    # 1. 检查技能配置
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                feedback["config"]["skill_configured"] = True
                
                # 检查self配置
                self_agent = feedback["agent"]
                if "self_by_agent" in config and self_agent in config["self_by_agent"]:
                    feedback["config"]["self_configured"] = True
                
                # 检查已配置的Agent
                if "agents" in config:
                    feedback["config"]["agents_configured"] = list(config["agents"].keys())
        except Exception as e:
            feedback["usage"]["errors"].append(f"配置读取错误: {str(e)}")
    
    # 2. 检查规则读取情况
    session_log = log_dir / f"session_{feedback['session_id']}.log"
    if session_log.exists():
        try:
            with open(session_log, 'r', encoding='utf-8') as f:
                content = f.read()
                feedback["usage"]["rules_read"] = (
                    "AGENT_RULES.md" in content or 
                    "feishu-agent-send" in content or
                    "跨Agent通信" in content
                )
        except:
            pass
    
    # 3. 检查今日使用情况
    today_log = log_dir / f"openclaw-{datetime.now().strftime('%Y-%m-%d')}.log"
    if today_log.exists():
        try:
            with open(today_log, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 检查今日是否使用
                agent_markers = [
                    f"from_agent.*{feedback['agent']}",
                    f"发送者.*{feedback['agent']}",
                    f"feishu_send.py.*{feedback['agent']}"
                ]
                
                for marker in agent_markers:
                    if marker in content:
                        feedback["usage"]["skill_used_today"] = True
                        break
                
                # 统计总使用次数
                usage_count = content.count("feishu_send.py")
                feedback["usage"]["total_usage"] = usage_count
                
                # 查找最后使用时间
                lines = content.split('\n')
                for line in reversed(lines):
                    if "feishu_send.py" in line and feedback['agent'] in line:
                        feedback["usage"]["last_used"] = line[:50]  # 取前50个字符
                        break
        except Exception as e:
            feedback["usage"]["errors"].append(f"日志读取错误: {str(e)}")
    
    return feedback

def generate_report(feedback_data):
    """生成反馈报告"""
    report = f"""# feishu-agent-send 使用反馈报告

**生成时间**: {feedback_data['timestamp']}
**报告Agent**: {feedback_data['agent']}
**Session ID**: {feedback_data['session_id']}

## 配置状态
- ✅ 技能配置: {'已配置' if feedback_data['config']['skill_configured'] else '❌ 未配置'}
- ✅ 自身配置: {'已配置' if feedback_data['config']['self_configured'] else '❌ 未配置'}
- 📋 已配置Agent: {', '.join(feedback_data['config']['agents_configured']) if feedback_data['config']['agents_configured'] else '无'}

## 使用情况
- 📖 规则读取: {'✅ 已读取' if feedback_data['usage']['rules_read'] else '❌ 未读取'}
- 🔧 今日使用: {'✅ 已使用' if feedback_data['usage']['skill_used_today'] else '🟡 未使用'}
- 📊 总使用次数: {feedback_data['usage']['total_usage']} 次
- 🕒 最后使用: {feedback_data['usage']['last_used'] or '无记录'}

## 问题记录
"""
    
    if feedback_data['usage']['errors']:
        for error in feedback_data['usage']['errors']:
            report += f"- ❌ {error}\n"
    else:
        report += "- ✅ 无错误记录\n"
    
    report += """
## 使用建议
1. **首次使用**: 确保运行 `feishu_set_self.py` 配置自身信息
2. **添加其他Agent**: 使用 `feishu_add.py` 添加通信对象
3. **发送消息**: 使用 `feishu_send.py --deliver` 生成命令并执行
4. **问题排查**: 使用 `feishu_status.py` 检查配置状态

## 监控建议
- 定期运行此脚本检查使用情况
- 查看 `/tmp/feishu_agent_feedback.json` 了解详细数据
- 如有问题，检查日志文件获取详细信息
"""
    
    return report

def save_feedback(feedback_data, report_text):
    """保存反馈数据"""
    
    # 保存JSON数据
    json_path = Path("/tmp/feishu_agent_feedback.json")
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存JSON数据失败: {e}")
    
    # 保存报告
    report_path = Path("/tmp/feishu_agent_report.md")
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
    except Exception as e:
        print(f"保存报告失败: {e}")
    
    return json_path, report_path

if __name__ == "__main__":
    print("收集 feishu-agent-send 使用反馈...")
    
    # 收集数据
    feedback = collect_usage_feedback()
    
    # 生成报告
    report = generate_report(feedback)
    
    # 保存数据
    json_path, report_path = save_feedback(feedback, report)
    
    # 输出摘要
    print(f"\n✅ 反馈收集完成")
    print(f"📊 配置状态: {'✅' if feedback['config']['skill_configured'] else '❌'}")
    print(f"📖 规则读取: {'✅' if feedback['usage']['rules_read'] else '❌'}")
    print(f"🔧 今日使用: {'✅' if feedback['usage']['skill_used_today'] else '❌'}")
    print(f"📁 数据保存: {json_path}")
    print(f"📄 报告保存: {report_path}")
    
    # 如果有问题，给出建议
    if not feedback['config']['skill_configured']:
        print("\n⚠️ 建议: 检查 ~/.feishu_agent_send/config.json 配置文件")
    
    if not feedback['config']['self_configured']:
        print("⚠️ 建议: 运行 feishu_set_self.py 配置自身信息")
    
    if not feedback['usage']['rules_read']:
        print("⚠️ 建议: 在Session启动时读取AGENT_RULES.md第6章")
    
    sys.exit(0)