# 有赞商城 A 微信推广：从空环境到首次 dry-run

这个目录同时保留两类文件：

- `openclaw/AGENTS.md`、三个 Skills 和 `iphone-use/scripts/wechat-iphone` 是 2026-07-14 实际工作区的公开脱敏快照；
- 环境样例、WDA 补丁、任务门禁和 smoke test 是复现审计后补充的加固层。

完成标准依次是：专用 Agent 能发现三个 Skills，浏览器能接管已登录的有赞会话，WDA 状态可驱动，微信群在 allowlist 中，dry-run 找到发送元素但没有点击。正式发送必须另行授权。

完整业务分析见[使用 OpenClaw + iPhone-use + WDA 实现有赞商城 A 自动化微信推广](../../Using%20OpenClaw%20iPhone-use%20and%20WDA%20to%20automate%20Youzan%20WeChat%20promotion.md)，WDA 基础安装见[在 Mac 上使用 iPhone-use 与 WebDriverAgent](../../Using%20iPhone-use%20and%20WDA%20on%20Mac.md)。

## 文件关系

| 文件 | 性质 | 用途 |
| --- | --- | --- |
| `openclaw/AGENTS.md` | 实践快照 | 专用 Agent 的授权、阶段和停止规则 |
| `openclaw/skills/*/SKILL.md` | 实践快照 | 选品上架、链接生成和总流程 |
| `iphone-use/scripts/wechat-iphone` | 实践快照 | 手机状态、WDA、群校验、草稿检查和发送 |
| `iphone-use/config/allowed-groups.json.example` | 脱敏配置 | 群聊 allowlist 格式 |
| `iphone-use/patches/setup-wda-269880b.patch` | 复现加固 | 本机成功启动 WDA 的最小修订 |
| `iphone-use/scripts/run-wechat-task.sh` | 复现加固 | 任务证据隔离和持久化 send-once 门禁 |
| `.env.example` | 复现加固 | Gateway 与手机脚本所需环境变量 |
| `examples/` | 复现加固 | 任务 JSON 与 OpenClaw 触发语句 |
| `tests/smoke.sh` | 复现加固 | 不连接浏览器和手机的离线测试 |

原始 `wechat-iphone` 的 `controller.lock` 只阻止同一状态目录中的并发进程；`AGENTS.md` 和主 Skill 负责单次运行的 send once。新增 `run-wechat-task.sh` 在任务目录创建 `send-invoked`，补上跨进程、跨重启的持久门禁。它没有改写原脚本。

## 实测版本基线

| 组件 | 2026-07-14 实测值 | 复现要求 |
| --- | --- | --- |
| OpenClaw | `2026.6.6 (8c802aa)` | npm 包要求 Node `>=22.19.0` |
| Node | `25.2.1` | 实测值，不是最低版本 |
| iphone-use | `0.4.12`，commit `269880b5e1ddd06c110fad8d7c37643ecc4212e5` | 先固定提交再应用补丁 |
| WebDriverAgent | commit `bed8d1e4964a49849c51462b80412359589b7654` | Team 与 Bundle ID 在 Xcode 本机配置 |
| macOS / Xcode | `26.5.1` / `26.3` | 其他版本需重新验证签名和 XCTest |
| iPhone 元素树画布 | `393 × 852` | 仅为实测设备坐标基线 |

先复现版本基线，再逐项升级。Node、OpenClaw、iOS 和微信同时变化时，很难判断故障发生在哪一层。

## 1. 安装 OpenClaw 与 iphone-use

先确认当前终端的 Node。`openclaw` 可能安装在新 Node 下，PATH 却仍指向旧 Node：

```bash
node --version
type -a node openclaw
```

确保 Node 不低于 `22.19.0`，再固定 OpenClaw 版本：

```bash
npm install -g openclaw@2026.6.6
hash -r
openclaw --version
openclaw onboard --install-daemon
openclaw gateway status --require-rpc
openclaw health --json
```

如果交互终端正常、Gateway 却启动失败，检查 launchd 使用的 Node 路径，不要在旧 Node 下反复重装 OpenClaw。

克隆并固定 iphone-use：

```bash
export IPHONE_USE_DIR="$HOME/path/to/iphone-use"
git clone https://github.com/leeguooooo/iphone-use.git "$IPHONE_USE_DIR"
git -C "$IPHONE_USE_DIR" checkout 269880b5e1ddd06c110fad8d7c37643ecc4212e5
```

然后按基础文章完成以下门槛：

- iphone-use daemon 可通过 `http://127.0.0.1:44321` 访问；
- Agent Token 只存放在 `$HOME/.iphone-use/agent-token`；
- WDA 已在 Xcode 使用本机 Team 和唯一 Bundle ID 签名；
- USB `iproxy` 可访问 `http://127.0.0.1:8100/status`；
- `/agent/status` 返回 `drivable=true`、`mode=agent`。

