# Train Watch 🌙 - 赛博监工

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### The Problem

You start training at 11 PM. You go to sleep. You wake up at 8 AM.

**The training crashed at 2 AM.**

You want to kill someone.

### The Solution

**Train Watch** — Your AI training supervisor that never sleeps.

- 🤖 Powered by Claude Code
- 🔄 Checks every N minutes (you decide)
- 🚨 Auto-detects crashes, OOM, NaN, GPU hangs
- 🔧 Auto-fixes and restarts when possible
- 📝 Logs everything for morning review

### How It Works

```bash
# 1. Start your training with Claude Code
claude
> "Help me run this training"

# 2. Launch the watchdog (it will monitor in background)
./watchdog.sh --session <your-session-id> --pid <training-pid> --log train.log

# 3. Go to sleep

# 4. Wake up, resume your session
claude --resume <your-session-id>
> "What happened overnight?"
```

Claude will tell you everything: how many checks, any issues found, what actions were taken.

### What It Monitors

- ✅ Process alive/dead
- ✅ GPU utilization (detects hangs)
- ✅ Log errors (NaN, Inf, OOM, exceptions)
- ✅ Loss trends
- ✅ Disk space

### Installation

```bash
git clone https://github.com/yourusername/train-watch.git
cd train-watch
chmod +x watchdog.sh
```

Requirements:
- Claude Code CLI installed
- Python 3.7+
- nvidia-smi (for GPU monitoring)

### Usage

**⚠️ IMPORTANT: Safety First**

Before using Train Watch:
1. **Backup your code** - Commit and push all changes
2. **Use `/branch` to fork your session** - This keeps your main conversation clean and allows rollback
3. **Test on non-critical experiments first** - Make sure it works as expected
4. **Review the auto-fix logic** - Claude will attempt to fix issues automatically with `--dangerously-skip-permissions`

**Disclaimer**: This tool gives Claude Code autonomous control over your training process. While it's designed to help, it may make mistakes. Use at your own risk. Always have backups.

---

**Step 1**: Copy `CLAUDE.md` to your training project root

**Step 2**: Start training with Claude Code and **fork the session**
```bash
cd /your/training/project
claude
```

In the conversation:
```
You: /branch
Claude: [creates a branch]
You: Help me run train.py with these configs
Claude: [starts training, tells you PID and session ID]
```

**Why fork?** This keeps your main conversation history clean and lets you return to the original session if needed.

**Step 3**: Launch watchdog with the **branched session ID**
```bash
nohup ./watchdog.sh --session <session-id> --pid <pid> --log train.log > watchdog.out 2>&1 &
```

**Step 4**: Sleep peacefully 😴

**Step 5**: Morning review
```bash
claude --resume <session-id>
```

Or just read `.train_status.log`:
```bash
cat .train_status.log
```

### Configuration

```bash
./watchdog.sh \
  --session <claude-session-id>  # Required
  --pid <training-pid>            # Optional but recommended
  --log <log-file>                # Optional but recommended
  --interval 1800                 # Check interval in seconds (default: 30min)
  --disk /path/to/check           # Disk path to monitor (default: .)
```

### Stopping the Watchdog

```bash
kill $(cat .watchdog.pid)
```

### Example Log

```
[2026-03-26 03:00:01] ✅ OK — 进程存活，GPU 利用率 94%，loss 0.342，无异常
[2026-03-26 03:30:01] 🚨 CRITICAL — 进程已死亡，原因：CUDA OOM。已将 batch_size 从 128 改为 64，已重启，新 PID 45231
[2026-03-26 04:00:01] ✅ OK — 进程存活（PID 45231），GPU 利用率 91%，loss 0.318，恢复正常
```

### Why This Exists

Claude Code and Codex are amazing, but they lack one critical feature: **heartbeat monitoring**.

When you're running overnight experiments, you need an agent that:
- Actively checks status (not passively waiting for you to ask)
- Takes action when things go wrong (not just notifying you)
- Works while you sleep (because 2 AM crashes are the worst)

This is that missing piece.

### Contributing

PRs welcome! Especially for:
- Better error detection patterns
- Auto-fix strategies for common issues
- Support for other training frameworks

### License

MIT

---

<a name="中文"></a>
## 中文

### 问题

晚上 11 点开始训练。你去睡觉。早上 8 点醒来。

