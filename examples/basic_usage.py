#!/usr/bin/env python3
"""
feishu-agent-send 基础用法示例
"""

import sys
sys.path.insert(0, '..')

from feishu_agent_send import (
    setup_agent,
    feishu_agent_send_and_deliver,
    get_chat_id,
    list_known_agents
)


def example_1_setup_agent():
    """示例1：首次配置Agent"""
    print("=== 示例1：配置Agent ===")
    
    # 添加新Agent
    setup_agent(
        name="我的助手",
        chat_id="oc_xxx",  # 从飞书获取
        open_id="ou_xxx"   # 可选
    )
    
    print("✅ Agent配置成功！")
    print()


def example_2_send_message():
    """示例2：发送消息"""
    print("=== 示例2：发送消息 ===")
    
    # 一键准备发送
    result = feishu_agent_send_and_deliver(
        to="我的助手",
        message="你好！这是测试消息。",
        from_agent="我"
    )
    
    if result["success"]:
        print("✅ 消息准备成功！")
        print(f"格式化消息：{result['formatted_message'][:50]}...")
        print(f"chat_id：{result.get('chat_id', '无')}")
        print()
        print("下一步：使用 feishu_im_user_message 实际发送")
        # feishu_im_user_message(**result["send_params"])
    else:
        print(f"❌ 失败：{result.get('error')}")
    print()


def example_3_query_chat_id():
    """示例3：查询chat_id"""
    print("=== 示例3：查询chat_id ===")
    
    chat_id = get_chat_id("我的助手")
    if chat_id:
        print(f"✅ 找到chat_id：{chat_id}")
    else:
        print("❌ 未找到chat_id")
    print()


def example_4_list_agents():
    """示例4：列出所有Agent"""
    print("=== 示例4：列出所有Agent ===")
    
    agents = list_known_agents()
    print(f"共有 {len(agents)} 个Agent：")
    for name, info in agents.items():
        print(f"  - {name}: chat_id={info['chat_id'][:20]}...")
    print()


if __name__ == "__main__":
    print("feishu-agent-send 基础用法示例")
    print("=" * 40)
    print()
    
    # 运行示例
    example_4_list_agents()
    example_3_query_chat_id()
    
    print("提示：运行示例1和2前，请先修改代码中的chat_id为你自己的值")
