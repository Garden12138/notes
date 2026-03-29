---
name: openclaw-telegram-cron-delivery
description: Create reliable exact-time Telegram cron pushes in OpenClaw. Use when a scheduled job must run at a precise time, send the final summary text to a specific Telegram numeric chatId, and avoid ambiguous session-based routing such as current/last/main fallback.
---

# OpenClaw Telegram Cron Delivery

Use this skill when building scheduled Telegram push jobs in OpenClaw.

## Recommended implementation

Prefer a **single isolated cron job** with explicit Telegram delivery.

Use this stable pattern:
- `--session isolated`
- `--cron ...`
- `--tz <iana>`
- `--exact`
- `--announce`
- `--channel telegram`
- `--to <numeric_chat_id>`
- `--expect-final`
- prompt must require **final user-facing summary only**

## Canonical command

```bash
openclaw cron add \
  --name "oc-watch-telegram-direct" \
  --agent oc-watch \
  --session isolated \
  --cron "0 9,21 * * *" \
  --tz Asia/Shanghai \
  --exact \
  --announce \
  --channel telegram \
  --to 8667319381 \
  --expect-final \
  --message "执行 openclaw/openclaw 更新监控。先读取本 workspace 的历史记录/记忆，避免重复播报；只输出新增或明显变化。最终只输出面向用户的一条最终摘要，格式固定为：1) 今日是否有新版本 2) 新增/值得关注的 PR 3) 对我现有 Telegram 多 agent 部署的潜在影响 4) 建议是否需要手动升级/继续观察。不要输出过程日志，不要额外寒暄。"
```

## Prompt rules

The cron prompt must:
- require **final summary text only**
- forbid process narration
- forbid tool/debug logs
- forbid prompt echo
- define the final structure clearly
- return `NO_REPLY` when there is no meaningful update

Good prompt ingredients:
- “最终只输出面向用户的一条最终摘要”
- “不要输出过程日志，不要额外寒暄”
- “如果没有新增或高价值变化，回复：NO_REPLY”

## Scheduling rules

When the user wants exact local-time execution:
- always set `--tz <iana>`
- always set `--exact`

Example:
- `--cron "0 9,21 * * *" --tz Asia/Shanghai --exact`

## Delivery rules

For Telegram cron pushes:
- use `--channel telegram`
- use a **numeric** `--to <chatId>`
- prefer explicit chat IDs over inferred routing

## Build rules

When iterating on delivery behavior:
1. keep only one active test job at a time
2. remove old test cron jobs before trying a new approach
3. validate with a manual run before trusting the schedule

Useful commands:

```bash
openclaw cron list --json
openclaw cron run <job-id>
openclaw cron runs --id <job-id> --expect-final
openclaw cron rm <job-id>
```

## Scope

Use this skill for:
- scheduled Telegram summaries
- update watchers
- alerts
- recurring bot push jobs that must reach a specific Telegram chat

If you need a fuller implementation example, read `references/production-template.md`.
