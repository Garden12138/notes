#!/usr/bin/env bash
# wechat-iphone — high-level WeChat automation over iphone-use + WDA
# macOS / Bash 3.2 compatible

set -uo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
STATE_DIR="${WECHAT_IPHONE_STATE_DIR:-$HOME/.iphone-use/wechat-iphone}"
TOKEN_FILE="${WECHAT_IPHONE_TOKEN_FILE:-$HOME/.iphone-use/agent-token}"
HOST="${WECHAT_IPHONE_HOST:-http://127.0.0.1:44321}"
WDA_URL="${WECHAT_IPHONE_WDA_URL:-http://127.0.0.1:8100}"
APP_BUNDLE="${WECHAT_IPHONE_APP_BUNDLE:-com.tencent.xin}"
DAEMON_LABEL="${WECHAT_IPHONE_DAEMON_LABEL:-com.leeguoo.iphone-use}"
DAEMON_PLIST="${WECHAT_IPHONE_DAEMON_PLIST:-$HOME/Library/LaunchAgents/com.leeguoo.iphone-use.plist}"
DAEMON_APP="${WECHAT_IPHONE_DAEMON_APP:-$HOME/Applications/iPhoneUse.app}"
DAEMON_BINARY="$DAEMON_APP/Contents/MacOS/iphone-use"

# Defaults below follow the user's verified deployment notes.
IPHONE_USE_PROJECT_DIR="${WECHAT_IPHONE_PROJECT_DIR:-$HOME/path/to/iphone-use}"
WDA_SCRIPT="${WECHAT_IPHONE_WDA_SCRIPT:-$IPHONE_USE_PROJECT_DIR/scripts/setup-wda.sh}"
WDA_FIXED_SCRIPT="${WECHAT_IPHONE_WDA_FIXED_SCRIPT:-$HOME/.iphone-use/setup-wda.sh}"
WDA_TEAM_ID="${WDA_TEAM_ID:-<APPLE_TEAM_ID>}"
WDA_UDID="${WDA_UDID:-<IPHONE_UDID>}"
WDA_SERVICE_LABEL="${WECHAT_IPHONE_WDA_SERVICE_LABEL:-com.leeguoo.iphone-use.wda}"
WDA_SERVICE_PLIST="${WECHAT_IPHONE_WDA_SERVICE_PLIST:-$HOME/Library/LaunchAgents/com.leeguoo.iphone-use.wda.plist}"
WDA_WRAPPER="$STATE_DIR/run-wda-keeper.sh"
WDA_SERVICE_LOG_DIR="${WECHAT_IPHONE_WDA_LOG_DIR:-$HOME/Library/Logs/iPhoneUse}"
WDA_START_TIMEOUT="${WECHAT_IPHONE_WDA_START_TIMEOUT:-300}"

# Coordinates validated on the user's current WeChat/iPhone layout.
SEARCH_X="${WECHAT_IPHONE_SEARCH_X:-0.50}"
SEARCH_Y="${WECHAT_IPHONE_SEARCH_Y:-0.12}"
FIRST_RESULT_X="${WECHAT_IPHONE_FIRST_RESULT_X:-0.50}"
FIRST_RESULT_Y="${WECHAT_IPHONE_FIRST_RESULT_Y:-0.20}"
MINI_PROGRAM_RESULT_X="${WECHAT_IPHONE_MINI_PROGRAM_RESULT_X:-$FIRST_RESULT_X}"
MINI_PROGRAM_RESULT_Y="${WECHAT_IPHONE_MINI_PROGRAM_RESULT_Y:-$FIRST_RESULT_Y}"
NEW_PRODUCTS_X="${WECHAT_IPHONE_NEW_PRODUCTS_X:-0.105}"
NEW_PRODUCTS_Y="${WECHAT_IPHONE_NEW_PRODUCTS_Y:-0.805}"
PRODUCT_SCROLL_X="${WECHAT_IPHONE_PRODUCT_SCROLL_X:-0.50}"
PRODUCT_SCROLL_Y="${WECHAT_IPHONE_PRODUCT_SCROLL_Y:-0.72}"
PRODUCT_SCROLL_DY="${WECHAT_IPHONE_PRODUCT_SCROLL_DY:-320}"
PRODUCT_MAX_SCROLLS="${WECHAT_IPHONE_PRODUCT_MAX_SCROLLS:-20}"
INPUT_X="${WECHAT_IPHONE_INPUT_X:-0.50}"
INPUT_Y="${WECHAT_IPHONE_INPUT_Y:-0.93}"
SCROLL_X="${WECHAT_IPHONE_SCROLL_X:-0.50}"
SCROLL_Y="${WECHAT_IPHONE_SCROLL_Y:-0.52}"
SCROLL_DY="${WECHAT_IPHONE_SCROLL_DY:--200}"
SCROLL_RETRY_DY="${WECHAT_IPHONE_SCROLL_RETRY_DY:--280}"

DEFAULT_CONFIG="$SCRIPT_DIR/../config/allowed-groups.json"
FALLBACK_CONFIG="$HOME/.config/wechat-iphone/allowed-groups.json"
if [[ -n "${WECHAT_IPHONE_CONFIG:-}" ]]; then
  CONFIG_FILE="$WECHAT_IPHONE_CONFIG"
elif [[ -f "$DEFAULT_CONFIG" ]]; then
  CONFIG_FILE="$DEFAULT_CONFIG"
else
  CONFIG_FILE="$FALLBACK_CONFIG"
fi

mkdir -p "$STATE_DIR"
LOCK_DIR="$STATE_DIR/controller.lock"
TOKEN=""

log() {
  printf '[wechat-iphone] %s\n' "$*" >&2
}

die_json() {
  local code="$1"
  local message="$2"
  local exit_code="${3:-1}"
  python3 - "$code" "$message" <<'PY'
import json, sys
print(json.dumps({"ok": False, "error": sys.argv[1], "message": sys.argv[2]}, ensure_ascii=False))
PY
  exit "$exit_code"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die_json "MISSING_COMMAND" "缺少命令：$1"
}

init_runtime() {
  require_cmd curl
  require_cmd python3
  if [[ ! -f "$TOKEN_FILE" ]]; then
    die_json "TOKEN_NOT_FOUND" "找不到 iphone-use token：$TOKEN_FILE"
  fi
  TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"
  if [[ -z "$TOKEN" ]]; then
    die_json "TOKEN_EMPTY" "iphone-use token 为空：$TOKEN_FILE"
  fi
}

acquire_lock() {
  if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    die_json "PHONE_CONTROLLER_BUSY" "另一个微信手机操作任务正在运行" 75
  fi
  printf '%s\n' "$$" > "$LOCK_DIR/pid"
  trap 'rm -rf "$LOCK_DIR"' EXIT INT TERM HUP
}

phone_status() {
  curl --noproxy "*" -sS --max-time 8 \
    -H "Authorization: Bearer $TOKEN" \
    "$HOST/agent/status"
}

phone_elements() {
  curl --noproxy "*" -sS --max-time 20 \
    -H "Authorization: Bearer $TOKEN" \
    "$HOST/agent/elements"
}

phone_act() {
  local payload="$1"
  curl --noproxy "*" -sS --max-time 30 \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -X POST \
    "$HOST/agent/input" \
    -d "$payload"
}

json_text_payload() {
  python3 - "$1" <<'PY'
import json, sys
print(json.dumps({"type": "text", "text": sys.argv[1]}, ensure_ascii=False))
PY
}

json_tap_label_payload() {
  python3 - "$1" <<'PY'
import json, sys
print(json.dumps({"type": "tap", "label": sys.argv[1]}, ensure_ascii=False))
PY
}

json_launch_payload() {
  python3 - "$1" <<'PY'
import json, sys
print(json.dumps({"type": "launch_app", "bundle": sys.argv[1]}, ensure_ascii=False))
PY
}

status_ready_from_stdin() {
  python3 -c '
import json, sys
try:
    s = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
ready = all([
    s.get("ok") is True,
    s.get("wda") is True,
    s.get("wda_actionable") is True,
    s.get("wda_locked") is False,
    s.get("drivable") is True,
    s.get("mode") == "agent",
])
raise SystemExit(0 if ready else 1)
'
}

