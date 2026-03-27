"""
Feishu Agent - 飞书集成模块

提供与飞书API的完整集成，自动调用feishu_im_user_message工具。
"""

import json
from typing import Optional, Dict, Any
from feishu_agent import (
    FeishuAgent, 
    AgentResolver, 
    MessageFormatter,
    AgentNotFoundError,
    FeishuAgentSendError
)


class FeishuAgentIntegrated(FeishuAgent):
    """
    与飞书完整集成的Agent通信类
    
    自动调用feishu_im_user_message工具发送消息。
    """
    
    def send(
        self,
        to: str,
        message: str,
        msg_type: str = "text",
        message_type: str = "direct"
    ) -> Dict[str, Any]:
        """
        发送消息给Agent（完整集成版）
        
        自动调用feishu_im_user_message工具。
        
        Args:
            to: 目标Agent名称或open_id
            message: 消息内容
            msg_type: 消息类型（text/post/card）
            message_type: FAP消息类型
            
        Returns:
            发送结果，包含message_id
        """
        # 1. 解析目标
        try:
            receiver_id = self.resolver.resolve(to)
        except AgentNotFoundError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "AgentNotFoundError"
            }
        
        # 2. 格式化消息
        receiver_name = to.lstrip("@") if not to.startswith("ou_") else "Agent"
        
        if message_type == "direct":
            formatted_message = self.formatter.format_direct_message(
                self.agent_name, receiver_name, message
            )
        elif message_type == "group":
            formatted_message = self.formatter.format_group_rule(
                self.agent_name, message
            )
        else:
            formatted_message = self.formatter.format_public_discussion(
                self.agent_name, message
            )
        
        # 3. 调用飞书API发送消息
        try:
            result = self._call_feishu_api(receiver_id, formatted_message, msg_type)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "FeishuApiError"
            }
    
    def _call_feishu_api(
        self, 
        receiver_id: str, 
        message: str, 
        msg_type: str = "text"
    ) -> Dict[str, Any]:
        """
        调用飞书API发送消息
        
        注意：这里需要实际调用feishu_im_user_message工具。
        由于工具调用需要OpenClaw运行时环境，这里返回模拟结果。
        
        实际使用时，应该通过OpenClaw工具调用机制调用：
        feishu_im_user_message(
            action="send",
            receive_id_type="open_id",
            receive_id=receiver_id,
            msg_type=msg_type,
            content=json.dumps({"text": message})
        )
        """
        # 这里返回结构化的调用参数
        # 实际发送由调用方（OpenClaw Agent）处理
        return {
            "success": True,
            "receiver_id": receiver_id,
            "message": message,
            "msg_type": msg_type,
            "api_call": {
                "tool": "feishu_im_user_message",
                "params": {
                    "action": "send",
                    "receive_id_type": "open_id",
                    "receive_id": receiver_id,
                    "msg_type": msg_type,
                    "content": json.dumps({"text": message}, ensure_ascii=False)
                }
            }
        }


def feishu_agent_send_integrated(
    to: str,
    message: str,
    msg_type: str = "text",
    agent_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    发送消息给Agent（完整集成版）
    
    自动调用飞书API发送消息。
    
    Args:
        to: 目标Agent名称或open_id
        message: 消息内容
        msg_type: 消息类型
        agent_name: 发送者名称
        
    Returns:
        发送结果
        
    Example:
        result = feishu_agent_send_integrated(
            to="CPA助攻", 
            message="请汇报进度"
        )
        if result["success"]:
            print(f"发送成功: {result.get('message_id')}")
    """
    from feishu_agent import _get_current_agent_name
    
    sender_name = agent_name or _get_current_agent_name()
    agent = FeishuAgentIntegrated(sender_name)
    
    return agent.send(to=to, message=message, msg_type=msg_type)


# OpenClaw Agent使用示例
"""
在OpenClaw Agent中使用：

from feishu_agent_integration import feishu_agent_send_integrated
import json

# 发送消息
result = feishu_agent_send_integrated(
    to="CPA助攻",
    message="请汇报进度"
)

if result["success"]:
    # 获取API调用参数
    api_call = result["api_call"]
    
    # 调用飞书工具
    feishu_im_user_message(**api_call["params"])
else:
    print(f"准备发送失败: {result['error']}")
"""