## 2. 应用本机验证过的 WDA 启动修订

实测修订让 `xcodebuild` 成为 keeper 的直接子进程，并复用 Xcode 工程内的有效签名，不再从命令行覆盖 Team 和 Bundle ID。补丁只对应上表 iphone-use commit：

在 notes 仓库根目录执行：

```bash
export KIT_DIR="$PWD/ai/code/youzan-wechat-promotion"

git -C "$IPHONE_USE_DIR" apply --check \
  "$KIT_DIR/iphone-use/patches/setup-wda-269880b.patch"
git -C "$IPHONE_USE_DIR" apply \
  "$KIT_DIR/iphone-use/patches/setup-wda-269880b.patch"
```

`--check` 失败时先核对 commit 和本地修改，不要强行套补丁。启动 WDA 前退出 Xcode GUI、iPhone 镜像和其他占用 XCTest/CoreDevice 的进程。

## 3. 创建专用 Agent 并部署快照

从 `.env.example` 复制本机值到私有 shell 配置，不要提交真实值：

```bash
export OPENCLAW_AGENT_ID="<AGENT_NAME>"
export OPENCLAW_WORKSPACE="$HOME/.openclaw/workspace-youzan-promotion"
export WECHAT_IPHONE_CONFIG="$OPENCLAW_WORKSPACE/skills/wechat-iphone/config/allowed-groups.json"
export WECHAT_IPHONE_TARGET_GROUP="<TARGET_WECHAT_GROUP>"
export WDA_TEAM_ID="<APPLE_TEAM_ID>"
export WDA_UDID="<IPHONE_UDID>"
```

先检查 Agent 是否已存在；仅在不存在时创建：

```bash
openclaw agents list --json
openclaw agents add "$OPENCLAW_AGENT_ID" \
  --workspace "$OPENCLAW_WORKSPACE" \
  --non-interactive \
  --json
```

部署 Agent、Skills、脚本和 allowlist：

```bash
install -d "$OPENCLAW_WORKSPACE/skills" \
  "$OPENCLAW_WORKSPACE/skills/wechat-iphone/scripts" \
  "$OPENCLAW_WORKSPACE/skills/wechat-iphone/config"

install -m 0644 "$KIT_DIR/openclaw/AGENTS.md" \
  "$OPENCLAW_WORKSPACE/AGENTS.md"
cp -R "$KIT_DIR/openclaw/skills/." "$OPENCLAW_WORKSPACE/skills/"
install -m 0755 "$KIT_DIR/iphone-use/scripts/wechat-iphone" \
  "$OPENCLAW_WORKSPACE/skills/wechat-iphone/scripts/wechat-iphone"
install -m 0755 "$KIT_DIR/iphone-use/scripts/run-wechat-task.sh" \
  "$OPENCLAW_WORKSPACE/skills/wechat-iphone/scripts/run-wechat-task.sh"
install -m 0644 "$KIT_DIR/iphone-use/config/allowed-groups.json.example" \
  "$OPENCLAW_WORKSPACE/skills/wechat-iphone/config/allowed-groups.json"
```

编辑 `allowed-groups.json`，把占位符替换为唯一允许群的完整名称。不要使用关键词、前缀或模糊匹配。

检查 Skill 发现结果：

```bash
openclaw skills list --agent "$OPENCLAW_AGENT_ID" --json
openclaw skills check --agent "$OPENCLAW_AGENT_ID"
```

列表应包含三个 `youzan-*` Skill。`wechat-iphone` 是脚本依赖，没有 `SKILL.md`，不应被误报为缺失 Skill。

## 4. 把运行变量交给 Gateway

launchd 启动的 Gateway 不保证继承当前终端的 `export`。把非密钥环境值写入 OpenClaw 配置：

```bash
openclaw config set env.vars.WECHAT_IPHONE_PROJECT_DIR "$IPHONE_USE_DIR"
openclaw config set env.vars.WECHAT_IPHONE_CONFIG "$WECHAT_IPHONE_CONFIG"
openclaw config set env.vars.WECHAT_IPHONE_TARGET_GROUP "$WECHAT_IPHONE_TARGET_GROUP"
openclaw config set env.vars.WDA_TEAM_ID "$WDA_TEAM_ID"
openclaw config set env.vars.WDA_UDID "$WDA_UDID"
openclaw config set env.vars.WECHAT_TASK_ROOT "$HOME/.iphone-use/wechat-iphone/tasks"
openclaw config validate
openclaw gateway restart
openclaw gateway status --require-rpc
```

Agent Token 不写入 OpenClaw 配置。原脚本按 `WECHAT_IPHONE_TOKEN_FILE` 或默认路径读取 Token 文件。

