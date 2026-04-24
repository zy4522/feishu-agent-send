def parse_agent_message(raw_content):
    """
    自动解析 feishu_agent_send 消息
    
    支持两种格式：
    1. post 消息（群聊）：从 content.content 数组提取
    2. text 消息（私聊）：从 content.text 字符串提取
    
    Args:
        raw_content: 飞书消息的原始 content（字符串或 dict）
    
    Returns:
        dict: {
            'is_agent_message': bool,  # 是否是代理消息
            'from_agent': str,         # 发送者
            'to_agent': str,           # 接收者
            'message': str,            # 纯文本内容
            'chat_type': str,          # 'group' 或 'p2p'
            'raw_content': any         # 原始内容（调试用）
        }
    """
    import json
    
    result = {
        'is_agent_message': False,
        'from_agent': None,
        'to_agent': None,
        'message': None,
        'chat_type': None,
        'raw_content': raw_content
    }
    
    # 处理 post 消息（群聊）
    if isinstance(raw_content, dict) and 'zh_cn' in raw_content:
        result['chat_type'] = 'group'
        
        zh_cn = raw_content['zh_cn']
        title = zh_cn.get('title', '')
        content_blocks = zh_cn.get('content', [[]])[0] if zh_cn.get('content') else []
        
        # 检查是否是代理消息（通过 title 判断）
        if '【代理消息】' in title or '来自 ' in title:
            result['is_agent_message'] = True
            
            # 从 title 提取发送者和接收者
            # 格式: 【代理消息】@目标 来自 发送者
            if '来自 ' in title:
                parts = title.split('来自 ')
                if len(parts) >= 2:
                    result['from_agent'] = parts[-1].strip()
            
            if '@' in title:
                # 提取 @ 后面的目标名称
                at_part = title.split('@')[1].split(' ')[0] if '@' in title else None
                if at_part:
                    result['to_agent'] = at_part.strip()
        
        # 提取消息正文
        text_parts = []
        for block in content_blocks:
            if block.get('tag') == 'text':
                text = block.get('text', '')
                # 跳过代理标识行
                if not text.startswith('---') and not text.startswith('📨') and text.strip():
                    text_parts.append(text)
        
        result['message'] = '\n'.join(text_parts).strip()
    
    # 处理 text 消息（私聊）
    elif isinstance(raw_content, dict) and 'text' in raw_content:
        result['chat_type'] = 'p2p'
        text = raw_content['text']
        
        # 检查是否是代理消息格式
        if '【代理】' in text and '元数据：' in text:
            result['is_agent_message'] = True
            
            # 提取元数据
            try:
                metadata_start = text.find('元数据：') + 4
                metadata_end = text.find('\n---', metadata_start)
                if metadata_end == -1:
                    metadata_end = len(text)
                
                metadata_json = text[metadata_start:metadata_end].strip()
                metadata = json.loads(metadata_json)
                result['from_agent'] = metadata.get('from_agent')
                result['to_agent'] = metadata.get('to_agent')
            except:
                pass
            
            # 提取消息正文
            lines = text.split('\n')
            message_lines = []
            skip_patterns = ['📨【', '---', '实际发送者', '代理发送者', '元数据']
            for line in lines:
                if any(line.startswith(p) for p in skip_patterns):
                    continue
                message_lines.append(line)
            result['message'] = '\n'.join(message_lines).strip()
    
    return result