**训练在凌晨 2 点崩了。**

你想杀人。

### 解决方案

**Train Watch** — 永不睡觉的 AI 训练监工。

- 🤖 基于 Claude Code
- 🔄 每 N 分钟检查一次（你决定）
- 🚨 自动检测崩溃、OOM、NaN、GPU 卡死
- 🔧 可能的话自动修复并重启
- 📝 记录所有事件供早晨查看

### 工作原理

```bash
# 1. 用 Claude Code 启动训练
claude
> "帮我跑这个训练"

# 2. 启动 watchdog（后台监控）
./watchdog.sh --session <你的session-id> --pid <训练进程PID> --log train.log

# 3. 去睡觉

# 4. 醒来后恢复会话
claude --resume <你的session-id>
> "昨晚发生了什么？"
```

Claude 会告诉你一切：检查了几次、发现了什么问题、采取了什么行动。

### 监控内容

- ✅ 进程存活状态
- ✅ GPU 利用率（检测卡死）
- ✅ 日志错误（NaN、Inf、OOM、异常）
- ✅ Loss 趋势
- ✅ 磁盘空间

### 安装

```bash
git clone https://github.com/yourusername/train-watch.git
cd train-watch
chmod +x watchdog.sh
```

依赖：
- Claude Code CLI
- Python 3.7+
- nvidia-smi（用于 GPU 监控）

### 使用方法

**⚠️ 重要：安全第一**

使用 Train Watch 之前：
1. **备份代码** - 提交并推送所有更改
2. **使用 `/branch` fork 会话** - 保持主对话干净，允许回滚
3. **先在非关键实验上测试** - 确保按预期工作
4. **检查自动修复逻辑** - Claude 会使用 `--dangerously-skip-permissions` 自动修复问题

**免责声明**：此工具赋予 Claude Code 对训练过程的自主控制权。虽然设计用于帮助，但可能会出错。使用风险自负。务必备份。

---

**第 1 步**：将 `CLAUDE.md` 复制到你的训练项目根目录

**第 2 步**：用 Claude Code 启动训练并 **fork 会话**
```bash
cd /your/training/project
claude
```

在对话中：
```
你：/branch
Claude：[创建分支]
你：帮我用这些配置运行 train.py
Claude：[启动训练，告诉你 PID 和 session ID]
```

**为什么要 fork？** 保持主对话历史干净，需要时可以返回原始会话。

**第 3 步**：使用 **分支的 session ID** 启动 watchdog
```bash
nohup ./watchdog.sh --session <session-id> --pid <pid> --log train.log > watchdog.out 2>&1 &
```

**第 4 步**：安心睡觉 😴

**第 5 步**：早晨查看
```bash
claude --resume <session-id>
```

或直接读日志：
```bash
cat .train_status.log
```

### 配置选项

```bash
./watchdog.sh \
  --session <claude-session-id>  # 必需
  --pid <训练进程PID>             # 可选但推荐
  --log <日志文件>                # 可选但推荐
  --interval 1800                 # 检查间隔（秒），默认 30 分钟
  --disk /path/to/check           # 监控的磁盘路径，默认当前目录
```

### 停止 Watchdog

```bash
kill $(cat .watchdog.pid)
```

### 日志示例

```
[2026-03-26 03:00:01] ✅ OK — 进程存活，GPU 利用率 94%，loss 0.342，无异常
[2026-03-26 03:30:01] 🚨 CRITICAL — 进程已死亡，原因：CUDA OOM。已将 batch_size 从 128 改为 64，已重启，新 PID 45231
[2026-03-26 04:00:01] ✅ OK — 进程存活（PID 45231），GPU 利用率 91%，loss 0.318，恢复正常
```

### 为什么做这个

Claude Code 和 Codex 很强大，但缺少一个关键功能：**心跳监控**。

跑通宵实验时，你需要一个能：
- 主动检查状态（而不是被动等你问）
- 出问题时采取行动（而不只是通知你）
- 在你睡觉时工作（因为凌晨 2 点崩溃最要命）

这就是那个缺失的拼图。

### 贡献

欢迎 PR！特别是：
- 更好的错误检测模式
- 常见问题的自动修复策略
- 支持其他训练框架

### 许可证

MIT

---

**Train Watch** — You sleep. I watch. 🌙