## 5. 接管已登录的有赞浏览器会话

有赞 Skill 依赖当前登录态、CSRF 和页面 DOM，不能在全新无登录浏览器中直接执行。实测使用 OpenClaw 的 `user` profile 接管本机 Chrome 会话：

1. 使用 Chrome 144 或更高版本打开 `chrome://inspect/#remote-debugging`，启用远程调试；
2. 在同一个 Chrome 配置中手工登录有赞商城 A；
3. 保持 Chrome 运行；首次连接出现授权提示时人工批准；
4. 不把账号、密码或验证码交给 Agent。

配置并验证：

```bash
openclaw config set browser.enabled true
openclaw config set browser.defaultProfile user
openclaw config validate
openclaw gateway restart

openclaw browser --browser-profile user start
openclaw browser --browser-profile user status
openclaw browser --browser-profile user tabs
openclaw browser --browser-profile user snapshot --format ai
```

成功门槛是 `driver=existing-session`、`transport=chrome-mcp`、`running=true`，并能从 tabs/snapshot 识别当前有赞页面。只看到浏览器进程不算接管成功。

## 6. 离线 smoke test

不连接有赞和手机，先检查 Shell 语法、命令帮助、报告字段和持久化 send-once：

```bash
cd "$KIT_DIR"
bash tests/smoke.sh
```

预期最后一行是 `smoke test passed`。测试使用假手机命令，不会访问真实微信。

## 7. 启动手机栈并校准坐标

定义脚本路径，避免假设 `wechat-iphone` 已加入 PATH：

```bash
export WECHAT_IPHONE="$OPENCLAW_WORKSPACE/skills/wechat-iphone/scripts/wechat-iphone"
export WECHAT_TASK_RUNNER="$OPENCLAW_WORKSPACE/skills/wechat-iphone/scripts/run-wechat-task.sh"

"$WECHAT_IPHONE" doctor
"$WECHAT_IPHONE" start
"$WECHAT_IPHONE" status
```

`status.ready` 必须为 `true`；嵌套状态同时满足：

```json
{
  "ok": true,
  "wda": true,
  "wda_actionable": true,
  "wda_locked": false,
  "drivable": true,
  "mode": "agent"
}
```

新设备不能直接沿用快照坐标。手工把微信依次放到聊天列表、搜索结果页和目标群输入页，每一步读取元素树：

```bash
"$WECHAT_IPHONE" elements > /tmp/iphone-elements.json
```

从元素的 `rect=[left, top, width, height]` 与画布尺寸计算归一化中心：

```text
x = (left + width / 2) / screen.width
y = (top  + height / 2) / screen.height
```

依次校准搜索框、第一条搜索结果和消息输入框，并写入 `WECHAT_IPHONE_SEARCH_X/Y`、`WECHAT_IPHONE_FIRST_RESULT_X/Y`、`WECHAT_IPHONE_INPUT_X/Y`。每次手工切换页面后重新执行 `elements`，不要从同一棵元素树猜三个位置。先在测试账号验证坐标，不用真实群做探针。

将 `.env.example` 中六个坐标改成实测值并导出；需要 OpenClaw 直接操作手机时，再同步给 Gateway：

```bash
openclaw config set env.vars.WECHAT_IPHONE_SEARCH_X "$WECHAT_IPHONE_SEARCH_X"
openclaw config set env.vars.WECHAT_IPHONE_SEARCH_Y "$WECHAT_IPHONE_SEARCH_Y"
openclaw config set env.vars.WECHAT_IPHONE_FIRST_RESULT_X "$WECHAT_IPHONE_FIRST_RESULT_X"
openclaw config set env.vars.WECHAT_IPHONE_FIRST_RESULT_Y "$WECHAT_IPHONE_FIRST_RESULT_Y"
openclaw config set env.vars.WECHAT_IPHONE_INPUT_X "$WECHAT_IPHONE_INPUT_X"
openclaw config set env.vars.WECHAT_IPHONE_INPUT_Y "$WECHAT_IPHONE_INPUT_Y"
openclaw config validate
openclaw gateway restart
```

## 8. 首次手机 dry-run

准备一条不含换行的测试文案：

```bash
export DRY_TASK_ID="youzan-promo-dry-<YYYYMMDD>-001"
printf '%s\n' '测试文案 <PRODUCT_LINK>' > /tmp/youzan-promotion.txt

"$WECHAT_TASK_RUNNER" \
  --task-id "$DRY_TASK_ID" \
  --mode preflight

"$WECHAT_TASK_RUNNER" \
  --task-id "$DRY_TASK_ID" \
  --mode dry-run \
  --group "$WECHAT_IPHONE_TARGET_GROUP" \
  --message-file /tmp/youzan-promotion.txt
```