assert_ready() {
  local raw
  if ! raw="$(phone_status 2>/dev/null)"; then
    die_json "IPHONE_USE_UNREACHABLE" "无法访问 $HOST/agent/status"
  fi
  if ! printf '%s' "$raw" | status_ready_from_stdin; then
    printf '%s\n' "$raw" >&2
    die_json "IPHONE_NOT_READY" "需要 ok=true、wda=true、wda_actionable=true、wda_locked=false、drivable=true、mode=agent"
  fi
}

is_allowed_group() {
  local group="$1"
  if [[ ! -f "${CONFIG_FILE}" ]]; then
    return 1
  fi
  python3 - "${CONFIG_FILE}" "$group" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
allowed = data.get("groups", [])
raise SystemExit(0 if sys.argv[2] in allowed else 1)
PY
}

assert_allowed_group() {
  local group="$1"
  if ! is_allowed_group "$group"; then
    die_json "GROUP_NOT_ALLOWED" "群聊不在允许名单：${group}；配置文件：${CONFIG_FILE}"
  fi
}

save_elements() {
  local file="$1"
  if ! phone_elements > "$file"; then
    die_json "ELEMENTS_FAILED" "读取元素树失败"
  fi
  if ! python3 - "$file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    json.load(f)
PY
  then
    die_json "ELEMENTS_INVALID_JSON" "元素树不是有效 JSON：$file"
  fi
}

find_label_contains() {
  local file="$1"
  local needle="$2"
  python3 - "$file" "$needle" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
needle = sys.argv[2]
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    if needle in label:
        print(label)
        break
PY
}

is_chat_list_file() {
  local file="$1"
  python3 - "$file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    kind = str(e.get("kind", ""))
    rect = e.get("rect") or []
    y = float(rect[1]) if len(rect) == 4 else 9999
    if "搜索" in label and y < 250 and kind in {"SearchField", "TextField", "Button", "Other", "StaticText"}:
        raise SystemExit(0)
raise SystemExit(1)
PY
}

is_group_open_file() {
  local file="$1"
  local group="$2"
  python3 - "$file" "$group" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
target = sys.argv[2]
header = False
chat_hint = False
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    rect = e.get("rect") or []
    y = float(rect[1]) if len(rect) == 4 else 9999
    if target in label and y < 180:
        header = True
    if label in {"语音", "键盘", "表情", "更多", "发送", "聊天信息"}:
        chat_hint = True
raise SystemExit(0 if header and chat_hint else 1)
PY
}

verify_group_open() {
  local group="$1"
  local file="$2"
  save_elements "$file"
  is_group_open_file "$file" "$group"
}

return_to_chat_list() {
  local tmp="$STATE_DIR/current-elements.json"
  local attempt=1
  while [[ $attempt -le 4 ]]; do
    save_elements "$tmp"
    if is_chat_list_file "$tmp"; then
      return 0
    fi
    local back_label
    back_label="$(find_label_contains "$tmp" "返回")"
    if [[ -z "$back_label" ]]; then
      return 1
    fi
    phone_act "$(json_tap_label_payload "$back_label")" >/dev/null
    sleep 1
    attempt=$((attempt + 1))
  done
  save_elements "$tmp"
  is_chat_list_file "$tmp"
}

clear_search_if_possible() {
  local tmp="$STATE_DIR/search-elements.json"
  save_elements "$tmp"
  local label
  label="$(find_label_contains "$tmp" "清除")"
  if [[ -n "$label" ]]; then
    phone_act "$(json_tap_label_payload "$label")" >/dev/null || true
    sleep 0.5
  fi
}

open_group_internal() {
  local group="$1"
  local verify_file="$STATE_DIR/group-verify.json"

  log "打开微信"
  phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null
  sleep 1

  if verify_group_open "$group" "$verify_file"; then
    log "当前已在目标群聊"
    return 0
  fi

  if ! return_to_chat_list; then
    die_json "CHAT_LIST_NOT_FOUND" "无法返回微信聊天列表"
  fi

  log "点击聊天列表搜索栏"
  phone_act "{\"type\":\"tap\",\"x\":$SEARCH_X,\"y\":$SEARCH_Y}" >/dev/null
  sleep 1

  clear_search_if_possible

  log "搜索群聊：$group"
  phone_act "$(json_text_payload "$group")" >/dev/null
  sleep 1

  log "点击第一条搜索结果"
  phone_act "{\"type\":\"tap\",\"x\":$FIRST_RESULT_X,\"y\":$FIRST_RESULT_Y}" >/dev/null
  sleep 1

  if ! verify_group_open "$group" "$verify_file"; then
    die_json "TARGET_GROUP_NOT_VERIFIED" "点击搜索结果后，未在页面顶部验证到目标群聊：$group"
  fi
}

page_signature() {
  local file="$1"
  python3 - "$file" <<'PY'
import hashlib, json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
rows = []
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    rect = e.get("rect") or []
    if not label or len(rect) != 4:
        continue
    x, y, w, h = map(float, rect)
    if 70 <= y < 690:
        rows.append((str(e.get("kind", "")), label, round(x), round(y), round(w), round(h)))
rows.sort()
blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
print(hashlib.sha256(blob).hexdigest())
PY
}

cmd_status() {
  init_runtime
  local raw
  raw="$(phone_status)" || die_json "IPHONE_USE_UNREACHABLE" "无法访问 iphone-use status"
  printf '%s' "$raw" | python3 -c '
import json, sys
s = json.load(sys.stdin)
ready = all([
    s.get("ok") is True,
    s.get("wda") is True,
    s.get("wda_actionable") is True,
    s.get("wda_locked") is False,
    s.get("drivable") is True,
    s.get("mode") == "agent",
])
out = {
    "ok": True,
    "action": "status",
    "ready": ready,
    "status": s,
}
print(json.dumps(out, ensure_ascii=False))
'
}

resolve_wda_script() {
  if [[ -x "$WDA_SCRIPT" ]]; then
    printf '%s\n' "$WDA_SCRIPT"
    return 0
  fi
  if [[ -x "$WDA_FIXED_SCRIPT" ]]; then
    printf '%s\n' "$WDA_FIXED_SCRIPT"
    return 0
  fi
  return 1
}

service_loaded() {
  local label="$1"
  launchctl print "gui/$(id -u)/$label" >/dev/null 2>&1
}

wda_reachable() {
  curl --noproxy "*" -sS --max-time 4 "$WDA_URL/status" >/dev/null 2>&1
}

validate_wda_script() {
  local script="$1"
  local active="$STATE_DIR/wda-script-active.$$"

  sed '/^[[:space:]]*#/d' "$script" > "$active"

  if grep -Eq 'nohup[[:space:]]+xcodebuild' "$active"; then
    rm -f "$active"
    die_json "WDA_SCRIPT_NOT_PATCHED" "setup-wda.sh 仍使用 nohup xcodebuild；请按实测文档移除 nohup，并让 xcodebuild 保持为 setup-wda.sh 的直接子进程"
  fi

  if grep -Eq -- '-allowProvisioningUpdates|-allowProvisioningDeviceRegistration|DEVELOPMENT_TEAM=|PRODUCT_BUNDLE_IDENTIFIER=|CODE_SIGN_IDENTITY=|CODE_SIGN_STYLE=' "$active"; then
    rm -f "$active"
    die_json "WDA_SIGNING_OVERRIDE_FOUND" "setup-wda.sh 仍包含命令行签名覆盖；本机成功方案要求复用 Xcode 项目中的 Team 与 Bundle ID 配置"
  fi

  rm -f "$active"

  if ! grep -q 'WDA_KEEPALIVE' "$script"; then
    die_json "WDA_KEEPALIVE_UNSUPPORTED" "setup-wda.sh 不包含 WDA_KEEPALIVE 支持，请同步实测修改后的脚本"
  fi
}

