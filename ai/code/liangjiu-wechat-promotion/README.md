# 良久素材微信推广：从空环境到首次 dry-run

这是 2026-07-14 真机实践的公开脱敏包。它同时保留两类文件：

- `practice-snapshot/`：当时实际使用的 Agent、Skills 和场景三/四脚本，只做脱敏，用于复盘；
- 其余文件：审计后补齐数据交接、白名单和 dry-run 残留问题的可部署版。

本文档的完成标准不是“脚本能启动”，而是从一台已登录微信的 iPhone 依次做到：OpenClaw 能发现两个 Skills、WDA 可驱动、iPhone 剪贴板可回传、场景一能定位新品页、场景二能提取一个真实商品、场景三 dry-run 能命中允许群且不发送。

完整业务文章见[使用 OpenClaw + iPhone-use + WDA 实现“良久素材”自动化微信推广](../../Using%20OpenClaw%20iPhone-use%20and%20WDA%20to%20automate%20Liangjiu%20WeChat%20promotion.md)，WDA 基础安装见[在 Mac 上使用 iPhone-use 与 WebDriverAgent](../../Using%20iPhone-use%20and%20WDA%20on%20Mac.md)。

## 文件关系

| 文件 | 用途 |
| --- | --- |
| `openclaw/AGENTS.md`、`TOOLS.md` | 可部署的任务约束与本地工具表 |
| `openclaw/skills/*/SKILL.md` | 完整采集 Skill 与推广 Skill |
| `openclaw/practice-snapshot/` | 实践结束时的原始规则，公开脱敏版 |
| `iphone-use/scripts/wechat-iphone-scenario1-*` | 状态、WDA 启动与新品名称采集 |
| `iphone-use/scripts/select_safe_products.py` | `products.jsonl -> selected-products.txt` |
| `iphone-use/scripts/wechat-iphone-scenario2-*` | 商品详情与链接提取 |
| `iphone-use/scripts/build_verified_promotion.py` | `results.jsonl -> final-promotion.txt` |
| `iphone-use/scripts/wechat-iphone-scenario3-*` | 群允许名单、群名双校验与单次发送 |
| `iphone-use/scripts/wechat-iphone-scenario4-*` | 从最终文案逐链接分享 |
| `iphone-use/scripts/iu_clipboard_relay.py` | iPhone 剪贴板转发到 `/agent/inbox` |
| `iphone-use/patches/setup-wda-269880b.patch` | 本机成功的 WDA 启动修订 |
| `examples/` | 任务上下文、触发语句和文件格式 |
| `evidence/` | 真实运行结果的最小脱敏投影 |
| `tests/` | 不连接手机的静态与数据交接测试 |

## 实测版本基线

| 组件 | 2026-07-14 本机值 | 说明 |
| --- | --- | --- |
| OpenClaw | `2026.6.6 (8c802aa)` | npm 包要求 Node `>=22.19.0` |
| Node | `25.2.1` | 实测值，不是最低要求 |
| iphone-use | `0.4.12`，commit `269880b5e1ddd06c110fad8d7c37643ecc4212e5` | 场景脚本基于该提交 |
| WebDriverAgent | commit `bed8d1e4964a49849c51462b80412359589b7654` | Xcode 工程签名仍需本机配置 |
| macOS / Xcode | `26.5.1` / `26.3` | 实测值 |
| 元素树画布 | `393 × 852` | 坐标基线，不代表所有 iPhone |

先按上述版本复现，再升级单个组件。直接把所有依赖换成 latest，出现 UI 或 CLI 差异时难以定位责任层。

## 1. 安装 OpenClaw 与 iphone-use

安装 Node 后固定 OpenClaw 版本并完成向导：

```bash
npm install -g openclaw@2026.6.6
openclaw onboard --install-daemon
openclaw gateway status --require-rpc
openclaw health --json
```

在新目录克隆已验证的 iphone-use 提交：

```bash
export IPHONE_USE_DIR="$HOME/path/to/iphone-use"
git clone https://github.com/leeguooooo/iphone-use.git "$IPHONE_USE_DIR"
git -C "$IPHONE_USE_DIR" checkout 269880b5e1ddd06c110fad8d7c37643ecc4212e5
```

