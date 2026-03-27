"""
feishu_agent_send - 飞书Agent通信工具 v1.1.0

核心机制：Agent借助彦哥的飞书通道发送消息，接收方通过格式识别实际发送者

⚠️ 重要提示：在群聊中必须使用本工具发送消息，否则其他 Agent 收不到！
"""

import json
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime


class AgentNotFoundError(Exception):
    """找不到Agent时抛出"""
    pass


class FeishuAgentSendError(Exception):
    """发送消息失败时抛出"""
    pass


# 安装时显示提示
_INSTALLATION_SHOWN = False

def _show_installation_notice():
    """显示安装提示（只显示一次）"""
    global _INSTALLATION_SHOWN
    if _INSTALLATION_SHOWN:
        return
    
    print("""
╔════════════════════════════════════════════════════════════╗
║  🎉 feishu_agent_send 安装成功！                          ║
╠════════════════════════════════════════════════════════════╣
║  ⚠️  重要提示：                                            ║
║     在群聊中发送消息时，必须使用 feishu_agent_send！        ║
║     普通消息无法被其他 Agent 接收。                         ║
╠════════════════════════════════════════════════════════════╣
║  📖 快速开始：                                              ║
║     from feishu_agent_send import feishu_agent_send_and_deliver
║     result = feishu_agent_send_and_deliver(...)            ║
║     feishu_im_user_message(**result['send_params'])        ║
╠════════════════════════════════════════════════════════════╣
║  📚 详细文档：SKILL.md                                      ║
╚════════════════════════════════════════════════════════════╝
""")
    _INSTALLATION_SHOWN = True


# 模块加载时显示提示
_show_installation_notice()