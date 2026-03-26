#!/usr/bin/env python3
"""
monitor.py — 训练状态快照，输出纯文本 summary 供 Claude 读取
用法: python monitor.py --pid 12345 --log train.log
"""

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def check_process(pid: int) -> dict:
    try:
        os.kill(pid, 0)
        return {"alive": True, "pid": pid}
    except ProcessLookupError:
        return {"alive": False, "pid": pid, "reason": "进程不存在"}
    except PermissionError:
        return {"alive": True, "pid": pid}


def check_gpu() -> list[dict]:
    try:
        result = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=index,utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        gpus = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",")]
            gpus.append({
                "index": parts[0],
                "util": int(parts[1]),
                "mem_used": int(parts[2]),
                "mem_total": int(parts[3]),
                "temp": int(parts[4]),
            })
        return gpus
    except Exception as e:
        return [{"error": str(e)}]


def check_log(log_path: str, tail_lines: int = 50) -> dict:
    path = Path(log_path)
    if not path.exists():
        return {"error": f"Log 文件不存在: {log_path}"}

    try:
        result = subprocess.run(
            ["tail", "-n", str(tail_lines), str(path)],
            capture_output=True, text=True
        )
        lines = result.stdout
    except Exception:
        with open(path) as f:
            lines = "".join(f.readlines()[-tail_lines:])

    issues = []
    error_patterns = [
        (r"\bnan\b|\bNaN\b|\bNAN\b", "NaN detected"),
        (r"\binf\b|\bInf\b|\bINF\b", "Inf detected"),
        (r"CUDA out of memory|OOM", "OOM"),
        (r"Error|Exception|Traceback", "Error/Exception"),
        (r"Killed|killed", "进程被 kill"),
        (r"Disk quota exceeded|No space left", "磁盘空间不足"),
    ]
    for pattern, label in error_patterns:
        if re.search(pattern, lines):
            issues.append(label)

    # 提取最近的 loss（支持常见格式）
    loss_pattern = r"[Ll]oss[:\s=]+([0-9]+\.?[0-9]*(?:e[-+]?[0-9]+)?)"
    losses = re.findall(loss_pattern, lines)
    latest_loss = losses[-1] if losses else None

    # 最后一行
    last_line = lines.strip().split("\n")[-1] if lines.strip() else "(empty)"

    return {
        "issues": issues,
        "latest_loss": latest_loss,
        "last_line": last_line,
        "log_path": str(path),
    }


def check_disk(path: str = ".") -> dict:
    try:
        result = subprocess.run(
            ["df", "-h", path],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            return {"total": parts[1], "used": parts[2], "avail": parts[3], "use_pct": parts[4]}
    except Exception as e:
        return {"error": str(e)}
    return {}


def format_summary(pid_info, gpus, log_info, disk_info) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"=== 训练状态快照 [{now}] ===", ""]

    # 进程
    if pid_info:
        status = "✅ 存活" if pid_info["alive"] else f"❌ 已死亡 ({pid_info.get('reason', '')})"
        lines.append(f"[进程] PID {pid_info['pid']}: {status}")
    else:
        lines.append("[进程] 未指定 PID，跳过检查")

    # GPU
    lines.append("")
    if gpus and "error" not in gpus[0]:
        for g in gpus:
            util_warn = " ⚠️ 利用率极低！" if g["util"] < 5 else ""
            lines.append(
                f"[GPU {g['index']}] 利用率 {g['util']}%{util_warn} | "
                f"显存 {g['mem_used']}/{g['mem_total']} MB | 温度 {g['temp']}°C"
            )
    else:
        lines.append(f"[GPU] 获取失败: {gpus[0].get('error', '未知')}")

    # Log
    lines.append("")
    if "error" in log_info:
        lines.append(f"[Log] {log_info['error']}")
    else:
        if log_info["issues"]:
            lines.append(f"[Log] ⚠️ 发现问题: {', '.join(log_info['issues'])}")
        else:
            lines.append("[Log] 未发现明显异常")
        if log_info["latest_loss"]:
            lines.append(f"[Loss] 最新值: {log_info['latest_loss']}")
        lines.append(f"[Log 末行] {log_info['last_line']}")

    # 磁盘
    lines.append("")
    if "error" not in disk_info and disk_info:
        use_pct = int(disk_info["use_pct"].replace("%", ""))
        disk_warn = " ⚠️ 磁盘即将满！" if use_pct > 90 else ""
        lines.append(
            f"[磁盘] 已用 {disk_info['used']}/{disk_info['total']} ({disk_info['use_pct']}){disk_warn} | 剩余 {disk_info['avail']}"
        )

    # 综合判断
    lines.append("")
    critical = []
    if pid_info and not pid_info["alive"]:
        critical.append("进程已死亡")
    if gpus and "error" not in gpus[0] and all(g["util"] < 5 for g in gpus):
        critical.append("所有GPU利用率为0")
    if log_info.get("issues"):
        critical.extend(log_info["issues"])

    if critical:
        lines.append(f"[综合判断] 🚨 CRITICAL: {', '.join(critical)}")
    else:
        lines.append("[综合判断] ✅ 训练运行正常")

    lines.append("=== END ===")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="训练状态监控")
    parser.add_argument("--pid", type=int, help="训练进程 PID")
    parser.add_argument("--log", type=str, help="训练日志文件路径")
    parser.add_argument("--disk", type=str, default=".", help="检查磁盘的路径")
    parser.add_argument("--tail", type=int, default=50, help="读取 log 末尾行数")
    args = parser.parse_args()

    pid_info = check_process(args.pid) if args.pid else None
    gpus = check_gpu()
    log_info = check_log(args.log, args.tail) if args.log else {"error": "未指定 log 文件"}
    disk_info = check_disk(args.disk)

    summary = format_summary(pid_info, gpus, log_info, disk_info)
    print(summary)


if __name__ == "__main__":
    main()