按基础文章完成 iphone-use 构建、Agent Token、WDA 签名、USB `iproxy` 和 `/agent/status` 验证。微信必须已登录，iPhone 保持解锁；运行 WDA 时退出 Xcode GUI 和 iPhone 镜像，避免争用 XCTest 会话。

## 2. 部署公开脚本与 WDA 补丁

在 notes 仓库根目录执行：

```bash
export KIT_DIR="$PWD/ai/code/liangjiu-wechat-promotion"
mkdir -p "$IPHONE_USE_DIR/scripts" "$IPHONE_USE_DIR/config"

cp "$KIT_DIR"/iphone-use/scripts/* "$IPHONE_USE_DIR/scripts/"
chmod +x "$IPHONE_USE_DIR"/scripts/*.sh "$IPHONE_USE_DIR"/scripts/*.py

cp "$KIT_DIR/iphone-use/config/allowed-groups.json.example" \
  "$IPHONE_USE_DIR/config/allowed-groups.json"
```

编辑 `allowed-groups.json`，把占位符替换为允许发送的完整群名。场景一、三、四都会读取同一份 `groups` 数组；不在名单内时在触碰微信前返回 `GROUP_NOT_ALLOWED`。

本机成功的 `setup-wda.sh` 去掉了 `nohup xcodebuild` 和命令行签名覆盖，使 `xcodebuild` 成为 keeper 的直接子进程，并复用 Xcode 工程内已验证的 Team 与 Bundle ID。补丁只针对上表 commit：

```bash
git -C "$IPHONE_USE_DIR" apply --check \
  "$KIT_DIR/iphone-use/patches/setup-wda-269880b.patch"
git -C "$IPHONE_USE_DIR" apply \
  "$KIT_DIR/iphone-use/patches/setup-wda-269880b.patch"
```

`--check` 失败时不要强行套补丁。先确认 commit，或人工对照当前 `setup-wda.sh` 的 WDA 启动段。基础提交已经包含 `WDA_KEEPALIVE`；场景一会拒绝仍含 `nohup xcodebuild`、签名覆盖或缺少 `WDA_KEEPALIVE` 的版本。

## 3. 配置运行环境

从 `.env.example` 取值，但不要覆盖已有的 OpenClaw 全局 `.env`：

```bash
export OPENCLAW_AGENT_ID="liangjiu-promotion"
export OPENCLAW_WORKSPACE="$HOME/.openclaw/workspace-liangjiu-promotion"
export WECHAT_IPHONE_CONFIG="$IPHONE_USE_DIR/config/allowed-groups.json"
export WECHAT_IPHONE_TARGET_GROUP="<TARGET_WECHAT_GROUP>"
export WDA_TEAM_ID="<APPLE_TEAM_ID>"
export WDA_UDID="<IPHONE_UDID>"
```

OpenClaw Gateway 由 launchd 启动时不一定继承当前终端变量。把这些本地值写入 OpenClaw 的非覆盖 `env.vars`，不要写 Agent Token：

```bash
openclaw config set env.vars.IPHONE_USE_DIR "$IPHONE_USE_DIR"
openclaw config set env.vars.WECHAT_IPHONE_PROJECT_DIR "$IPHONE_USE_DIR"
openclaw config set env.vars.WECHAT_IPHONE_CONFIG "$WECHAT_IPHONE_CONFIG"
openclaw config set env.vars.WECHAT_IPHONE_TARGET_GROUP "$WECHAT_IPHONE_TARGET_GROUP"
openclaw config set env.vars.WDA_TEAM_ID "$WDA_TEAM_ID"
openclaw config set env.vars.WDA_UDID "$WDA_UDID"
openclaw config validate
openclaw gateway restart
```

Token 继续由脚本从 `~/.iphone-use/agent-token` 读取。不要把 Token 放进快捷指令、Skill、`.env.example` 或仓库。

## 4. 创建专用 OpenClaw Agent

```bash
openclaw agents add "$OPENCLAW_AGENT_ID" \
  --workspace "$OPENCLAW_WORKSPACE" \
  --non-interactive \
  --json

install -m 0644 "$KIT_DIR/openclaw/AGENTS.md" "$OPENCLAW_WORKSPACE/AGENTS.md"
install -m 0644 "$KIT_DIR/openclaw/TOOLS.md" "$OPENCLAW_WORKSPACE/TOOLS.md"
mkdir -p "$OPENCLAW_WORKSPACE/skills"
cp -R "$KIT_DIR/openclaw/skills/." "$OPENCLAW_WORKSPACE/skills/"

openclaw agents list --json
openclaw skills list --agent "$OPENCLAW_AGENT_ID" --json
openclaw skills check --agent "$OPENCLAW_AGENT_ID"
```