close_competing_apps() {
  log "关闭可能争用 XCTest 会话的 Xcode GUI 与 iPhone 镜像"
  osascript -e 'tell application "Xcode" to quit' >/dev/null 2>&1 || true
  osascript -e 'tell application id "com.apple.ScreenContinuity" to quit' >/dev/null 2>&1 || true
  sleep 1
}

check_wda_prerequisites() {
  require_cmd xcodebuild
  require_cmd xcrun
  require_cmd iproxy
  require_cmd idevice_id

  local script
  script="$(resolve_wda_script)" || die_json "WDA_SCRIPT_NOT_FOUND" "找不到 setup-wda.sh；已检查：$WDA_SCRIPT 和 $WDA_FIXED_SCRIPT"
  validate_wda_script "$script"

  if command -v warp-cli >/dev/null 2>&1 && warp-cli status 2>/dev/null | grep -qiw 'Connected'; then
    die_json "VPN_TUN_ACTIVE" "Cloudflare WARP 正在连接，会破坏 CoreDevice/XCTest 会话；请先断开"
  fi

  if ! idevice_id -l 2>/dev/null | grep -Fxq "$WDA_UDID"; then
    die_json "IPHONE_USB_NOT_FOUND" "USB 未识别目标 iPhone：${WDA_UDID}；请解锁、保持亮屏并检查数据线"
  fi
}

start_daemon_internal() {
  local uid_num
  uid_num="$(id -u)"

  [[ -f "$DAEMON_PLIST" ]] || die_json "DAEMON_PLIST_NOT_FOUND" "找不到：$DAEMON_PLIST"
  [[ -x "$DAEMON_BINARY" ]] || die_json "DAEMON_BINARY_NOT_FOUND" "找不到或不可执行：$DAEMON_BINARY"

  if ! plutil -lint "$DAEMON_PLIST" >/dev/null; then
    die_json "DAEMON_PLIST_INVALID" "LaunchAgent plist 校验失败：$DAEMON_PLIST"
  fi

  log "启动 iphone-use LaunchAgent"
  if ! service_loaded "$DAEMON_LABEL"; then
    launchctl bootstrap "gui/$uid_num" "$DAEMON_PLIST" >/dev/null 2>&1 \
      || die_json "DAEMON_BOOTSTRAP_FAILED" "无法 bootstrap $DAEMON_LABEL"
  fi

  launchctl enable "gui/$uid_num/$DAEMON_LABEL" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/$uid_num/$DAEMON_LABEL" >/dev/null \
    || die_json "DAEMON_KICKSTART_FAILED" "无法启动 $DAEMON_LABEL"

  local count=0
  while true; do
    if phone_status >/dev/null 2>&1; then
      return 0
    fi
    count=$((count + 1))
    if [[ $count -ge 30 ]]; then
      die_json "DAEMON_START_TIMEOUT" "iphone-use 未在 30 秒内响应 $HOST/agent/status"
    fi
    sleep 1
  done
}

stop_wda_processes() {
  local script=""
  script="$(resolve_wda_script 2>/dev/null || true)"
  if [[ -n "$script" ]]; then
    "$script" stop >/dev/null 2>&1 || true
  fi

  pkill -9 -f 'xcodebuild.*WebDriverAgentRunner' 2>/dev/null || true
  pkill -f 'iproxy.*8100' 2>/dev/null || true
  pkill -f 'socat.*8100' 2>/dev/null || true
  pkill -f 'iproxy.*9100' 2>/dev/null || true
  pkill -9 -f '/usr/bin/sudo -- /usr/bin/true' 2>/dev/null || true

  rm -f \
    "$HOME/.iphone-use/wda-runner.pid" \
    "$HOME/.iphone-use/wda-relay.pid" \
    "$HOME/.iphone-use/wda-mjpeg-relay.pid"
}

write_wda_service_files() {
  local script="$1"
  mkdir -p "$STATE_DIR" "${WDA_SERVICE_LOG_DIR}" "$HOME/Library/LaunchAgents"

  cat > "$WDA_WRAPPER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$IPHONE_USE_PROJECT_DIR"
exec env \\
  WDA_KEEPALIVE=1 \\
  WDA_TEAM_ID="$WDA_TEAM_ID" \\
  WDA_UDID="$WDA_UDID" \\
  "$script"
EOF
  chmod 700 "$WDA_WRAPPER"

  cat > "$WDA_SERVICE_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$WDA_SERVICE_LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>$WDA_WRAPPER</string>
  </array>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>

  <key>ThrottleInterval</key>
  <integer>30</integer>

  <key>LimitLoadToSessionType</key>
  <string>Aqua</string>

  <key>EnvironmentVariables</key>
  <dict>
    <key>HOME</key>
    <string>$HOME</string>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>

  <key>StandardOutPath</key>
  <string>${WDA_SERVICE_LOG_DIR}/wda-keeper.log</string>
  <key>StandardErrorPath</key>
  <string>${WDA_SERVICE_LOG_DIR}/wda-keeper.err</string>
</dict>
</plist>
EOF
  chmod 600 "$WDA_SERVICE_PLIST"
  plutil -lint "$WDA_SERVICE_PLIST" >/dev/null \
    || die_json "WDA_SERVICE_PLIST_INVALID" "生成的 WDA LaunchAgent plist 无效"
}

stop_wda_service_internal() {
  local uid_num
  uid_num="$(id -u)"

  launchctl bootout "gui/$uid_num/$WDA_SERVICE_LABEL" >/dev/null 2>&1 || true
  sleep 1
  stop_wda_processes
}

start_wda_service_internal() {
  local force="${1:-0}"
  local uid_num
  uid_num="$(id -u)"

  if [[ "$force" != "1" ]] && wda_reachable && service_loaded "$WDA_SERVICE_LABEL"; then
    log "WDA 已由专用 LaunchAgent 守护并且可用，跳过重启"
    return 0
  fi

  if [[ "$force" != "1" ]] && wda_reachable && ! service_loaded "$WDA_SERVICE_LABEL"; then
    log "检测到手工启动的 WDA；将其切换为专用 LaunchAgent 守护模式"
  fi

  check_wda_prerequisites
  close_competing_apps

  local script
  script="$(resolve_wda_script)" || die_json "WDA_SCRIPT_NOT_FOUND" "找不到 setup-wda.sh"

  log "清理旧 WDA/XCTest/iproxy 进程"
  stop_wda_service_internal
  write_wda_service_files "$script"

  log "通过专用 LaunchAgent 启动 WDA_KEEPALIVE=1"
  if ! launchctl bootstrap "gui/$uid_num" "$WDA_SERVICE_PLIST" >/dev/null 2>&1; then
    sleep 1
    launchctl bootout "gui/$uid_num/$WDA_SERVICE_LABEL" >/dev/null 2>&1 || true
    sleep 1
    launchctl bootstrap "gui/$uid_num" "$WDA_SERVICE_PLIST" >/dev/null 2>&1 \
      || die_json "WDA_SERVICE_BOOTSTRAP_FAILED" "无法加载 ${WDA_SERVICE_LABEL}；查看 ${WDA_SERVICE_LOG_DIR}/wda-keeper.err"
  fi

  launchctl enable "gui/$uid_num/$WDA_SERVICE_LABEL" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/$uid_num/$WDA_SERVICE_LABEL" >/dev/null \
    || die_json "WDA_SERVICE_KICKSTART_FAILED" "无法启动 $WDA_SERVICE_LABEL"

  local elapsed=0
  while ! wda_reachable; do
    elapsed=$((elapsed + 2))
    if [[ $elapsed -ge $WDA_START_TIMEOUT ]]; then
      tail -n 80 "$HOME/.iphone-use/wda-runner.log" >&2 2>/dev/null || true
      tail -n 80 "${WDA_SERVICE_LOG_DIR}/wda-keeper.err" >&2 2>/dev/null || true
      die_json "WDA_START_TIMEOUT" "WDA 未在 ${WDA_START_TIMEOUT} 秒内响应 $WDA_URL/status"
    fi
    sleep 2
  done
}

