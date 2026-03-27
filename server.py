#!/usr/bin/env python3
"""
Feishu Agent Send - MCP Server
让 feishu_agent_send 作为 MCP 工具被 Agent 调用
"""

import json
import sys
from typing import Any

# 添加 skill 路径
sys.path.insert(0, "/root/.openclaw/skills/feishu_agent_send")
from feishu_agent_send import feishu_agent_send, AgentNotFoundError


def send_tool(arguments: dict) -> dict:
    """MCP 工具：发送消息给 Agent"""
    to = arguments.get("to")
    message = arguments.get("message")
    msg_type = arguments.get("msg_type", "text")
    agent_name = arguments.get("agent_name")
    
    if not to or not message:
        return {
            "content": [{"type": "text", "text": "错误：缺少必需参数 'to' 或 'message'"}],
            "isError": True
        }
    
    try:
        result = feishu_agent_send(
            to=to,
            message=message,
            msg_type=msg_type,
            agent_name=agent_name
        )
        
        if result.get("success"):
            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ 消息已格式化\n\n接收者: {result['receiver_name']} ({result['receiver_id']})\n\n格式化内容:\n{result['formatted_message']}"
                }]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"❌ 失败: {result.get('error', '未知错误')}"}],
                "isError": True
            }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"❌ 异常: {str(e)}"}],
            "isError": True
        }


def main():
    """MCP Server 主循环"""
    # 发送初始化响应
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "feishu_agent_send", "version": "1.0.0"}
        }
    }), flush=True)
    
    # 处理工具列表请求
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [{
                "name": "feishu_agent_send",
                "description": "向飞书Agent发送消息，支持通过名称或open_id指定目标",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "目标Agent名称（如'CPA助攻'）或open_id（如'ou_xxx'）"
                        },
                        "message": {
                            "type": "string",
                            "description": "要发送的消息内容"
                        },
                        "msg_type": {
                            "type": "string",
                            "enum": ["text", "post", "card"],
                            "description": "消息类型，默认text"
                        },
                        "agent_name": {
                            "type": "string",
                            "description": "发送者名称，可选"
                        }
                    },
                    "required": ["to", "message"]
                }
            }]
        }
    }), flush=True)
    
    # 处理工具调用
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            
            if method == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                arguments = params.get("arguments", {})
                
                if name == "feishu_agent_send":
                    result = send_tool(arguments)
                    print(json.dumps({
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": result
                    }), flush=True)
                    
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": str(e)}
            }), flush=True)


if __name__ == "__main__":
    main()