如果 Agent 已存在，不要重复 `agents add`；只更新该 Agent 的 workspace 文件。Skill 列表必须同时出现：

- `liangjiu-new-products-collection-v1-0-0`
- `liangjiu-wechat-auto-promotion-v1-0-0`

旧会话可能缓存 Skill 列表。更新后开启新会话，或重启 Gateway。

## 5. 配置 iPhone 快捷指令

先启动 iphone-use，再从项目目录启动 Relay：

```bash
cd "$IPHONE_USE_DIR"
python3 scripts/iu_clipboard_relay.py
```

另开终端：

```bash
curl http://127.0.0.1:18080/health
ipconfig getifaddr en0
```

在 iPhone 新建 `IU Clipboard Export`：

1. 添加“获取剪贴板”；
2. 添加“获取 URL 内容”；
3. URL 设为 `http://<MAC_LAN_IP>:18080/clipboard`；
4. 方法选 `POST`，请求体选 `JSON`；
5. 设置 `verb=clipboard_export`、`ok=true`、`text=剪贴板变量`；
6. 不设置 Authorization 或 Agent Token。

Mac 与 iPhone 要在同一可信局域网，并允许“快捷指令”的本地网络权限。Relay 监听 `0.0.0.0:18080` 且 iPhone 到 Relay 这一段没有鉴权；不要做公网端口映射，任务结束后停止 Relay。

验证：

```bash
cd "$IPHONE_USE_DIR/scripts"
./wechat-iphone-scenario2-v13-safe-reset-list-top.sh test-clipboard-bridge \
  --clipboard-shortcut-name "IU Clipboard Export" \
  --shortcut-timeout 25
```

只有脚本读到本次 iPhone 剪贴板文本才算成功。`/health` 成功只证明 Relay 在监听，不证明上游 inbox 已收到。

## 6. 新设备校准

先读取元素树：

```bash
cd "$IPHONE_USE_DIR/scripts"
./wechat-iphone-scenario1-v13-names-only.sh elements > /tmp/iphone-elements.json
```

核对 `screen.width`、`screen.height`，并从目标元素 `rect=[left, top, width, height]` 计算：

```text
x = (left + width / 2) / screen.width
y = (top  + height / 2) / screen.height
```

将新画布和坐标写入 `WECHAT_IPHONE_SCREEN_WIDTH`、`WECHAT_IPHONE_SCREEN_HEIGHT`、`WECHAT_IPHONE_NEW_PRODUCTS_X/Y`。不要直接沿用 `393 × 852` 的兜底坐标。

## 7. 首跑验证阶梯

每一级成功后再进入下一级。

### A. 不连接手机的 smoke test

```bash
cd "$KIT_DIR"
bash tests/smoke.sh
```

预期最后输出 `smoke test passed`。它检查 Shell/Python 语法、两个数据转换 helper 和 Skill 基本结构。

### B. WDA 与手机状态

```bash
cd "$IPHONE_USE_DIR/scripts"
./wechat-iphone-scenario1-v13-names-only.sh status
```

预期 `ready=true`，并满足 `wda_actionable=true`、`wda_locked=false`、`drivable=true`、`mode=agent`。

### C. 只定位新品页

```bash
./wechat-iphone-scenario1-v13-names-only.sh collect-new-products \
  --limit 6 \
  --dry-run
```

预期 `dry_run=true`、`positioned_at="新品首发"`。该命令会操作手机进入新品页，但不采集、不滚动。

### D. 采集与自动选品

```bash
export TASK_ID="liangjiu-promo-$(date +%Y%m%d)-manual-001"
export RUN_DIR="$IPHONE_USE_DIR/runs/$TASK_ID"
mkdir -p "$RUN_DIR"

./wechat-iphone-scenario1-v13-names-only.sh collect-new-products \
  --limit 50 \
  --max-scrolls 20 \
  --skip-open \
  --out-dir "$RUN_DIR/new-products"

python3 ./select_safe_products.py \
  --input "$RUN_DIR/new-products/products.jsonl" \
  --count 6 \
  --output "$RUN_DIR/selected-products.txt" \
  --report "$RUN_DIR/selection.json"
```