预期报告分别为 `PREFLIGHT_READY` 和 `DRY_RUN_READY`。dry-run 会打开群聊、输入文案并定位发送元素，但不点击；草稿会留在输入框。正式任务必须重新预检，并让脚本判断草稿为 `exact`、`duplicate`、`different` 或 `unknown`。

证据位于：

```text
$HOME/.iphone-use/wechat-iphone/tasks/<TASK_ID>/
├── task.json
├── send-invoked/
│   └── marker.json
└── invocations/<RUN_ID>/
    ├── message.txt
    ├── wechat-result.json
    ├── wechat.log
    ├── report.json
    └── state/
```

dry-run 没有 `send-invoked/`；正式发送在调用原脚本前创建该目录。即使进程超时或验证不完整，同一 `task_id` 也不能再次发送。

## 9. 先让 OpenClaw 完成业务草稿

使用固定 session key 保存同一业务任务上下文：

```bash
export TASK_ID="youzan-promo-<YYYYMMDD>-001"
export SESSION_KEY="agent:${OPENCLAW_AGENT_ID}:${TASK_ID}"

openclaw agent \
  --agent "$OPENCLAW_AGENT_ID" \
  --session-key "$SESSION_KEY" \
  --message "$(<"$KIT_DIR/examples/openclaw-trigger-draft.txt")" \
  --json
```

人工核对返回的商品身份、全部 SKU、新售价、保存结果、链接 alias/path 和单行文案。遇到验证码、店铺不一致、商品字段矛盾或链接错配时停止；不要通过调整提示词要求 Agent 绕过。

首次正式发送建议把已核对文案写入文件，再由任务门禁执行：

```bash
export SEND_TASK_ID="youzan-promo-send-<YYYYMMDD>-001"

"$WECHAT_TASK_RUNNER" \
  --task-id "$SEND_TASK_ID" \
  --mode preflight

"$WECHAT_TASK_RUNNER" \
  --task-id "$SEND_TASK_ID" \
  --mode send \
  --group "$WECHAT_IPHONE_TARGET_GROUP" \
  --message-file /tmp/youzan-promotion.txt
```

这一步会产生真实群消息。只有 `SUCCESS` 表示 `sent=true, verified=true`；`SENT_UNVERIFIED` 的退出码是 2，仍按可能已经发送处理，禁止重试、WDA 补点或坐标补点。

若要求 OpenClaw 在同一 session 的下一轮直接发送，使用 `examples/openclaw-trigger-send.txt` 明确授权。原始 Agent 会直接调用 `wechat-iphone send`，send once 依赖 `AGENTS.md` 和主 Skill；它不会自动使用新增任务门禁。

## 10. 定时和上线门槛

当前公开快照没有商品推广账本，也没有持久任务队列。Cron 只能先触发 `draft`：

```cron
PATH=/absolute/path/to/node/bin:/usr/bin:/bin
30 10 * * 1-5 openclaw agent --agent "<AGENT_NAME>" --message "为有赞商城 A 创建新推广任务，模式=draft；不得发送。"
```

定时环境必须显式使用前文验证过的 Node/OpenClaw 路径。在自动定时发送前，至少补齐商品 alias、推广链接摘要、目标群、`send_invoked`、`sent`、`verified` 和完成时间的持久记录，并完成不少于 20 次 dry-run、10 次人工监督的正式发送。任一正式发送结果不确定，都要先解决根因再恢复计划任务。

## 常见阻塞

| 现象 | 判断与处理 |
| --- | --- |
| `openclaw` 报 Node 版本过低 | `type -a node openclaw`，统一终端和 Gateway 的 Node 路径 |
| Skills 不完整 | 确认 workspace 路径，重启 Gateway 或开启新会话 |
| 浏览器没有有赞标签页 | 启用 Chrome 远程调试，使用 `user` profile，手工完成登录 |
| `WDA_SCRIPT_NOT_PATCHED` | 核对 iphone-use commit 和补丁，不绕过检查 |
| `PHONE_CONTROLLER_BUSY` | 检查持锁进程；仍在运行时等待 |
| `GROUP_NOT_ALLOWED` | 修正完整群名和 allowlist，不放宽为模糊匹配 |
| `DRAFT_MESSAGE_CONFLICT` | 人工清理草稿，使用新任务重新预检 |
| `SEND_ALREADY_INVOKED` | 当前任务已消耗发送机会，不删除 marker 重跑 |
| `SENT_UNVERIFIED` | 人工查看群聊并记录，禁止自动补发 |

## 公开脱敏范围

公开包不含真实用户名、绝对路径、Agent 名、群名、Team ID、UDID、Token、WDA Bundle ID、商品链接、聊天内容或完整运行证据。脚本中的环境默认值已替换为占位符；业务规则和错误处理未改写。
