#!/usr/bin/env python3
"""
feishu_set_self.py - 设置当前 Agent 的 self 信息

用法：
  python3 feishu_set_self.py <Agent名称> <chat_id>

示例：
  python3 feishu_set_self.py kfj oc_4811eda51e2e9626fc7dfea21882942b
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feishu_agent_send import AgentConfig


def main():
    if len(sys.argv) < 3:
        print("用法: python3 feishu_set_self.py <Agent名称> <chat_id>")
        print("示例: python3 feishu_set_self.py kfj oc_xxx")
        sys.exit(1)
    
    agent_name = sys.argv[1]
    chat_id = sys.argv[2]
    
    AgentConfig.set_self(agent_name, chat_id)
    print(f"✅ 已设置 {agent_name} 的 self 信息: {chat_id[:20]}...")
    
    # 显示已配置的所有 Agent
    all_self = AgentConfig.get_all_self()
    if len(all_self) > 1:
        print("\n已配置的 Agent self 列表:")
        for name, info in all_self.items():
            cid = info.get('chat_id', '')[:20]
            print(f"  • {name}: {cid}...")


if __name__ == '__main__':
    main()
