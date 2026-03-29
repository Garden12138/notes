# Production Template: OpenClaw Telegram Cron Delivery

Use this reference when you want a reusable production pattern for Telegram scheduled pushes.

## Goal

Run a cron job at exact local times and deliver the final summary text directly to a Telegram numeric chatId.

## Template command

```bash
openclaw cron add \
  --name "<job-name>" \
  --agent <agent-id> \
  --session isolated \
  --cron "<cron-expr>" \
  --tz <iana-timezone> \
  --exact \
  --announce \
  --channel telegram \
  --to <numeric-chat-id> \
  --expect-final \
  --message "<final-user-facing-task-prompt>"
```

## Field guide

### `<job-name>`
Use a stable, descriptive name.

Examples:
- `oc-watch-telegram-direct`
- `daily-ops-report-telegram`
- `build-alert-telegram`

### `<agent-id>`
Use the agent that owns the relevant workspace and memory.

Examples:
- `oc-watch`
- `main`
- `ops`

### `<cron-expr>`
Examples:
- `0 9,21 * * *` → every day at 09:00 and 21:00
- `0 8 * * 1-5` → weekdays at 08:00
- `30 18 * * 1` → Mondays at 18:30

### `<iana-timezone>`
Examples:
- `Asia/Shanghai`
- `America/New_York`
- `Europe/Berlin`

### `<numeric-chat-id>`
Use the Telegram numeric chat id, not a username.

### `<final-user-facing-task-prompt>`
Write the prompt so the final output is already suitable for delivery.

Required properties:
- tell the agent exactly what to check
- tell it to consult history/memory first if dedupe matters
- tell it to output only the final summary
- forbid logs, reasoning, and prompt restatement
- define exact response structure
- define `NO_REPLY` behavior when appropriate

## Suggested prompt skeleton

```text
执行 <task>。
先读取相关历史记录/记忆，避免重复推送。
只输出新增或高价值变化。
最终只输出一条面向用户的最终摘要。
输出格式固定为：
1) ...
2) ...
3) ...
4) ...
不要输出过程日志，不要额外寒暄。
如果没有新增或高价值变化，回复：NO_REPLY。
```

## Validation flow

After creating the job:

```bash
openclaw cron list --json
```

Confirm:
- `sessionTarget: isolated`
- `channel: telegram`
- `to: <numeric-chat-id>`
- expected cron expression
- expected timezone
- stagger disabled

Then test:

```bash
openclaw cron run <job-id>
openclaw cron runs --id <job-id> --expect-final
```

Check:
- run status is `ok`
- delivery status is `delivered`
- Telegram receives the final summary text

## Iteration rule

Before trying a revised version:
- remove or disable the previous test job
- keep the environment clean
- compare only one delivery strategy at a time