request_agent_mode_if_needed() {
  local raw
  raw="$(phone_status 2>/dev/null || true)"
  if printf '%s' "$raw" | status_ready_from_stdin >/dev/null 2>&1; then
    return 0
  fi

  curl --noproxy "*" -sS --max-time 15 \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -X POST \
    "$HOST/agent/mode" \
    -d '{"mode":"agent"}' >/dev/null 2>&1 || true
}

wait_agent_ready() {
  local count=0
  local raw=""
  while true; do
    raw="$(phone_status 2>/dev/null || true)"
    if printf '%s' "$raw" | status_ready_from_stdin >/dev/null 2>&1; then
      return 0
    fi
    count=$((count + 1))
    if [[ $count -ge 60 ]]; then
      printf '%s\n' "$raw" >&2
      die_json "STACK_NOT_READY" "WDA 已启动，但 iphone-use 未在 60 秒内进入可操作 Agent 状态"
    fi
    sleep 1
  done
}

cmd_status() {
  init_runtime

  local raw=""
  local daemon_loaded=false
  local wda_service_loaded=false
  local wda_http=false

  service_loaded "$DAEMON_LABEL" && daemon_loaded=true
  service_loaded "$WDA_SERVICE_LABEL" && wda_service_loaded=true
  wda_reachable && wda_http=true
  raw="$(phone_status 2>/dev/null || true)"

  python3 - "$raw" "$daemon_loaded" "$wda_service_loaded" "$wda_http" "$IPHONE_USE_PROJECT_DIR" "$WDA_UDID" <<'PY'
import json, sys
raw, daemon_loaded, wda_service_loaded, wda_http, project_dir, udid = sys.argv[1:]
try:
    status = json.loads(raw)
except Exception:
    status = None
ready = bool(status) and all([
    status.get("ok") is True,
    status.get("wda") is True,
    status.get("wda_actionable") is True,
    status.get("wda_locked") is False,
    status.get("drivable") is True,
    status.get("mode") == "agent",
])
print(json.dumps({
    "ok": True,
    "action": "status",
    "ready": ready,
    "daemon_loaded": daemon_loaded == "true",
    "wda_service_loaded": wda_service_loaded == "true",
    "wda_http_reachable": wda_http == "true",
    "project_dir": project_dir,
    "wda_udid": udid,
    "status": status,
}, ensure_ascii=False))
PY
}

cmd_start_daemon() {
  init_runtime
  start_daemon_internal
  cmd_status
}

cmd_start_wda() {
  init_runtime
  start_wda_service_internal 0
  request_agent_mode_if_needed
  wait_agent_ready
  cmd_status
}

cmd_start() {
  init_runtime
  start_daemon_internal
  start_wda_service_internal 0
  request_agent_mode_if_needed
  wait_agent_ready
  cmd_status
}

cmd_restart() {
  init_runtime
  start_daemon_internal
  start_wda_service_internal 1
  request_agent_mode_if_needed
  wait_agent_ready
  cmd_status
}

cmd_stop_wda() {
  require_cmd launchctl
  require_cmd curl
  stop_wda_service_internal
  python3 - <<'PY'
import json
print(json.dumps({"ok": True, "action": "stop-wda", "stopped": True}, ensure_ascii=False))
PY
}

cmd_stop() {
  require_cmd launchctl
  local uid_num
  uid_num="$(id -u)"

  stop_wda_service_internal
  launchctl bootout "gui/$uid_num/$DAEMON_LABEL" >/dev/null 2>&1 || true

  python3 - <<'PY'
import json
print(json.dumps({"ok": True, "action": "stop", "wda_stopped": True, "daemon_stopped": True}, ensure_ascii=False))
PY
}

cmd_doctor() {
  require_cmd python3
  require_cmd curl

  local wda_script=""
  wda_script="$(resolve_wda_script 2>/dev/null || true)"
  local daemon_plist_ok=false daemon_binary_ok=false project_ok=false wda_script_ok=false
  local iproxy_ok=false usb_ok=false wda_http=false daemon_http=false

  [[ -f "$DAEMON_PLIST" ]] && plutil -lint "$DAEMON_PLIST" >/dev/null 2>&1 && daemon_plist_ok=true
  [[ -x "$DAEMON_BINARY" ]] && daemon_binary_ok=true
  [[ -d "$IPHONE_USE_PROJECT_DIR" ]] && project_ok=true
  [[ -n "$wda_script" && -x "$wda_script" ]] && wda_script_ok=true
  command -v iproxy >/dev/null 2>&1 && iproxy_ok=true
  command -v idevice_id >/dev/null 2>&1 && idevice_id -l 2>/dev/null | grep -Fxq "$WDA_UDID" && usb_ok=true
  wda_reachable && wda_http=true

  if [[ -f "$TOKEN_FILE" ]]; then
    TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"
    phone_status >/dev/null 2>&1 && daemon_http=true
  fi

  python3 - "$daemon_plist_ok" "$daemon_binary_ok" "$project_ok" "$wda_script_ok" "$iproxy_ok" "$usb_ok" "$wda_http" "$daemon_http" "$wda_script" <<'PY'
import json, sys
names = [
    "daemon_plist_ok", "daemon_binary_ok", "project_dir_ok", "wda_script_ok",
    "iproxy_ok", "usb_device_ok", "wda_http_reachable", "daemon_http_reachable",
]
values = [value == "true" for value in sys.argv[1:9]]
checks = dict(zip(names, values))
print(json.dumps({
    "ok": all(values[:6]),
    "action": "doctor",
    "checks": checks,
    "wda_script": sys.argv[9],
}, ensure_ascii=False))
PY
}

cmd_open_group() {
  local group=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --group) group="${2:-}"; shift 2 ;;
      *) die_json "INVALID_ARGUMENT" "未知参数：$1" ;;
    esac
  done
  [[ -n "$group" ]] || die_json "GROUP_REQUIRED" "需要 --group"

  init_runtime
  assert_allowed_group "$group"
  assert_ready
  acquire_lock
  open_group_internal "$group"

  python3 - "$group" <<'PY'
import json, sys
print(json.dumps({"ok": True, "action": "open-group", "group": sys.argv[1], "verified": True}, ensure_ascii=False))
PY
}

cmd_send() {
  local group=""
  local message=""
  local dry_run=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --group) group="${2:-}"; shift 2 ;;
      --message) message="${2:-}"; shift 2 ;;
      --dry-run) dry_run=1; shift ;;
      *) die_json "INVALID_ARGUMENT" "未知参数：$1" ;;
    esac
  done

  [[ -n "$group" ]] || die_json "GROUP_REQUIRED" "需要 --group"
  [[ -n "$message" ]] || die_json "MESSAGE_REQUIRED" "需要 --message"

  init_runtime
  assert_allowed_group "$group"
  assert_ready
  acquire_lock
  open_group_internal "$group"

  log "点击消息输入框"
  phone_act "{\"type\":\"tap\",\"x\":$INPUT_X,\"y\":$INPUT_Y}" >/dev/null
  sleep 1

  log "输入消息"
  phone_act "$(json_text_payload "$message")" >/dev/null
  sleep 2

  local before="$STATE_DIR/before-send.json"
  save_elements "$before"
  if ! is_group_open_file "$before" "$group"; then
    die_json "TARGET_GROUP_LOST" "输入消息后已无法验证目标群聊，停止发送"
  fi

  local send_label
  send_label="$(find_label_contains "$before" "发送")"
  if [[ -z "$send_label" ]]; then
    die_json "SEND_BUTTON_NOT_FOUND" "没有在元素树中找到发送按钮，消息未发送"
  fi

  if [[ $dry_run -eq 1 ]]; then
    python3 - "$group" "$message" "$send_label" <<'PY'
import json, sys
print(json.dumps({
    "ok": True,
    "action": "send",
    "dry_run": True,
    "group": sys.argv[1],
    "message": sys.argv[2],
    "send_label": sys.argv[3],
    "prepared": True,
}, ensure_ascii=False))
PY
    return 0
  fi

  log "点击发送按钮：$send_label"
  local send_result
  send_result="$(phone_act "$(json_tap_label_payload "$send_label")")"
  sleep 3

  local after="$STATE_DIR/after-send.json"
  save_elements "$after"

  python3 - "$after" "$group" "$message" "$send_result" <<'PY'
