# Examples

## 1. 一次性提醒，2分钟后提醒洗杯子

Apple Reminders:

```bash
osascript ~/.openclaw/scripts/add_boss_reminder.scpt "洗杯子" "2026-04-17 17:40" "老板提醒" "2分钟后"
```

OpenClaw cron:

```bash
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

## 2. 今天 14:30 提醒接待高育良书记

Apple Reminders:

```bash
osascript ~/.openclaw/scripts/add_boss_reminder.scpt "接待高育良书记" "2026-04-17 14:30" "老板提醒" "今天 14:30"
```

OpenClaw cron:

```bash
openclaw cron add \
  --agent gardenmacmini_reminder \
  --account gardenmacmini_reminder \
  --channel telegram \
  --to 8667319381 \
  --session-key agent:gardenmacmini_reminder:telegram:direct:8667319381 \
  --at '2026-04-17T14:30:00+08:00' \
  --name 'reception-reminder-20260417-1430' \
  --description '今天14:30提醒接待高育良书记' \
  --message '标题：接待提醒\n时间：今天 14:30\n事项：接待高育良书记\n优先级：高\n是否需要我回复确认：否' \
  --announce \
  --delete-after-run \
  --json
```

## 3. 每日 08:00 待办提醒

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
  --message '请按以下格式发送早间提醒：\n- 标题\n- 时间\n- 事项\n- 优先级\n- 是否需要我回复确认\n\n内容模板：\n1. 今日核心待办\n2. 今日会议/节点\n3. 最重要的一件事\n\n要求：简洁、清晰、不闲聊、以执行为主。' \
  --announce \
  --json
```

## 4. 每日 22:00 晚间复盘提醒

```bash
openclaw cron add \
  --agent gardenmacmini_reminder \
  --account gardenmacmini_reminder \
  --channel telegram \
  --to 8667319381 \
  --session-key agent:gardenmacmini_reminder:telegram:direct:8667319381 \
  --cron '0 22 * * *' \
  --tz Asia/Shanghai \
  --name 'daily-evening-review-reminder' \
  --description '每日晚上10点提醒复盘并整理明天待办' \
  --message '请按以下格式发送晚间提醒：\n- 标题\n- 时间\n- 事项\n- 优先级\n- 是否需要我回复确认\n\n内容模板：\n1. 今天完成了什么\n2. 今天未完成什么\n3. 明天最优先的三件事\n\n要求：简洁、清晰、不闲聊、以执行为主。' \
  --announce \
  --json
```

## 5. 给其他机器迁移时的建议

- 将 `scripts/add_boss_reminder.scpt` 复制到目标机器的 `~/.openclaw/scripts/`。
- 先用 `osascript` 单独测试提醒事项写入是否正常。
- 再创建 OpenClaw cron。
- 如果需求是“触发时同时发 Telegram 和写入 Reminders”，需要用运行时脚本或包装器，而不是只在创建时写一次 Reminders。
