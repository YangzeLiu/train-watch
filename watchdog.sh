#!/bin/bash
# watchdog.sh — 定时唤醒 Claude Code 检查训练状态
#
# 用法:
#   chmod +x watchdog.sh
#   ./watchdog.sh --session 6fc07dc6-1d68-4db1-a766-92de29407563 --pid 12345 --log train.log
#   后台运行: nohup ./watchdog.sh ... > watchdog.out 2>&1 &

set -euo pipefail

# ── 默认配置 ──────────────────────────────────────────────
INTERVAL=1800          # 检查间隔（秒），默认 30 分钟
SESSION_ID=""
PID=""
LOG_FILE=""
DISK_PATH="."
STATUS_LOG=".train_status.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_PY="$SCRIPT_DIR/monitor.py"

# ── 参数解析 ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --session)   SESSION_ID="$2"; shift 2 ;;
        --pid)       PID="$2";        shift 2 ;;
        --log)       LOG_FILE="$2";   shift 2 ;;
        --interval)  INTERVAL="$2";   shift 2 ;;
        --disk)      DISK_PATH="$2";  shift 2 ;;
        --status-log) STATUS_LOG="$2"; shift 2 ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# ── 校验 ──────────────────────────────────────────────────
if [[ -z "$SESSION_ID" ]]; then
    echo "❌ 必须提供 --session <claude-session-id>"
    echo "   启动训练前先开一个 claude 会话，在会话里用 /status 或看终端标题获取 session id"
    exit 1
fi

if ! command -v claude &>/dev/null; then
    echo "❌ 找不到 claude 命令，请先安装 Claude Code"
    exit 1
fi

if [[ ! -f "$MONITOR_PY" ]]; then
    echo "❌ 找不到 monitor.py，请确保它和 watchdog.sh 在同一目录"
    exit 1
fi

# ── 构建 monitor 命令 ──────────────────────────────────────
build_monitor_cmd() {
    local cmd="python3 $MONITOR_PY"
    [[ -n "$PID" ]]      && cmd="$cmd --pid $PID"
    [[ -n "$LOG_FILE" ]] && cmd="$cmd --log $LOG_FILE"
    cmd="$cmd --disk $DISK_PATH"
    echo "$cmd"
}

# ── 单次 check ────────────────────────────────────────────
do_check() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] 开始 check..."

    # 1. 采集状态
    local monitor_cmd
    monitor_cmd=$(build_monitor_cmd)
    local summary
    summary=$(eval "$monitor_cmd" 2>&1)

    echo "$summary"

    # 2. 构建发给 Claude 的 prompt
    local prompt
    prompt=$(cat <<EOF
[自动 Watchdog Check — $timestamp]

以下是当前训练状态快照：

$summary

请你：
1. 判断训练是否正常
2. 如果发现 CRITICAL 问题，立即采取行动（修复代码 / 重启训练），不需要再征求我的同意
3. 将你的判断和操作记录追加写入 $STATUS_LOG，格式为：[$timestamp] <你的判断和操作>
4. 如果一切正常，只需在 $STATUS_LOG 里写一行 OK 记录即可，不必做其他事
EOF
)

    # 3. 唤醒 Claude Code
    echo "[$timestamp] 唤醒 Claude..."
    claude --resume "$SESSION_ID" \
           --dangerously-skip-permissions \
           -p "$prompt" \
        >> watchdog.out 2>&1 || {
        echo "[$timestamp] ⚠️ Claude 调用失败，见 watchdog.out"
    }

    echo "[$timestamp] Check 完成，下次检查在 $((INTERVAL / 60)) 分钟后"
    echo "────────────────────────────────────"
}

# ── 主循环 ────────────────────────────────────────────────
WATCHDOG_PID_FILE=".watchdog.pid"
echo $$ > "$WATCHDOG_PID_FILE"

echo "🚀 Watchdog 启动"
echo "   Watchdog PID: $$ (保存在 $WATCHDOG_PID_FILE)"
echo "   Session : $SESSION_ID"
echo "   PID     : ${PID:-未指定}"
echo "   Log     : ${LOG_FILE:-未指定}"
echo "   间隔    : $((INTERVAL / 60)) 分钟"
echo "   状态 log: $STATUS_LOG"
echo "   停止方法: kill \$(cat $WATCHDOG_PID_FILE)"
echo "────────────────────────────────────"

# 立即跑一次，确认配置没问题
do_check

while true; do
    sleep "$INTERVAL"
    do_check
done
