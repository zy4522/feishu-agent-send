#!/bin/bash
# pre_push_check.sh - Push 前自动检查
# 用法：在 feishu-agent-send 仓库根目录运行 bash tools/pre_push_check.sh
# 或挂载到 .git/hooks/pre-push

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

cd "$REPO_DIR"

ERRORS=0

echo "========================================="
echo "  Pre-push Check: feishu-agent-send"
echo "========================================="

# --------------------------------------------------
# 1. 版本号一致性检查
# --------------------------------------------------
echo ""
echo "📌 [1/4] 版本号一致性..."

# 提取各文件中的版本号
send_ver=$(grep -oP 'v[\d]+\.[\d]+\.[\d]+' tools/feishu_send.py | head -1 || echo "NOT_FOUND")
status_ver=$(grep -oP 'v[\d]+\.[\d]+\.[\d]+' tools/feishu_status.py | head -1 || echo "NOT_FOUND")
scan_ver=$(grep -oP 'v[\d]+\.[\d]+\.[\d]+' tools/feishu_scan_group.py | head -1 || echo "NOT_FOUND")
add_ver=$(grep -oP 'v[\d]+\.[\d]+\.[\d]+' tools/feishu_add.py | head -1 || echo "NOT_FOUND")
skill_ver=$(grep -oP '[\d]+\.[\d]+\.[\d]+' SKILL.md | head -1 || echo "NOT_FOUND")

# 统一格式为 v1.2.3
send_v="${send_ver#v}"
status_v="${status_ver#v}"
scan_v="${scan_ver#v}"
add_v="${add_ver#v}"

if [ "$send_v" != "$skill_ver" ]; then
    echo "  ❌ feishu_send.py: $send_ver ≠ SKILL.md: $skill_ver"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ feishu_send.py: $send_ver"
fi

if [ "$status_v" != "$skill_ver" ]; then
    echo "  ❌ feishu_status.py: $status_ver ≠ SKILL.md: $skill_ver"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ feishu_status.py: $status_ver"
fi

if [ "$scan_v" != "$skill_ver" ]; then
    echo "  ❌ feishu_scan_group.py: $scan_ver ≠ SKILL.md: $skill_ver"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ feishu_scan_group.py: $scan_ver"
fi

if [ "$add_v" != "$skill_ver" ]; then
    echo "  ❌ feishu_add.py: $add_ver ≠ SKILL.md: $skill_ver"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ feishu_add.py: $add_ver"
fi

# --------------------------------------------------
# 2. SKILL.md 重复段落检查
# --------------------------------------------------
echo ""
echo "📌 [2/4] SKILL.md 重复内容..."

# 统计 "✨ v3.x 改进" 出现次数
dup_count=$(grep -c '✨ v[0-9]' SKILL.md || echo "0")
# 统计版本历史表中有多少个版本行
hist_count=$(grep -cP '^\| v[0-9]' SKILL.md || echo "0")

if [ "$dup_count" -gt "$hist_count" ]; then
    echo "  ❌ 改进段落($dup_count)多于版本历史条目($hist_count)，可能有重复"
    echo "     请检查是否有多个相同的 v3.x 改进段落"
    grep -n '✨ v[0-9]' SKILL.md | while read line; do
        echo "    → $line"
    done
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ 改进段落数($dup_count) = 版本历史数($hist_count)"
fi

# --------------------------------------------------
# 3. 版本历史表必须包含最新版本
# --------------------------------------------------
echo ""
echo "📌 [3/4] 版本历史表..."

if ! grep -qP "\\| v${skill_ver} " SKILL.md; then
    echo "  ❌ 版本历史表缺少 v$skill_ver 条目"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✅ 版本历史表已包含 v$skill_ver"
fi

# 检查最新版本是否排在第一行
first_hist=$(grep -P '^\| v[0-9]' SKILL.md | head -1)
if echo "$first_hist" | grep -qP "\\| v${skill_ver} "; then
    echo "  ✅ v$skill_ver 在版本历史第一行（最新位置）"
else
    echo "  ⚠️  v$skill_ver 不在版本历史第一行，建议移上去"
    echo "     当前第一行: $first_hist"
fi

# --------------------------------------------------
# 4. 关键函数存在性检查
# --------------------------------------------------
echo ""
echo "📌 [4/4] 关键函数存在性..."

# 检查 send_to_agent 主函数是否存在
if grep -q 'def send_to_agent' tools/feishu_send.py 2>/dev/null; then
    echo "  ✅ feishu_send.py: send_to_agent 函数存在"
else
    echo "  ❌ feishu_send.py: send_to_agent 函数缺失"
    ERRORS=$((ERRORS + 1))
fi

# 检查 feishu_direct_send.py 是否存在（v3.9.0 引入的独立模块）
if [ -f "tools/feishu_direct_send.py" ]; then
    echo "  ✅ feishu_direct_send.py: 独立发送模块存在"
    if grep -q 'def send_message' tools/feishu_direct_send.py 2>/dev/null; then
        echo "  ✅ feishu_direct_send.py: send_message 函数存在"
    else
        echo "  ⚠️  feishu_direct_send.py: send_message 函数可能缺失"
    fi
else
    echo "  ⚠️  feishu_direct_send.py: 不存在（如果不是 v3.9.0+ 可忽略）"
fi

# --------------------------------------------------
# 结果
# --------------------------------------------------
echo ""
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    echo "  ✅ All checks passed! 可以 push"
    echo "========================================="
    exit 0
else
    echo "  ❌ $ERRORS 个错误，请修复后再 push"
    echo "========================================="
    exit 1
fi