import json, sys
path, group, message, send_result = sys.argv[1:]
with open(path, encoding="utf-8") as f:
    data = json.load(f)
labels = [str(e.get("label", "")) for e in data.get("elements", [])]
group_ok = any(group in x for x in labels)
message_ok = any(message in x for x in labels)
print(json.dumps({
    "ok": True,
    "action": "send",
    "group": group,
    "message": message,
    "sent": True,
    "verified": bool(group_ok and message_ok),
    "group_still_open": group_ok,
    "message_visible": message_ok,
    "transport_result": send_result,
    "warning": None if group_ok and message_ok else "发送操作已执行，但元素树未能完整验证；不要自动重试，以免重复发送。",
}, ensure_ascii=False))
PY
}

cmd_read() {
  local group=""
  local pages=1
  local out_dir=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --group) group="${2:-}"; shift 2 ;;
      --pages) pages="${2:-}"; shift 2 ;;
      --out-dir) out_dir="${2:-}"; shift 2 ;;
      *) die_json "INVALID_ARGUMENT" "未知参数：$1" ;;
    esac
  done

  [[ -n "$group" ]] || die_json "GROUP_REQUIRED" "需要 --group"
  if ! [[ "$pages" =~ ^[0-9]+$ ]] || [[ "$pages" -lt 1 ]] || [[ "$pages" -gt 50 ]]; then
    die_json "INVALID_PAGES" "--pages 必须是 1 到 50 的整数"
  fi

  init_runtime
  assert_allowed_group "$group"
  assert_ready
  acquire_lock
  open_group_internal "$group"

  if [[ -z "$out_dir" ]]; then
    out_dir="$STATE_DIR/history-$(date +%Y%m%d-%H%M%S)"
  fi
  mkdir -p "$out_dir"

  local first="$out_dir/page-01.json"
  save_elements "$first"
  local previous_signature
  previous_signature="$(page_signature "$first")"
  local collected=1

  local page_number=2
  while [[ $page_number -le $pages ]]; do
    local page_name
    page_name="$(printf '%02d' "$page_number")"
    local candidate="$out_dir/.candidate.json"
    local target="$out_dir/page-${page_name}.json"

    log "准备获取第 $page_number 页"
    local scroll_result
    scroll_result="$(phone_act "{\"type\":\"scroll\",\"x\":$SCROLL_X,\"y\":$SCROLL_Y,\"dx\":0,\"dy\":$SCROLL_DY}")"
    if [[ "$scroll_result" != *"ok"* ]]; then
      log "滑动未成功：$scroll_result"
      break
    fi

    sleep 2
    save_elements "$candidate"
    local next_signature
    next_signature="$(page_signature "$candidate")"

    if [[ "$next_signature" == "$previous_signature" ]]; then
      log "页面未变化，尝试更强滑动"
      scroll_result="$(phone_act "{\"type\":\"scroll\",\"x\":$SCROLL_X,\"y\":0.55,\"dx\":0,\"dy\":$SCROLL_RETRY_DY}")"
      if [[ "$scroll_result" != *"ok"* ]]; then
        rm -f "$candidate"
        break
      fi
      sleep 2
      save_elements "$candidate"
      next_signature="$(page_signature "$candidate")"
    fi

    if [[ "$next_signature" == "$previous_signature" ]]; then
      log "页面仍未变化，可能已经到达最早消息"
      rm -f "$candidate"
      break
    fi

    mv "$candidate" "$target"
    previous_signature="$next_signature"
    collected=$page_number
    page_number=$((page_number + 1))
  done

  python3 - "$out_dir" "$group" "$pages" "$collected" <<'PY'
import glob, json, os, sys
out_dir, group, requested, collected = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ignore = {
    group, "返回", "聊天信息", "语音", "键盘", "表情", "更多", "发送", "搜索"
}
pages = []
for filename in sorted(glob.glob(os.path.join(out_dir, "page-*.json"))):
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    seen = set()
    for element in data.get("elements", []):
        label = str(element.get("label", "")).strip()
        rect = element.get("rect") or []
        if not label or label in ignore or len(rect) != 4:
            continue
        x, y, width, height = map(float, rect)
        if not 70 <= y < 690:
            continue
        key = (label, round(x), round(y), round(width), round(height))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "kind": element.get("kind"),
            "label": label,
            "rect": rect,
            "depth": element.get("depth"),
        })
    rows.sort(key=lambda item: (float(item["rect"][1]), float(item["rect"][0])))
    pages.append({
        "page": os.path.basename(filename),
        "items": rows,
    })
print(json.dumps({
    "ok": True,
    "action": "read",
    "group": group,
    "requested_pages": requested,
    "collected_pages": len(pages),
    "raw_dir": out_dir,
    "pages": pages,
}, ensure_ascii=False))
PY
}


is_mini_program_open_file() {
  local file="$1"
  local mini_program="$2"
  python3 - "$file" "$mini_program" <<'PY'
import json, sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

target = sys.argv[2]
labels = [str(e.get("label", "")).strip() for e in data.get("elements", [])]

# 微信搜索名是“良久素材”，但进入小程序后顶部可能显示“良久团购”。
name_ok = any(
    target in label
    or "良久素材" in label
    or "良久团购" in label
    or "LIANGJIUTUANGOU" in label
    for label in labels
)

# 微信小程序壳元素。
mini_shell_ok = any(
    label in {"更多", "关闭", "返回"}
    or "小程序" in label
    for label in labels
)

# 良久首页特征元素。你的截图里可以看到这些入口。
liangjiu_home_ok = any(
    key in label
    for label in labels
    for key in [
        "新品首发",
        "爆款加开",
        "日销尖货",
        "新人展业",
        "公益助农",
        "官方授权",
        "品质保证",
        "极速发货",
        "售后无忧",
    ]
)

raise SystemExit(0 if (name_ok and mini_shell_ok) or liangjiu_home_ok else 1)
PY
}

is_liangjiu_home_file() {
  local file="$1"
  python3 - "$file" <<'PY'
import json, sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

labels = [str(e.get("label", "")).strip() for e in data.get("elements", [])]
keywords = [
    "良久团购",
    "良久素材",
    "新品首发",
    "爆款加开",
    "日销尖货",
    "新人展业",
    "公益助农",
    "官方授权",
    "品质保证",
    "极速发货",
    "售后无忧",
]

ok = any(keyword in label for keyword in keywords for label in labels)
raise SystemExit(0 if ok else 1)
PY
}

return_to_wechat_chat_list() {
  local tmp="$STATE_DIR/scenario-current-elements.json"
  local attempt=1

  while [[ $attempt -le 8 ]]; do
    save_elements "$tmp"

    if is_chat_list_file "$tmp"; then
      return 0
    fi

    local back_label
    back_label="$(find_label_contains "$tmp" "返回")"

    if [[ -n "$back_label" ]]; then
      phone_act "$(json_tap_label_payload "$back_label")" >/dev/null || true
    else
      phone_act '{"type":"tap","x":0.06,"y":0.065}' >/dev/null || true
    fi

    sleep 1
    attempt=$((attempt + 1))
  done

  save_elements "$tmp"
  is_chat_list_file "$tmp"
}

