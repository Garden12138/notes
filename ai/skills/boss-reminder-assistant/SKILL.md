---
name: boss-reminder-assistant
description: Build reminder workflows in OpenClaw that schedule Telegram reminders, support one-shot and recurring reminders, and also sync each scheduled reminder into Apple Reminders via a local osascript with different copy for Telegram versus Reminders.
---

# OpenClaw Reminder Assistant

Use this skill when the user wants a reminder bot that:
- sends reminders to Telegram
- supports one-time reminders like “2分钟后提醒我开会” or “今天14:30提醒我做什么”
- supports recurring reminders like “每周几几点提醒我做什么”
- has fixed daily reminder jobs
- syncs reminders into Apple Reminders with a local script

Bundled resources:
- AppleScript: `scripts/add_boss_reminder.scpt`
- examples: `references/examples.md`

## Core rules

1. For every scheduled reminder, treat **Telegram delivery** and **Apple Reminders sync** as two separate outputs.
2. Telegram content should follow the user-facing structured reminder format.
3. Apple Reminders content should be shorter and more direct. Do not copy the Telegram template into Reminders.
4. If the user gave a script path, call that script when creating the reminder so the reminder is also written into Reminders.
5. Use explicit timezone configuration for scheduled jobs.
6. For Telegram delivery, use explicit `--channel`, `--to`, `--account`, and `--session-key` when available.

## User-facing reminder format

Default Telegram output format:
- 标题
- 时间
- 事项
- 优先级
- 是否需要我回复确认

Keep it concise, clear, execution-oriented, and free of chatter.

Example Telegram payload:

```text
标题：提醒
时间：2分钟后
事项：洗杯子
优先级：中
是否需要我回复确认：否
```

## Apple Reminders format

Use short fields:
- title: just the action or a compact reminder title
- datetime: exact local datetime in `YYYY-MM-DD HH:MM`
- list: use the configured list name, or the script default
- notes: short context only

Example:

```bash
osascript ~/.openclaw/scripts/add_boss_reminder.scpt "洗杯子" "2026-04-17 17:40" "老板提醒" "2分钟后"
```

If you need concrete command patterns, read `references/examples.md`.

## Script contract

Example script contract:

```bash
osascript ~/.openclaw/scripts/add_boss_reminder.scpt "标题" "YYYY-MM-DD HH:MM" [列表名] [备注]
```

A reusable copy of this script is bundled at `scripts/add_boss_reminder.scpt`.

If the script defines a default list, you may omit the list name unless the user asked for a specific one.

## One-shot reminder pattern

For one-shot reminders, create the Apple Reminders item and the OpenClaw cron job together.

Pattern:

```bash
osascript ~/.openclaw/scripts/add_boss_reminder.scpt "洗杯子" "2026-04-17 17:40" "老板提醒" "2分钟后" && \
openclaw cron add \
  --agent gardenmacmini_reminder \
  --account gardenmacmini_reminder \
  --channel telegram \
  --to 8667319381 \
  --session-key agent:gardenmacmini_reminder:telegram:direct:8667319381 \
  --at '2m' \
  --name 'wash-cup-reminder-20260417-1738' \
  --description '2分钟后提醒洗杯子' \
  --message '标题：提醒\n时间：2分钟后\n事项：洗杯子\n优先级：中\n是否需要我回复确认：否' \
  --announce \
  --delete-after-run \
  --json
```

Notes:
- `--at` accepts durations like `2m` or an ISO datetime.
- use `--delete-after-run` for one-shot reminders.
- use stable, unique names.

## Recurring reminder pattern

For recurring reminders:
- compute the cron expression correctly
- set `--tz <iana>`
- create the Apple Reminders item only if the user's local workflow expects a matching Reminders entry now
- if the user wants Reminders sync for every scheduled occurrence, you need a cron payload or wrapper that writes to Apple Reminders at trigger time, not just at creation time
- for morning and evening summary jobs, do not rely only on session context, read `memory/*.md` first

Example recurring cron:

```bash
openclaw cron add \
  --agent gardenmacmini_reminder \
  --account gardenmacmini_reminder \
  --channel telegram \
  --to 8667319381 \
  --session-key agent:gardenmacmini_reminder:telegram:direct:8667319381 \
  --cron '0 8 * * *' \
  --tz Asia/Shanghai \
  --name 'daily-morning-todo-reminder' \
  --description '每日早上8点提醒查看今日待办' \
  --message '请按固定格式发送早间提醒...' \
  --announce \
  --json
```

## Daily reminder templates

Morning 08:00 template:
1. 今日核心待办
2. 今日会议/节点
3. 最重要的一件事

Evening 22:00 template:
1. 今天完成了什么
2. 今天未完成什么
3. 明天最优先的三件事

## Memory-first summary rule

For daily morning and evening reminder jobs:
- read recent `memory/*.md` files before composing the message
- treat memory files as the source of truth for completed, delayed, pending, and scheduled items
- use recent conversation only as a secondary supplement when memory is incomplete
- if the reminders become too generic, the likely failure is missing daily memory updates, not prompt wording alone

Recommended daily memory pattern:
- create or append `memory/YYYY-MM-DD.md`
- record reminders created
- record reminders completed
- record delays or reschedules
- record important notes that should appear in the next reminder, such as materials to bring

Example facts to store:
- 15:00 给老板发周报，已完成
- 2026-04-22 10:00 开项目会
- 和老板确认方案从 2026-04-21 18:00 延期到 2026-04-22 12:00
- 备注：带上 PPT 和排期表

## Important implementation detail

If the user's real requirement is:
- send Telegram reminder when the schedule fires, and
- also write into Apple Reminders when the schedule fires

then do not assume that creating the Reminders item once at scheduling time is enough.

You need one of these approaches:
1. a wrapper script or executable that writes to Apple Reminders and then sends or schedules the Telegram reminder
2. a cron payload that triggers an agent/tool flow which writes to Apple Reminders at run time
3. separate paired jobs if the system design requires it

This distinction matters.

## Recommended workflow

1. Parse the reminder request.
2. Determine whether it is one-shot or recurring.
3. Determine the exact local datetime or cron expression.
4. Write Apple Reminders copy separately from Telegram copy.
5. Create the Reminders entry if the workflow calls for creation-time sync.
6. Create the OpenClaw cron job with explicit Telegram routing.
7. Write or update daily memory so future morning and evening summaries can reuse the facts.
8. Return a short structured confirmation.

## Validation checklist

Before finishing:
- correct time parsed
- timezone explicit when needed
- Telegram chat id correct
- agent id correct
- session key correct
- Telegram text is structured for chat
- Apple Reminders title/notes are short and natural
- one-shot jobs use `--delete-after-run`
- daily memory was created or updated when the reminder changes the user's task state

## When to use this skill

Trigger on requests like:
- “几点提醒我做什么”
- “每周几几点提醒我做什么”
- “帮我设置每天早晚提醒”
- “创建 Telegram 提醒并同步到提醒事项”
- “用 OpenClaw 做提醒助手”
