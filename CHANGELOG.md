# CHANGELOG - feishu-agent-send

## v3.9.0 (2026-04-25)
- --execute 模式升级为真正的一站式发送：直接调用飞书 API
- 新增 feishu_direct_send.py 独立发送模块
- UAT 解密支持增强
- parse_agent_message() 正则解析加固
- 批量发送支持（逗号分隔多目标）
- 版本号统一至 _version.py
- 命令注入修复（feishu_execute.py json.dumps 安全转义）
- agent_name 格式校验、chat_id 长度+字集校验
- 静默异常改为 warnings.warn 提示
- SKILL.md 从 524 行精简至 ~130 行

## v3.8.0 (2026-04-24)
- 修复 --execute 假执行问题
- 修复 feishu_status.py 版本检查误报
- 统一所有工具版本号
- 新增 parse_agent_message() 骨架
- 新增批量发送支持骨架

## v3.7.0 (2026-04-24)
- 单 self 自动选择
- --execute 直接执行模式
- feishu_status.py 配置诊断工具
- 配置防呆检查
- 消息来源标识优化
- --actual-sender 双身份支持

## v3.6.0 (2026-04-23)
- 合并群聊 @ 功能与代码改进
- JSON 元数据格式替代 HTML 注释
- 代码精简、Bug 修复

## v3.5.0 (2026-04-23)
- 群聊 post 富文本格式、@ 提醒
- 群初始化采集 app_id

## v3.4.0 (2026-04-23)
- 删除不可用 --send
- 修复 get_agent_info 多场景判断
- 统一代理发送者字段

## v3.2.0 (2026-04-22)
- main 路径检测、消息格式规范
- openclaw.json 绑定检查

## v3.0.1 (2026-04-22)
- 群消息延迟发送、移除真实 chat_id

## v3.0.0 (2026-04-22)
- --deliver 一站式发送
- 多场景提示、用户语言错误
- chat_type 验证