open_mini_program_internal() {
  local mini_program="$1"
  local tmp="$STATE_DIR/mini-program-elements.json"

  log "打开微信"
  phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null
  sleep 3

  # 不再相信启动微信后的第一次元素树。
  # 原因：iPhone-use/WDA 有时会返回上一次小程序页面的元素缓存，
  # 导致脚本误判“当前已在良久小程序页面”。
  # 所以只要没有显式传 --skip-open，就强制回到微信聊天列表，重新搜索并进入小程序。
  log "强制从微信聊天列表重新搜索小程序，避免复用上次元素树或页面缓存"

  if ! return_to_wechat_chat_list; then
    log "第一次返回聊天列表失败，重新启动微信后再试一次"
    phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null || true
    sleep 3
    return_to_wechat_chat_list || die_json "CHAT_LIST_NOT_FOUND" "无法返回微信聊天列表；请确认微信已解锁且在前台可操作"
  fi

  log "搜索小程序：${mini_program}"
  phone_act "{\"type\":\"tap\",\"x\":$SEARCH_X,\"y\":$SEARCH_Y}" >/dev/null
  sleep 1

  clear_search_if_possible

  phone_act "$(json_text_payload "$mini_program")" >/dev/null
  sleep 2

  log "点击最近使用过的小程序第一条记录：x=${MINI_PROGRAM_RESULT_X} y=${MINI_PROGRAM_RESULT_Y}"
  phone_act "{\"type\":\"tap\",\"x\":$MINI_PROGRAM_RESULT_X,\"y\":$MINI_PROGRAM_RESULT_Y}" >/dev/null
  sleep 4

  local verify_attempt=1
  while [[ $verify_attempt -le 8 ]]; do
    save_elements "$tmp"

    if is_mini_program_open_file "$tmp" "$mini_program"; then
      log "已验证进入良久小程序"
      return 0
    fi

    if is_liangjiu_home_file "$tmp"; then
      log "已进入良久首页，但元素树未显示搜索名，继续执行"
      return 0
    fi

    local found
    found="$(find_label_contains "$tmp" "$mini_program")"
    if [[ -n "$found" ]]; then
      log "通过文本验证进入小程序：${found}"
      return 0
    fi

    sleep 1
    verify_attempt=$((verify_attempt + 1))
  done

  die_json "MINI_PROGRAM_NOT_VERIFIED" "未能验证进入小程序：${mini_program}；当前可能点错搜索结果，请调整 --mini-program-result-x/y，或当前微信页面未能返回聊天列表"
}

enter_new_products_internal() {
  local tmp="$STATE_DIR/new-products-elements.json"
  save_elements "$tmp"
  local label
  label="$(find_label_contains "$tmp" "新品首发")"
  if [[ -n "$label" ]]; then
    log "通过元素标签点击新品首发：$label"
    phone_act "$(json_tap_label_payload "$label")" >/dev/null
  else
    log "通过坐标点击新品首发：x=$NEW_PRODUCTS_X y=$NEW_PRODUCTS_Y"
    phone_act "{\"type\":\"tap\",\"x\":$NEW_PRODUCTS_X,\"y\":$NEW_PRODUCTS_Y}" >/dev/null
  fi
  sleep 4
}

find_product_label_for_category() {
  local file="$1" category="$2"
  python3 - "$file" "$category" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f: data=json.load(f)
needle=sys.argv[2].strip(); candidates=[]
for e in data.get("elements", []):
    label=str(e.get("label", "")).strip(); rect=e.get("rect") or []; kind=str(e.get("kind", ""))
    if not label or needle not in label or len(rect)!=4: continue
    x,y,w,h=map(float,rect)
    if not 120 <= y <= 720: continue
    score={"Button":0,"Image":1,"Cell":2,"Other":3,"StaticText":4}.get(kind,5)
    candidates.append((score,-w*h,y,label))
if candidates:
    candidates.sort(); print(candidates[0][3])
PY
}

return_to_new_products_list() {
  local tmp="$STATE_DIR/product-detail-elements.json"
  save_elements "$tmp"
  local back_label
  back_label="$(find_label_contains "$tmp" "返回")"
  if [[ -n "$back_label" ]]; then
    phone_act "$(json_tap_label_payload "$back_label")" >/dev/null
  else
    phone_act '{"type":"tap","x":0.06,"y":0.065}' >/dev/null
  fi
  sleep 3
}

select_category_product_internal() {
  local category="$1" max_scrolls="$2" tmp="$STATE_DIR/product-list-elements.json" scroll_index=0
  while [[ $scroll_index -le $max_scrolls ]]; do
    save_elements "$tmp"
    local product_label
    product_label="$(find_product_label_for_category "$tmp" "$category")"
    if [[ -n "$product_label" ]]; then
      log "找到：$category -> $product_label"
      phone_act "$(json_tap_label_payload "$product_label")" >/dev/null
      sleep 4
      return_to_new_products_list
      printf '%s\n' "$product_label"
      return 0
    fi
    [[ $scroll_index -ge $max_scrolls ]] && break
    phone_act "{\"type\":\"scroll\",\"x\":$PRODUCT_SCROLL_X,\"y\":$PRODUCT_SCROLL_Y,\"dx\":0,\"dy\":$PRODUCT_SCROLL_DY}" >/dev/null
    sleep 2
    scroll_index=$((scroll_index + 1))
  done
  return 1
}

append_visible_products_from_page() {
  local page_file="$1"
  local seen_file="$2"
  local result_file="$3"
  local page_index="$4"
  local limit="$5"

  python3 - "$page_file" "$seen_file" "$result_file" "$page_index" "$limit" <<'PYCOLLECT_V13_NAMES_ONLY'
import json
import re
import sys
from pathlib import Path

page_file, seen_file, result_file, page_index, limit = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])

with open(page_file, encoding="utf-8") as f:
    data = json.load(f)

seen_path = Path(seen_file)
result_path = Path(result_file)