核对 `selection.json` 的品类、六个标题和排除原因。任何高风险标题或规格片段进入结果都要先修分类规则，不进入详情。

### E. 单商品详情

先从已核对清单复制一行到 `one-product.txt`，再运行：

```bash
sed -n '1p' "$RUN_DIR/selected-products.txt" > "$RUN_DIR/one-product.txt"

./wechat-iphone-scenario2-v13-safe-reset-list-top.sh promote-products \
  --products-file "$RUN_DIR/one-product.txt" \
  --link-read-mode shortcut \
  --clipboard-shortcut-name "IU Clipboard Export" \
  --shortcut-timeout 25 \
  --skip-open \
  --out-dir "$RUN_DIR/one-product-detail"
```

预期 `success_count=1`，且结果同时有标题、价格、完整链接和 `iphone_shortcut_inbox_received`。规格可能为空；不得补写。

### F. 构建一商品事实文案并 dry-run

```bash
python3 ./build_verified_promotion.py \
  --results "$RUN_DIR/one-product-detail/results.jsonl" \
  --expected-count 1 \
  --output "$RUN_DIR/one-product-promotion.txt"

./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion \
  --group "$WECHAT_IPHONE_TARGET_GROUP" \
  --message-file "$RUN_DIR/one-product-promotion.txt" \
  --dry-run
```

预期 `dry_run=true`、`sent=false`。公开版场景三会先清空输入框再写入，避免上一次 dry-run 草稿叠加。到这里仍未产生群消息。

场景四没有 dry-run。只有明确允许真实分享时才执行 `--max-links 1`；它会真的分享一个链接。

## 8. 通过 OpenClaw 跑完整草稿

使用固定 session key 保持任务上下文：

```bash
export TASK_ID="liangjiu-promo-$(date +%Y%m%d)-001"
export SESSION_KEY="agent:${OPENCLAW_AGENT_ID}:${TASK_ID}"

openclaw agent \
  --agent "$OPENCLAW_AGENT_ID" \
  --session-key "$SESSION_KEY" \
  --message "选择今天的新品，目标群是 <TARGET_WECHAT_GROUP>。先以 draft 模式完成采集、自动安全选品、详情提取和事实文案；回显文案、群名和 task_id，未收到本次确认不得发送。" \
  --json
```

核对 Agent 返回的 `task_id`、品类、商品数、目标群、文案和缺失字段。要正式发送时，在同一 session 明确确认：

```bash
openclaw agent \
  --agent "$OPENCLAW_AGENT_ID" \
  --session-key "$SESSION_KEY" \
  --message "确认发送 task_id=$TASK_ID 的当前 final-promotion.txt 到 <TARGET_WECHAT_GROUP>，发送成功后逐个分享其中链接。若发送结果 uncertain，立即停止，禁止补发和分享。" \
  --json
```

正式场景三每个任务只允许一次。退出码 2 或 `sent=true` 但证据不足都属于 `uncertain`，不能重跑。

## 常见阻塞

| 现象 | 处理 |
| --- | --- |
| `WDA_SCRIPT_NOT_PATCHED` | 核对 commit 和 WDA 补丁，不绕过校验 |
| `PHONE_CONTROLLER_BUSY` | 核对锁内 PID；进程仍在时等待 |
| `GROUP_ALLOWLIST_NOT_FOUND` | 设置 `WECHAT_IPHONE_CONFIG` 或部署 config 文件 |
| `GROUP_NOT_ALLOWED` | 核对完整群名和 `groups` 数组，不临时放宽匹配 |
| Relay `502` | 检查 iphone-use、Token 文件和 `/agent/inbox` |
| 快捷指令超时 | 检查局域网权限、编辑器运行按钮、请求体 `text` 变量 |
| `PRODUCT_NOT_FOUND` | 保留失败结果，同品类补位一次，不点相似标题 |
| `VERIFIED_PRODUCTS_NOT_ENOUGH` / `TOO_MANY` | 不生成正式文案，不发送 |
| 场景三 `uncertain` | 人工查看群聊，禁止自动补发 |

## 公开脱敏范围

公开包不含用户名路径、真实 Agent 名、群名、Team ID、UDID、Token、WDA Bundle ID、局域网地址、历史完整文案或完整小程序链接。真实元素树可能含聊天内容，不随包发布。