seen = set()
if seen_path.exists():
    seen = {
        line.strip()
        for line in seen_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

current_count = 0
if result_path.exists():
    for line in result_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            current_count += 1

# v13：只提取商品名称，不提取规格和价格。
# 后续进入商品详情页后，再采集规格、价格、图片、视频等详情数据。

blocked_exact = {
    "", "返回", "更多", "关闭", "搜索", "取消", "确定", "完成", "清除", "分享", "菜单",
    "新品首发", "爆款加开", "日销尖货", "新人展业", "公益助农",
    "首页", "分类", "购物车", "选品库", "我的", "客服",
    "官方授权", "品质保证", "极速发货", "售后无忧",
    "综合", "销量", "价格", "筛选", "全部", "上新", "推荐",
    "包邮", "现货", "新品", "去购买", "立即购买", "加入", "加购", "已售罄",
    "前往", "复制", "完成", "知道了", "允许", "不允许",
}

blocked_contains = [
    "微信", "小程序", "良久素材", "良久团购", "LIANGJIUTUANGOU",
    "返回", "更多", "关闭", "搜索", "购物车", "首页", "分类", "我的", "客服",
    "官方授权", "品质保证", "极速发货", "售后无忧",
    "新品首发", "爆款加开", "日销尖货", "新人展业", "公益助农",
    "加载中", "暂无", "没有更多", "下拉", "刷新", "查看更多", "立即登录",
    "授权", "登录", "隐私", "协议", "关注", "收藏", "分享",
]

# 只用于判断“像不像商品名称”，不是品类筛选。
product_terms = [
    "裤", "裙", "衣", "外套", "背心", "连衣裙", "套装", "鞋", "靴", "包", "帽", "袜", "衫", "服",
    "防晒", "乳", "霜", "水", "精华", "洗发", "沐浴", "牙膏", "牙刷", "纸", "巾", "抹布", "护肤",
    "架", "柜", "盒", "箱", "篮", "壶", "杯", "锅", "碗", "盘", "刀", "茶", "套装",
    "虾", "虾仁", "酱", "果", "天麻", "饼", "鸡排", "鱼排", "牛排", "肉串", "食品", "大虾", "馅饼",
    "枕", "被", "凉被", "四件套", "三件套", "凉席", "床单", "被套", "套件", "蚊帐", "纱帐", "空调被",
]

text_pattern = re.compile(r"[\u4e00-\u9fffA-Za-z]")
date_pattern = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s*星期[一二三四五六日天]$")
price_pattern = re.compile(r"(¥|￥|价格|售价|供货价|供货|到手价|到手|券后|佣金|利润|赚|团购价|零售价|市场价|现价|原价|秒杀价|活动价|\d{1,5}\.\d{1,2})")
measurement_pattern = re.compile(r"(\d+(\.\d+)?\s*(cm|mL|ml|g|kg|斤|袋|瓶|支|条|个|箱|片|包|组|套|m|L)|\d+\s*[xX*]\s*\d+|\d{2,3}\s*[xX*]\s*\d{2,3})")
size_pattern = re.compile(r"(^|\s)(XS|S|M|L|XL|XXL|2XL|3XL|4XL|5XL)(\s|$)|\b(3[5-9]|4[0-5])\b", re.I)

# 这些开头基本都是规格，不作为商品名。
spec_prefix_pattern = re.compile(
    r"^(规格|规格[一二三四五六七八九十]|标准款|单人款|双人款|平铺|平铺标准款|"
    r"三件套[（(:：]|四件套[（(:：]|[一二三四五六七八九十]?件套[（(:：]|"
    r"\d+\s*(组|袋|斤|个|瓶|支|条|箱|片|包|套))"
)

color_size_pattern = re.compile(
    r"^(黑色|白色|红色|紫红色|紫红|卡其|胡桃色|奶油白|玫瑰粉|浅雾|芭乐粉|木果绿|波浪绿|香槟|粉色|绿色|蓝色|灰色|米色|杏色|咖色|棕色|黄色|橙色|浅色|深色)"
    r"\s*(XS|S|M|L|XL|XXL|2XL|3XL|4XL|5XL|3[5-9]|4[0-5])?$",
    re.I,
)


def norm_label(value: str) -> str:
    value = str(value or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_key(value: str) -> str:
    value = norm_label(value).lower()
    value = re.sub(r"[\s\u3000，,。.!！:：;；、|/\\\-—_()（）\[\]【】]+", "", value)
    value = re.sub(r"(¥|￥)?\d+(\.\d+)?", "", value)
    return value[:100]


def has_product_term(label: str) -> bool:
    return any(term in label for term in product_terms)


def is_price_or_price_fragment(label: str) -> bool:
    s = norm_label(label)
    compact = re.sub(r"\s+", "", s)
    if compact in {"¥", "￥"}:
        return True
    if price_pattern.search(s):
        # 避免把 150*200cm / 500g 当价格。
        if measurement_pattern.search(s) and not ("¥" in s or "￥" in s or any(k in s for k in ["价", "供货", "到手", "券后"])):
            return False
        return True
    return False


def is_spec_line(label: str) -> bool:
    s = norm_label(label)
    if not s:
        return True
    if spec_prefix_pattern.search(s):
        return True
    if color_size_pattern.search(s):
        return True
    if size_pattern.search(s) and len(s) <= 14:
        return True
    # “1组... / 2袋... / 150*200cm...”这类纯规格。
    if measurement_pattern.search(s) and not has_product_term(s):
        return True
    # 含尺寸/容量且以“款、规格、颜色、尺寸”等为主，通常是规格。
    if measurement_pattern.search(s) and any(k in s for k in ["规格", "标准款", "单人款", "双人款", "尺寸", "尺码", "款", "色"]):
        # 但“宫廷公主落地蚊帐 三开门...”这类商品名本身不应被过滤。
        if not has_product_term(s) or s.startswith(("规格", "标准款", "单人款", "双人款", "平铺")):
            return True
    if len(s) <= 10 and any(k in s for k in ["任选", "颜色", "尺码", "款", "色"]):
        return True
    return False


def is_noise(label: str) -> bool:
    s = norm_label(label)
    if not s:
        return True
    if s in blocked_exact:
        return True
    if date_pattern.match(s):
        return True
    if any(key in s for key in blocked_contains):
        return True
    if len(s) < 2:
        return True
    if not text_pattern.search(s):
        return True
    if re.fullmatch(r"[\d\W_]+", s):
        return True
    return False


def is_likely_product_name(label: str) -> bool:
    s = norm_label(label)
    if is_noise(s):
        return False
    if is_price_or_price_fragment(s):
        return False
    if is_spec_line(s):
        return False

    product_like = has_product_term(s)

    # 有商品词，通常就是商品名。
    if product_like and len(s) >= 3:
        return True

    # 没有明显商品词，但较长中文短语也可能是商品名，例如品牌 + 系列名。
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", s))
    if chinese_chars >= 8 and len(s) >= 8:
        return True

    return False


candidates = []
for element in data.get("elements", []):
    label = norm_label(element.get("label", ""))
    rect = element.get("rect") or []
    kind = str(element.get("kind", ""))

    if not label or len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    # 商品列表主体区域。尽量避开顶部小程序壳、日期和底部 Tab。
    if y < 135 or y > 810:
        continue
    if w < 8 or h < 6:
        continue

    if not is_likely_product_name(label):
        continue

    cx = x + w / 2
    cy = y + h / 2
    column = "left" if cx < 195 else "right"

    candidates.append({
        "page": page_index,
        "title": label,
        "rect": [x, y, w, h],
        "kind": kind,
        "column": column,
        "card_top_y": y,
        "tap_x": round(cx, 2),
        "tap_y": round(cy, 2),
        "note": "name_only; specs_and_price_should_be_collected_from_detail_page",
    })

# 同一页先按视觉顺序排序：上到下，同一行左到右。
candidates.sort(key=lambda item: (round(item["card_top_y"] / 20), item["card_top_y"], 0 if item["column"] == "left" else 1))

added = []
for item in candidates:
    if current_count + len(added) >= limit:
        break

    key = normalize_key(item["title"])
    if not key or key in seen:
        continue

    added.append((key, item))
    seen.add(key)

with open(seen_file, "a", encoding="utf-8") as f_seen, open(result_file, "a", encoding="utf-8") as f_result:
    for key, item in added:
        f_seen.write(key + "\n")
        f_result.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")

print(len(added))
PYCOLLECT_V13_NAMES_ONLY
}

cmd_collect_new_products() {
  local mini_program="良久素材" limit=50 max_scrolls="$PRODUCT_MAX_SCROLLS" dry_run=0 skip_open=0
  local out_dir="" new_products_x="" new_products_y="" mini_program_result_x="" mini_program_result_y=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mini-program) mini_program="${2:-}"; shift 2 ;;
      --limit) limit="${2:-}"; shift 2 ;;
      --count) limit="${2:-}"; shift 2 ;;
      --max-scrolls) max_scrolls="${2:-}"; shift 2 ;;
      --out-dir) out_dir="${2:-}"; shift 2 ;;
      --new-products-x) new_products_x="${2:-}"; shift 2 ;;
      --new-products-y) new_products_y="${2:-}"; shift 2 ;;
      --mini-program-result-x) mini_program_result_x="${2:-}"; shift 2 ;;
      --mini-program-result-y) mini_program_result_y="${2:-}"; shift 2 ;;
      --skip-open) skip_open=1; shift ;;
      --dry-run) dry_run=1; shift ;;
      *) die_json "INVALID_ARGUMENT" "未知参数：$1" ;;
    esac
  done

  [[ "$limit" =~ ^[0-9]+$ ]] && [[ "$limit" -ge 1 ]] && [[ "$limit" -le 200 ]] || die_json "INVALID_LIMIT" "--limit/--count 必须是 1 到 200 的整数"
  [[ "$max_scrolls" =~ ^[0-9]+$ ]] || die_json "INVALID_MAX_SCROLLS" "--max-scrolls 必须是整数"

  [[ -n "$new_products_x" ]] && NEW_PRODUCTS_X="$new_products_x"
  [[ -n "$new_products_y" ]] && NEW_PRODUCTS_Y="$new_products_y"
  [[ -n "$mini_program_result_x" ]] && MINI_PROGRAM_RESULT_X="$mini_program_result_x"
  [[ -n "$mini_program_result_y" ]] && MINI_PROGRAM_RESULT_Y="$mini_program_result_y"

  init_runtime
  assert_ready
  acquire_lock

  if [[ $skip_open -eq 0 ]]; then
    open_mini_program_internal "$mini_program"
  else
    log "已启用 --skip-open，跳过打开微信和搜索小程序；请确认当前已经在良久首页或新品首发页"
  fi

  enter_new_products_internal

  if [[ $dry_run -eq 1 ]]; then
    python3 - "$mini_program" "$limit" <<'PYJSON'
import json, sys
print(json.dumps({
    "ok": True,
    "action": "collect-new-product-names",
    "dry_run": True,
    "mini_program": sys.argv[1],
    "limit": int(sys.argv[2]),
    "positioned_at": "新品首发",
    "note": "dry-run 只进入新品首发，不采集商品名称，也不滚动页面。",
}, ensure_ascii=False))
PYJSON
    return 0
  fi

  if [[ -z "$out_dir" ]]; then
    out_dir="$STATE_DIR/new-products-$(date +%Y%m%d-%H%M%S)"
  fi
  mkdir -p "$out_dir"

  local result_file="$out_dir/products.jsonl"
  local seen_file="$out_dir/seen-keys.txt"
  local summary_file="$out_dir/summary.json"
  : > "$result_file"
  : > "$seen_file"

  local collected=0
  local scroll_index=0
  local page_index=1
  local previous_signature=""

  while [[ $collected -lt $limit && $scroll_index -le $max_scrolls ]]; do
    local page_name
    page_name="$(printf '%03d' "$page_index")"
    local page_file="$out_dir/page-${page_name}.json"

    log "采集新品首发第 ${page_index} 页元素：当前 ${collected}/${limit}"
    save_elements "$page_file"

    local added
    added="$(append_visible_products_from_page "$page_file" "$seen_file" "$result_file" "$page_index" "$limit")"
    if [[ -z "$added" ]]; then
      added=0
    fi
    collected=$((collected + added))
    log "第 ${page_index} 页新增候选商品：${added}；累计：${collected}/${limit}"

    if [[ $collected -ge $limit ]]; then
      break
    fi

    local current_signature
    current_signature="$(page_signature "$page_file")"

    if [[ -n "$previous_signature" && "$current_signature" == "$previous_signature" ]]; then
      log "页面元素没有变化，停止继续滚动"
      break
    fi
    previous_signature="$current_signature"

    if [[ $scroll_index -ge $max_scrolls ]]; then
      break
    fi

    # 浏览更多商品：这里默认 dy=320。之前 dy=-320 会在顶部触发下拉刷新。
    log "向下浏览更多商品：x=${PRODUCT_SCROLL_X} y=${PRODUCT_SCROLL_Y} dy=${PRODUCT_SCROLL_DY}"
    phone_act "{\"type\":\"scroll\",\"x\":$PRODUCT_SCROLL_X,\"y\":$PRODUCT_SCROLL_Y,\"dx\":0,\"dy\":$PRODUCT_SCROLL_DY}" >/dev/null
    sleep 2

    scroll_index=$((scroll_index + 1))
    page_index=$((page_index + 1))
  done

  python3 - "$mini_program" "$limit" "$scroll_index" "$out_dir" "$result_file" "$summary_file" <<'PYRESULT'
import json
import sys
from pathlib import Path

mini_program, limit, scrolls, out_dir, result_file, summary_file = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
items = []
path = Path(result_file)
if path.exists():
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            item["index"] = len(items) + 1
            items.append(item)

target_reached = len(items) >= limit
summary = {
    "ok": True,
    "action": "collect-new-product-names",
    "mini_program": mini_program,
    "source_page": "新品首发",
    "target_count": limit,
    "collected_count": len(items),
    "target_reached": target_reached,
    "completion_reason": "target_reached" if target_reached else "end_reached_or_no_more_recognizable_products",
    "scroll_count": scrolls,
    "out_dir": out_dir,
    "products_jsonl": result_file,
    "product_names": [item.get("title", "") for item in items[:limit]],
    "products": items[:limit],
    "warning": None if target_reached else "新品首发可能已经到底，或页面中可由元素树稳定识别的商品名称不足目标数量；本次仍返回已清洗的商品名称列表。",
}
Path(summary_file).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False))
PYRESULT
}

# 兼容旧命令名：select-new-products 现在不再点击商品，而是采集新品首发前 N 个商品候选信息。
cmd_select_new_products() {
  cmd_collect_new_products "$@"
}

cmd_elements() {
  local group=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --group) group="${2:-}"; shift 2 ;;
      *) die_json "INVALID_ARGUMENT" "未知参数：$1" ;;
    esac
  done
  init_runtime
  assert_ready
  acquire_lock
  if [[ -n "$group" ]]; then
    assert_allowed_group "$group"
    open_group_internal "$group"
  fi
  phone_elements
}

usage() {
  cat <<'USAGE'
用法：
  wechat-iphone doctor
  wechat-iphone status
  wechat-iphone start-daemon
  wechat-iphone start-wda
  wechat-iphone start
  wechat-iphone restart
  wechat-iphone stop-wda
  wechat-iphone stop
  wechat-iphone open-group --group "群聊名称"
  wechat-iphone send --group "群聊名称" --message "消息正文" [--dry-run]
  wechat-iphone read --group "群聊名称" [--pages N] [--out-dir DIR]
  wechat-iphone elements [--group "群聊名称"]
  wechat-iphone collect-new-products [--limit 50] [--max-scrolls N] [--out-dir DIR] [--new-products-x 0.105 --new-products-y 0.805] [--skip-open] [--dry-run]
  wechat-iphone select-new-products [--limit 50] [--max-scrolls N] [--out-dir DIR] [--new-products-x 0.105 --new-products-y 0.805] [--skip-open] [--dry-run]
    说明：select-new-products 为兼容旧命令名，现在不再点击商品，只采集新品首发商品名称。

启动说明：
  - iphone-use 通过 com.leeguoo.iphone-use LaunchAgent 启动。
  - WDA 通过独立的 com.leeguoo.iphone-use.wda LaunchAgent 启动。
  - WDA 服务实际执行已验证命令：WDA_KEEPALIVE=1 + WDA_TEAM_ID + WDA_UDID。
  - 不传 WDA_BUNDLE_ID；签名 Team 与 Bundle ID 复用 Xcode 项目中的有效配置。
  - 启动 WDA 前自动退出 Xcode GUI 与 iPhone 镜像，并要求 USB 识别目标设备。

环境变量：
  WECHAT_IPHONE_PROJECT_DIR          默认 $HOME/path/to/iphone-use
  WECHAT_IPHONE_WDA_SCRIPT           默认 <项目>/scripts/setup-wda.sh
  WDA_TEAM_ID                        默认 <APPLE_TEAM_ID>
  WDA_UDID                           默认 <IPHONE_UDID>
  WECHAT_IPHONE_CONFIG               允许群配置文件
  WECHAT_IPHONE_HOST                 默认 http://127.0.0.1:44321
  WECHAT_IPHONE_TOKEN_FILE           默认 ~/.iphone-use/agent-token
  WECHAT_IPHONE_WDA_START_TIMEOUT    默认 300 秒
  WECHAT_IPHONE_SEARCH_X/Y           搜索栏坐标
  WECHAT_IPHONE_FIRST_RESULT_X/Y     第一条搜索结果坐标
  WECHAT_IPHONE_INPUT_X/Y            消息输入框坐标
  WECHAT_IPHONE_NEW_PRODUCTS_X/Y     新品首发入口坐标，只在点击“新品首发”时使用；当前截图建议 0.105 / 0.805
  WECHAT_IPHONE_MINI_PROGRAM_RESULT_X/Y  最近使用过的小程序第一条坐标，默认沿用 FIRST_RESULT_X/Y
USAGE
}

main() {
  local command="${1:-}"
  [[ $# -gt 0 ]] && shift
  case "$command" in
    doctor) cmd_doctor "$@" ;;
    status) cmd_status "$@" ;;
    start-daemon) cmd_start_daemon "$@" ;;
    start-wda) cmd_start_wda "$@" ;;
    start) cmd_start "$@" ;;
    restart) cmd_restart "$@" ;;
    stop-wda) cmd_stop_wda "$@" ;;
    stop) cmd_stop "$@" ;;
    open-group) cmd_open_group "$@" ;;
    send) cmd_send "$@" ;;
    read) cmd_read "$@" ;;
    elements) cmd_elements "$@" ;;
    collect-new-products) cmd_collect_new_products "$@" ;;
    select-new-products) cmd_select_new_products "$@" ;;
    help|-h|--help|"") usage ;;
    *) die_json "UNKNOWN_COMMAND" "未知命令：$command" ;;
  esac
}

main "$@"
