#!/usr/bin/env bash
# wechat-iphone-scenario4-v2
# 从最终推广文案提取小程序商品链接，经“文件传输助手”打开商品，
# 再通过“分享好友 → 微信好友”分享到指定微信群。
# macOS / Bash 3.2 compatible

set -uo pipefail
IFS=$'\n\t'

STATE_DIR="${WECHAT_IPHONE_STATE_DIR:-$HOME/.iphone-use/wechat-iphone}"
TOKEN_FILE="${WECHAT_IPHONE_TOKEN_FILE:-$HOME/.iphone-use/agent-token}"
HOST="${WECHAT_IPHONE_HOST:-http://127.0.0.1:44321}"
APP_BUNDLE="${WECHAT_IPHONE_APP_BUNDLE:-com.tencent.xin}"

DEFAULT_PROMOTION_FILE="./scenario3-final-promotion.txt"
DEFAULT_TRANSFER_CHAT="文件传输助手"
DEFAULT_TARGET_GROUP="${WECHAT_IPHONE_TARGET_GROUP:-}"

SEARCH_X="${WECHAT_IPHONE_SEARCH_X:-0.50}"
SEARCH_Y="${WECHAT_IPHONE_SEARCH_Y:-0.12}"
SEARCH_TYPE_DELAY="${WECHAT_IPHONE_SEARCH_TYPE_DELAY:-0.25}"

MESSAGE_INPUT_X="${WECHAT_IPHONE_MESSAGE_INPUT_X:-0.48}"
MESSAGE_INPUT_Y="${WECHAT_IPHONE_MESSAGE_INPUT_Y:-0.92}"

DETAIL_SCROLL_X="${WECHAT_IPHONE_DETAIL_SCROLL_X:-0.50}"
DETAIL_SCROLL_Y="${WECHAT_IPHONE_DETAIL_SCROLL_Y:-0.72}"
DETAIL_SCROLL_DY="${WECHAT_IPHONE_DETAIL_SCROLL_DY:-300}"
MAX_DETAIL_SCROLLS="${WECHAT_IPHONE_MAX_DETAIL_SCROLLS:-12}"
SHARE_CONFIRM_SEND_X="${WECHAT_IPHONE_SHARE_CONFIRM_SEND_X:-0.675}"
SHARE_CONFIRM_SEND_Y="${WECHAT_IPHONE_SHARE_CONFIRM_SEND_Y:-0.865}"

mkdir -p "$STATE_DIR"
LOCK_DIR="$STATE_DIR/controller.lock"
TOKEN=""
RUN_DIR=""
RESULTS_JSONL=""
LINKS_FILE=""

log() {
  printf '[wechat-iphone] %s\n' "$*" >&2
}

die_json() {
  local code="$1"
  local message="$2"
  local exit_code="${3:-1}"

  python3 - "$code" "$message" <<'PY'
import json
import sys

print(json.dumps({
    "ok": False,
    "error": sys.argv[1],
    "message": sys.argv[2],
}, ensure_ascii=False))
PY
  exit "$exit_code"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 \
    || die_json "MISSING_COMMAND" "缺少命令: $1"
}

init_runtime() {
  require_cmd curl
  require_cmd python3

  if [[ ! -f "$TOKEN_FILE" ]]; then
    die_json "TOKEN_NOT_FOUND" "找不到 iphone-use token: $TOKEN_FILE"
  fi

  TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"

  if [[ -z "$TOKEN" ]]; then
    die_json "TOKEN_EMPTY" "iphone-use token 为空: $TOKEN_FILE"
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

  curl --noproxy "*" -sS --max-time 40 \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -X POST \
    "$HOST/agent/input" \
    -d "$payload"
}

json_text_payload() {
  python3 - "$1" <<'PY'
import json
import sys

print(json.dumps({
    "type": "text",
    "text": sys.argv[1],
}, ensure_ascii=False))
PY
}

json_text_clear_payload() {
  python3 - "$1" <<'PY'
import json
import sys

print(json.dumps({
    "type": "text",
    "text": sys.argv[1],
    "clear": True,
}, ensure_ascii=False))
PY
}

json_tap_label_payload() {
  python3 - "$1" <<'PY'
import json
import sys

print(json.dumps({
    "type": "tap",
    "label": sys.argv[1],
}, ensure_ascii=False))
PY
}

json_tap_xy_payload() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

print(json.dumps({
    "type": "tap",
    "x": float(sys.argv[1]),
    "y": float(sys.argv[2]),
}, ensure_ascii=False))
PY
}

json_launch_payload() {
  python3 - "$1" <<'PY'
import json
import sys

print(json.dumps({
    "type": "launch_app",
    "bundle": sys.argv[1],
}, ensure_ascii=False))
PY
}

json_scroll_payload() {
  python3 - "$1" "$2" "$3" <<'PY'
import json
import sys

print(json.dumps({
    "type": "scroll",
    "x": float(sys.argv[1]),
    "y": float(sys.argv[2]),
    "dx": 0,
    "dy": float(sys.argv[3]),
}, ensure_ascii=False))
PY
}

status_ready_from_stdin() {
  python3 -c '
import json
import sys

try:
    status = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)

ready = all([
    status.get("ok") is True,
    status.get("wda") is True,
    status.get("wda_actionable") is True,
    status.get("wda_locked") is False,
    status.get("drivable") is True,
    status.get("mode") == "agent",
])

raise SystemExit(0 if ready else 1)
'
}

assert_ready() {
  local raw=""

  if ! raw="$(phone_status 2>/dev/null)"; then
    die_json "IPHONE_USE_UNREACHABLE" "无法访问 ${HOST}/agent/status"
  fi

  if ! printf '%s' "$raw" | status_ready_from_stdin; then
    printf '%s\n' "$raw" >&2
    die_json \
      "IPHONE_NOT_READY" \
      "需要 ok=true, wda=true, wda_actionable=true, wda_locked=false, drivable=true, mode=agent"
  fi
}

save_elements() {
  local file="$1"

  if ! phone_elements > "$file"; then
    die_json "ELEMENTS_FAILED" "读取元素树失败: $file"
  fi

  if ! python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    json.load(f)
PY
  then
    die_json "ELEMENTS_INVALID_JSON" "元素树不是有效 JSON: $file"
  fi
}

file_contains_label() {
  local file="$1"
  local needle="$2"

  python3 - "$file" "$needle" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

needle = sys.argv[2]

for element in data.get("elements", []):
    label = str(element.get("label", ""))
    value = str(element.get("value", ""))

    if needle in label or needle in value:
        raise SystemExit(0)

raise SystemExit(1)
PY
}

find_label_payload() {
  local file="$1"
  local needle="$2"

  python3 - "$file" "$needle" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

needle = sys.argv[2]
screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    value = str(element.get("value", "")).strip()
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < 0 or y > screen_h or w <= 0 or h <= 0:
        continue

    combined = f"{label} {value}"

    if needle not in combined:
        continue

    score = 0
    if label == needle or value == needle:
        score += 200
    if kind == "Button":
        score += 100
    score -= int(y)

    candidates.append((score, x, y, w, h, kind, label, value))

if not candidates:
    raise SystemExit(1)

score, x, y, w, h, kind, label, value = sorted(
    candidates,
    key=lambda item: (-item[0], item[2], item[1]),
)[0]

if kind == "Button" and label:
    print(json.dumps({
        "type": "tap",
        "label": label,
    }, ensure_ascii=False))
else:
    print(json.dumps({
        "type": "tap",
        "x": (x + w / 2) / screen_w,
        "y": (y + h / 2) / screen_h,
    }, ensure_ascii=False))
PY
}

is_chat_list_file() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

visible = []

for element in data.get("elements", []):
    label = str(element.get("label", "")).strip()
    rect = element.get("rect") or []

    if not label or len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if -50 <= x <= 450 and 0 <= y <= 852:
        visible.append((label, y))

has_search = any(
    "搜索" in label and y < 220
    for label, y in visible
)

tabs = ("微信", "通讯录", "发现", "我")
tab_hits = sum(
    1
    for tab in tabs
    if any(label == tab and y > 650 for label, y in visible)
)

raise SystemExit(0 if has_search and tab_hits >= 2 else 1)
PY
}

find_top_right_mini_program_close_payload() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

visible = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < 0 or y > screen_h:
        continue

    visible.append((kind, label, x, y, w, h))

has_more = any(
    kind == "Button"
    and "更多" in label
    and x > screen_w * 0.60
    and y < 150
    for kind, label, x, y, w, h in visible
)

close_candidates = [
    (x, y, w, h, label)
    for kind, label, x, y, w, h in visible
    if (
        kind == "Button"
        and "关闭" in label
        and x > screen_w * 0.72
        and y < 150
    )
]

if not has_more or not close_candidates:
    raise SystemExit(1)

x, y, w, h, label = sorted(
    close_candidates,
    key=lambda row: -row[0],
)[0]

print(json.dumps({
    "type": "tap",
    "x": (x + w / 2) / screen_w,
    "y": (y + h / 2) / screen_h,
}, ensure_ascii=False))
PY
}

find_top_left_back_payload() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if (
        kind == "Button"
        and ("返回" in label or label in {"Back", "back"})
        and -20 <= x < screen_w * 0.30
        and 0 <= y < 170
    ):
        candidates.append((y, x, w, h, label))

if not candidates:
    raise SystemExit(1)

y, x, w, h, label = sorted(candidates)[0]

print(json.dumps({
    "type": "tap",
    "x": (x + w / 2) / screen_w,
    "y": (y + h / 2) / screen_h,
}, ensure_ascii=False))
PY
}

return_to_chat_list() {
  local file="$RUN_DIR/return-chat-list.json"
  local attempt=1
  local payload=""

  while [[ $attempt -le 14 ]]; do
    save_elements "$file"

    if is_chat_list_file "$file"; then
      return 0
    fi

    payload=""

    if payload="$(find_top_right_mini_program_close_payload "$file" 2>/dev/null)"; then
      log "检测到微信小程序，点击右上角关闭: ${payload}"
      phone_act "$payload" >/dev/null 2>&1 || true
      sleep 2
      attempt=$((attempt + 1))
      continue
    fi

    if payload="$(find_top_left_back_payload "$file" 2>/dev/null)"; then
      log "点击左上角返回: ${payload}"
      phone_act "$payload" >/dev/null 2>&1 || true
    else
      log "未识别到返回按钮，使用左上角安全坐标"
      phone_act "$(json_tap_xy_payload 0.055 0.085)" >/dev/null 2>&1 || true
    fi

    sleep 1.5
    attempt=$((attempt + 1))
  done

  save_elements "$file"
  is_chat_list_file "$file"
}

find_clear_payload() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    rect = element.get("rect") or []

    if "清除" not in label or len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if 0 <= y < 220:
        print(json.dumps({
            "type": "tap",
            "x": (x + w / 2) / screen_w,
            "y": (y + h / 2) / screen_h,
        }, ensure_ascii=False))
        raise SystemExit(0)

raise SystemExit(1)
PY
}

clear_search_if_possible() {
  local file="$RUN_DIR/search-before-clear.json"
  local payload=""

  save_elements "$file"

  if payload="$(find_clear_payload "$file" 2>/dev/null)"; then
    phone_act "$payload" >/dev/null 2>&1 || true
    sleep 0.5
  fi
}

type_text_character_by_character() {
  local text="$1"
  local delay="${2:-0.25}"

  python3 - "$text" <<'PY' |
import json
import sys

for character in sys.argv[1]:
    print(json.dumps({
        "type": "text",
        "text": character,
    }, ensure_ascii=False))
PY
  while IFS= read -r payload; do
    [[ -n "$payload" ]] || continue
    phone_act "$payload" >/dev/null
    sleep "$delay"
  done
}

find_safe_search_result_payload() {
  local file="$1"
  local target="$2"

  python3 - "$file" "$target" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

target_raw = sys.argv[2]

def norm(value):
    value = str(value or "")
    value = re.sub(
        r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u2000-\u200a]",
        "",
        value,
    )
    value = re.sub(r"\s+", " ", value).strip()
    return value

target = norm(target_raw)
screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

rows = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = norm(element.get("label", ""))
    value = norm(element.get("value", ""))
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < 0 or y > screen_h or w <= 0 or h <= 0:
        continue

    rows.append({
        "kind": kind,
        "label": label,
        "value": value,
        "text": label or value,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    })

def first_y(terms):
    values = [
        row["y"]
        for row in rows
        if any(term in row["text"] for term in terms)
    ]
    return min(values) if values else None

chat_records_y = first_y(("聊天记录", "更多聊天记录"))
network_y = first_y(("搜索网络结果", "搜索网络", "搜一搜"))

upper_limit = screen_h * 0.75

if chat_records_y is not None:
    upper_limit = min(upper_limit, chat_records_y - 2)

if network_y is not None:
    upper_limit = min(upper_limit, network_y - 2)

count_pattern = re.compile(
    rf"^{re.escape(target)}\s*[（(]\s*\d+\s*[)）]$"
)

negative_terms = (
    "文章",
    "公众号",
    "小程序",
    "聊天记录",
    "朋友圈",
    "搜一搜",
    "网络搜索",
    "搜索网络",
    "视频号",
)

candidates = []

for row in rows:
    label = row["label"]
    value = row["value"]
    combined = norm(f"{label} {value}")

    exact = label == target or value == target
    with_count = bool(
        count_pattern.fullmatch(label)
        or count_pattern.fullmatch(value)
    )

    if not exact and not with_count:
        continue

    if row["y"] < 115 or row["y"] >= upper_limit:
        continue

    if any(term in combined for term in negative_terms):
        continue

    score = 0

    if exact:
        score += 500

    if with_count:
        score += 450

    if row["kind"] == "Button":
        score += 80

    score -= int(row["y"])

    candidates.append((score, row))

if not candidates:
    raise SystemExit(1)

score, row = sorted(
    candidates,
    key=lambda item: (-item[0], item[1]["y"], item[1]["x"]),
)[0]

print(
    "[wechat-iphone] 选中搜索结果: "
    f"target={target!r}, "
    f"label={row['label']!r}, "
    f"kind={row['kind']}, "
    f"rect={[row['x'], row['y'], row['w'], row['h']]}",
    file=sys.stderr,
)

print(json.dumps({
    "type": "tap",
    "x": 0.50,
    "y": (row["y"] + row["h"] / 2) / screen_h,
}, ensure_ascii=False))
PY
}

strip_member_count_python='
import re

def norm(value):
    value = str(value or "")
    value = re.sub(
        r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u2000-\u200a]",
        "",
        value,
    )
    value = re.sub(r"\s+", " ", value).strip()
    return value

def strip_member_count(value):
    value = norm(value)
    value = re.sub(
        r"\s*[（(]\s*\d+\s*[)）]\s*$",
        "",
        value,
    ).strip()
    return value
'

is_target_chat_file() {
  local file="$1"
  local target="$2"

  python3 - "$file" "$target" <<PY
import json
import re
import sys

${strip_member_count_python}

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

target = strip_member_count(sys.argv[2])
screen = data.get("screen") or {}
screen_h = float(screen.get("height") or 852)

has_header = False
has_search = False
has_chat_surface = False

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = norm(element.get("label", ""))
    value = norm(element.get("value", ""))
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < 0 or y > screen_h:
        continue

    if y < 155:
        for raw in (label, value):
            if raw and strip_member_count(raw) == target:
                has_header = True

    if kind == "SearchField" and y < 190:
        has_search = True

    combined = f"{label} {value}"

    if y > screen_h * 0.65 and (
        kind in {"TextView", "TextField"}
        or any(
            term in combined
            for term in (
                "输入",
                "发送",
                "表情",
                "语音",
                "按住说话",
                "更多功能",
            )
        )
    ):
        has_chat_surface = True

raise SystemExit(
    0
    if has_header and not has_search and has_chat_surface
    else 1
)
PY
}

open_chat_from_list() {
  local target="$1"
  local search_file="$RUN_DIR/search-${target}.json"
  local verify_file="$RUN_DIR/chat-${target}.json"
  local payload=""
  local attempt=1

  log "打开微信并返回聊天列表"
  phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null
  sleep 3

  if ! return_to_chat_list; then
    die_json "CHAT_LIST_NOT_FOUND" "无法返回微信聊天列表"
  fi

  log "搜索会话: ${target}"
  phone_act "$(json_tap_xy_payload "$SEARCH_X" "$SEARCH_Y")" >/dev/null
  sleep 1

  clear_search_if_possible

  log "逐字输入: ${target}"
  type_text_character_by_character "$target" "$SEARCH_TYPE_DELAY"

  payload=""
  attempt=1

  while [[ $attempt -le 8 ]]; do
    sleep 1
    save_elements "$search_file"

    if payload="$(find_safe_search_result_payload "$search_file" "$target")"; then
      phone_act "$payload" >/dev/null
      break
    fi

    attempt=$((attempt + 1))
  done

  if [[ -z "$payload" ]]; then
    die_json \
      "CHAT_SEARCH_RESULT_NOT_FOUND" \
      "未找到安全、完全匹配的会话结果: ${target}"
  fi

  attempt=1

  while [[ $attempt -le 8 ]]; do
    sleep 1
    save_elements "$verify_file"

    if is_target_chat_file "$verify_file" "$target"; then
      log "已进入目标会话: ${target}"
      return 0
    fi

    attempt=$((attempt + 1))
  done

  die_json "TARGET_CHAT_NOT_VERIFIED" "未能验证进入会话: ${target}"
}

find_message_input_payload() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    value = str(element.get("value", "")).strip()
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < screen_h * 0.65 or y > screen_h:
        continue

    combined = f"{label} {value}"
    score = 0

    if kind in {"TextView", "TextField"}:
        score += 100

    if "输入" in combined:
        score += 80

    if w > screen_w * 0.35:
        score += 40

    if score > 0:
        candidates.append((score, y, x, w, h))

if not candidates:
    raise SystemExit(1)

score, y, x, w, h = sorted(
    candidates,
    key=lambda item: (-item[0], -item[1]),
)[0]

print(json.dumps({
    "type": "tap",
    "x": (x + w / 2) / screen_w,
    "y": (y + h / 2) / screen_h,
}, ensure_ascii=False))
PY
}

find_send_payload() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    value = str(element.get("value", "")).strip()
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    combined = f"{label} {value}"

    if label != "发送" and value != "发送" and "发送" not in combined:
        continue

    cx = x + w / 2
    cy = y + h / 2

    if cx < screen_w * 0.68:
        continue

    if cy < screen_h * 0.30 or cy > screen_h * 0.85:
        continue

    score = 0

    if label == "发送" or value == "发送":
        score += 500

    if kind == "Button":
        score += 300

    if 25 <= w <= 130 and 25 <= h <= 100:
        score += 100

    candidates.append((score, x, y, w, h, kind, label))

if not candidates:
    raise SystemExit(1)

score, x, y, w, h, kind, label = sorted(
    candidates,
    key=lambda item: (-item[0], item[2]),
)[0]

if kind == "Button" and label == "发送":
    print(json.dumps({
        "type": "tap",
        "label": "发送",
    }, ensure_ascii=False))
else:
    print(json.dumps({
        "type": "tap",
        "x": (x + w / 2) / screen_w,
        "y": (y + h / 2) / screen_h,
    }, ensure_ascii=False))
PY
}

send_text_to_current_chat() {
  local text="$1"
  local before_input="$RUN_DIR/before-input.json"
  local before_send="$RUN_DIR/before-send.json"
  local payload=""

  save_elements "$before_input"

  if payload="$(find_message_input_payload "$before_input" 2>/dev/null)"; then
    phone_act "$payload" >/dev/null
  else
    phone_act \
      "$(json_tap_xy_payload "$MESSAGE_INPUT_X" "$MESSAGE_INPUT_Y")" \
      >/dev/null
  fi

  sleep 0.6

  phone_act "$(json_text_payload "$text")" >/dev/null
  sleep 1

  save_elements "$before_send"

  if payload="$(find_send_payload "$before_send")"; then
    log "点击发送按钮: ${payload}"
    phone_act "$payload" >/dev/null
  else
    die_json \
      "SEND_BUTTON_NOT_FOUND" \
      "输入商品链接后未识别到“发送”按钮，已停止"
  fi

  sleep 2
}

find_latest_link_payload() {
  local file="$1"
  local link="$2"

  python3 - "$file" "$link" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

link = sys.argv[2]
token = link.rsplit("/", 1)[-1]
screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", ""))
    value = str(element.get("value", ""))
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < 100 or y > screen_h * 0.82 or w <= 0 or h <= 0:
        continue

    combined = f"{label}\n{value}"

    if link not in combined and token not in combined:
        continue

    score = int(y * 10)

    if kind in {"Link", "StaticText", "Button"}:
        score += 100

    candidates.append((score, x, y, w, h, kind, label))

if not candidates:
    raise SystemExit(1)

score, x, y, w, h, kind, label = sorted(
    candidates,
    key=lambda item: (-item[0], -item[2]),
)[0]

print(
    "[wechat-iphone] 选中最新商品链接: "
    f"kind={kind}, rect={[x, y, w, h]}, label={label!r}",
    file=sys.stderr,
)

print(json.dumps({
    "type": "tap",
    "x": (x + w / 2) / screen_w,
    "y": (y + h / 2) / screen_h,
}, ensure_ascii=False))
PY
}

click_sent_link() {
  local link="$1"
  local file="$RUN_DIR/file-transfer-after-send.json"
  local payload=""
  local attempt=1

  while [[ $attempt -le 8 ]]; do
    save_elements "$file"

    if payload="$(find_latest_link_payload "$file" "$link")"; then
      log "点击文件传输助手中的商品链接"
      phone_act "$payload" >/dev/null
      return 0
    fi

    sleep 1
    attempt=$((attempt + 1))
  done

  die_json \
    "SENT_LINK_NOT_FOUND" \
    "未在文件传输助手中找到刚发送的商品链接: ${link}"
}

allow_open_mini_program() {
  local file="$RUN_DIR/allow-mini-program.json"
  local payload=""
  local attempt=1

  while [[ $attempt -le 12 ]]; do
    sleep 1
    save_elements "$file"

    if file_contains_label "$file" "即将打开"; then
      if payload="$(find_label_payload "$file" "允许" 2>/dev/null)"; then
        log "检测到“即将打开良久素材小程序”，点击允许"
        phone_act "$payload" >/dev/null
        return 0
      fi
    fi

    attempt=$((attempt + 1))
  done

  die_json \
    "ALLOW_DIALOG_NOT_FOUND" \
    "未找到“即将打开良久素材小程序”的允许窗口"
}

wait_for_product_detail() {
  local file="$RUN_DIR/product-detail.json"
  local attempt=1

  while [[ $attempt -le 20 ]]; do
    sleep 1
    save_elements "$file"

    if file_contains_label "$file" "分享好友"       || file_contains_label "$file" "立即报单"       || file_contains_label "$file" "已选："
    then
      log "已进入商品详情页"
      return 0
    fi

    attempt=$((attempt + 1))
  done

  die_json \
    "PRODUCT_DETAIL_NOT_VERIFIED" \
    "点击允许后未能验证进入商品详情页"
}

find_visible_share_friend_payload() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    value = str(element.get("value", "")).strip()
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    combined = f"{label} {value}"

    if "分享好友" not in combined:
        continue

    if x < -50 or y < 0 or y > screen_h or w <= 0 or h <= 0:
        continue

    score = 0

    if label == "分享好友" or value == "分享好友":
        score += 300

    if kind == "Button":
        score += 100

    score += int(y)

    candidates.append((score, x, y, w, h, kind, label))

if not candidates:
    raise SystemExit(1)

score, x, y, w, h, kind, label = sorted(
    candidates,
    key=lambda item: (-item[0], -item[2]),
)[0]

if kind == "Button" and label:
    print(json.dumps({
        "type": "tap",
        "label": label,
    }, ensure_ascii=False))
else:
    print(json.dumps({
        "type": "tap",
        "x": (x + w / 2) / screen_w,
        "y": (y + h / 2) / screen_h,
    }, ensure_ascii=False))
PY
}

open_share_method_sheet() {
  local file="$RUN_DIR/product-detail-share.json"
  local payload=""
  local scroll_count=0

  while [[ $scroll_count -le $MAX_DETAIL_SCROLLS ]]; do
    save_elements "$file"

    if payload="$(find_visible_share_friend_payload "$file" 2>/dev/null)"; then
      log "点击商品详情页“分享好友”"
      phone_act "$payload" >/dev/null
      break
    fi

    if [[ $scroll_count -eq $MAX_DETAIL_SCROLLS ]]; then
      die_json \
        "SHARE_FRIEND_NOT_FOUND" \
        "滚动商品详情后仍未找到“分享好友”"
    fi

    log "商品详情向下浏览，查找“分享好友”: $((scroll_count + 1))/${MAX_DETAIL_SCROLLS}"

    phone_act \
      "$(json_scroll_payload "$DETAIL_SCROLL_X" "$DETAIL_SCROLL_Y" "$DETAIL_SCROLL_DY")" \
      >/dev/null

    sleep 1
    scroll_count=$((scroll_count + 1))
  done

  local sheet_file="$RUN_DIR/share-method-sheet.json"
  local attempt=1

  while [[ $attempt -le 10 ]]; do
    sleep 1
    save_elements "$sheet_file"

    if file_contains_label "$sheet_file" "通过以下方式分享"       || file_contains_label "$sheet_file" "微信好友"
    then
      log "已弹出“通过以下方式分享”"
      return 0
    fi

    attempt=$((attempt + 1))
  done

  die_json \
    "SHARE_METHOD_SHEET_NOT_FOUND" \
    "点击分享好友后未出现分享方式窗口"
}

click_wechat_friend_method() {
  local file="$RUN_DIR/share-method-sheet.json"
  local payload=""

  save_elements "$file"

  if payload="$(find_label_payload "$file" "微信好友" 2>/dev/null)"; then
    log "选择分享方式：微信好友"
    phone_act "$payload" >/dev/null
    sleep 2
    return 0
  fi

  die_json \
    "WECHAT_FRIEND_METHOD_NOT_FOUND" \
    "分享方式窗口中未找到“微信好友”"
}

find_search_field_payload() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = str(element.get("label", "")).strip()
    value = str(element.get("value", "")).strip()
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < 0 or y > screen_h * 0.55:
        continue

    combined = f"{label} {value}"

    if kind != "SearchField" and "搜索" not in combined:
        continue

    score = 0

    if kind == "SearchField":
        score += 200

    if "搜索" in combined:
        score += 100

    score -= int(y)

    candidates.append((score, x, y, w, h))

if not candidates:
    raise SystemExit(1)

score, x, y, w, h = sorted(
    candidates,
    key=lambda item: (-item[0], item[2]),
)[0]

print(json.dumps({
    "type": "tap",
    "x": (x + w / 2) / screen_w,
    "y": (y + h / 2) / screen_h,
}, ensure_ascii=False))
PY
}

find_picker_group_payload() {
  local file="$1"
  local group="$2"

  python3 - "$file" "$group" <<PY
import json
import re
import sys

${strip_member_count_python}

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

target = strip_member_count(sys.argv[2])
screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

candidates = []

for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = norm(element.get("label", ""))
    value = norm(element.get("value", ""))
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if x < -50 or y < 90 or y > screen_h * 0.82 or w <= 0 or h <= 0:
        continue

    if kind == "SearchField":
        continue

    matches = any(
        raw and strip_member_count(raw) == target
        for raw in (label, value)
    )

    if not matches:
        continue

    score = 0

    if kind in {"Cell", "Button"}:
        score += 100

    score -= int(y)

    candidates.append((score, x, y, w, h, kind, label))

if not candidates:
    raise SystemExit(1)

score, x, y, w, h, kind, label = sorted(
    candidates,
    key=lambda item: (-item[0], item[2]),
)[0]

print(
    "[wechat-iphone] 选择分享目标群聊: "
    f"label={label!r}, kind={kind}, rect={[x, y, w, h]}",
    file=sys.stderr,
)

print(json.dumps({
    "type": "tap",
    "x": (x + w / 2) / screen_w,
    "y": (y + h / 2) / screen_h,
}, ensure_ascii=False))
PY
}

select_share_target_group() {
  local group="$1"
  local picker_file="$RUN_DIR/share-contact-picker.json"
  local search_file="$RUN_DIR/share-contact-search.json"
  local payload=""
  local attempt=1

  while [[ $attempt -le 10 ]]; do
    save_elements "$picker_file"

    if payload="$(find_search_field_payload "$picker_file" 2>/dev/null)"; then
      log "点击微信好友选择页的搜索框"
      phone_act "$payload" >/dev/null
      break
    fi

    sleep 1
    attempt=$((attempt + 1))
  done

  if [[ -z "$payload" ]]; then
    die_json \
      "SHARE_CONTACT_SEARCH_NOT_FOUND" \
      "进入微信好友选择页后未找到搜索框"
  fi

  sleep 0.6

  log "逐字输入目标群聊: ${group}"
  type_text_character_by_character "$group" "$SEARCH_TYPE_DELAY"

  payload=""
  attempt=1

  while [[ $attempt -le 10 ]]; do
    sleep 1
    save_elements "$search_file"

    if payload="$(find_picker_group_payload "$search_file" "$group")"; then
      phone_act "$payload" >/dev/null
      sleep 1.5
      return 0
    fi

    attempt=$((attempt + 1))
  done

  die_json \
    "SHARE_TARGET_GROUP_NOT_FOUND" \
    "微信好友选择页中未找到目标群聊: ${group}"
}


is_share_confirm_file() {
  local file="$1"
  local group="$2"

  python3 - "$file" "$group" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

target = sys.argv[2]

def norm(value):
    value = str(value or "")
    value = re.sub(
        r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u2000-\u200a]",
        "",
        value,
    )
    value = re.sub(r"\s+", " ", value).strip()
    return value

def strip_count(value):
    value = norm(value)
    value = re.sub(
        r"\s*[（(]\s*\d+\s*(?:人)?\s*[)）]\s*$",
        "",
        value,
    ).strip()
    return value

target = strip_count(target)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

visible = []
for element in data.get("elements", []):
    kind = str(element.get("kind", ""))
    label = norm(element.get("label", ""))
    value = norm(element.get("value", ""))
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if (
        x < -50
        or y < 0
        or y > screen_h
        or w <= 0
        or h <= 0
    ):
        continue

    visible.append({
        "kind": kind,
        "label": label,
        "value": value,
        "text": norm(f"{label} {value}"),
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    })

has_send_to = any(
    "发送给" in row["text"]
    for row in visible
)

has_target_group = any(
    any(
        raw and strip_count(raw) == target
        for raw in (row["label"], row["value"])
    )
    for row in visible
)

has_cancel = any(
    (row["label"] == "取消" or row["value"] == "取消")
    and row["y"] > screen_h * 0.68
    for row in visible
)

has_bottom_send = any(
    (row["label"] == "发送" or row["value"] == "发送")
    and (row["x"] + row["w"] / 2) > screen_w * 0.50
    and (row["y"] + row["h"] / 2) > screen_h * 0.72
    for row in visible
)

ok = (
    has_target_group
    and has_bottom_send
    and (has_send_to or has_cancel)
)

raise SystemExit(0 if ok else 1)
PY
}

find_share_confirm_send_payload() {
  local file="$1"
  local group="$2"

  python3 - "$file" "$group" <<'PY'
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

target = sys.argv[2]

def norm(value):
    value = str(value or "")
    value = re.sub(
        r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u2000-\u200a]",
        "",
        value,
    )
    value = re.sub(r"\s+", " ", value).strip()
    return value

def strip_count(value):
    value = norm(value)
    value = re.sub(
        r"\s*[（(]\s*\d+\s*(?:人)?\s*[)）]\s*$",
        "",
        value,
    ).strip()
    return value

target = strip_count(target)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

visible = []
for index, element in enumerate(data.get("elements", [])):
    kind = str(element.get("kind", ""))
    label = norm(element.get("label", ""))
    value = norm(element.get("value", ""))
    rect = element.get("rect") or []

    if len(rect) != 4:
        continue

    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if (
        x < -50
        or y < 0
        or y > screen_h
        or w <= 0
        or h <= 0
    ):
        continue

    visible.append({
        "index": index,
        "kind": kind,
        "label": label,
        "value": value,
        "text": norm(f"{label} {value}"),
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    })

has_target_group = any(
    any(
        raw and strip_count(raw) == target
        for raw in (row["label"], row["value"])
    )
    for row in visible
)

has_modal_marker = any(
    "发送给" in row["text"]
    for row in visible
) or any(
    (row["label"] == "取消" or row["value"] == "取消")
    and row["y"] > screen_h * 0.68
    for row in visible
)

if not has_target_group or not has_modal_marker:
    raise SystemExit(1)

candidates = []

for row in visible:
    exact_send = row["label"] == "发送" or row["value"] == "发送"

    if not exact_send:
        continue

    cx = row["x"] + row["w"] / 2
    cy = row["y"] + row["h"] / 2

    # 截图中的确认按钮位于底部弹层右侧，
    # 大约 x=0.675、y=0.865。
    if cx < screen_w * 0.50:
        continue

    if cy < screen_h * 0.72 or cy > screen_h * 0.96:
        continue

    score = 0

    if row["kind"] == "Button":
        score += 500

    if row["label"] == "发送":
        score += 400

    if 60 <= row["w"] <= 180:
        score += 120

    if 30 <= row["h"] <= 100:
        score += 120

    score += int(cx)
    score += int(cy)

    candidates.append((score, row))

for score, row in sorted(
    candidates,
    key=lambda item: (-item[0], -item[1]["y"]),
):
    print(
        "[wechat-iphone] 分享确认发送按钮候选: "
        f"index={row['index']}, "
        f"kind={row['kind']}, "
        f"label={row['label']!r}, "
        f"value={row['value']!r}, "
        f"rect={[row['x'], row['y'], row['w'], row['h']]}",
        file=sys.stderr,
    )

if not candidates:
    raise SystemExit(1)

score, row = sorted(
    candidates,
    key=lambda item: (-item[0], -item[1]["y"]),
)[0]

tap_x = (row["x"] + row["w"] / 2) / screen_w
tap_y = (row["y"] + row["h"] / 2) / screen_h

print(
    "[wechat-iphone] 选中分享确认页右下角发送按钮: "
    f"rect={[row['x'], row['y'], row['w'], row['h']]}, "
    f"tap_x={tap_x:.6f}, tap_y={tap_y:.6f}",
    file=sys.stderr,
)

# 必须使用当前候选的中心坐标，不能用 label，
# 因为页面中可能还有其他包含“发送”的元素。
print(json.dumps({
    "type": "tap",
    "x": tap_x,
    "y": tap_y,
}, ensure_ascii=False))
PY
}

share_confirm_closed_file() {
  local file="$1"
  local group="$2"

  if is_share_confirm_file "$file" "$group"; then
    return 1
  fi

  # 确认弹层消失后，通常回到商品详情页，或出现“已发送”提示。
  if file_contains_label "$file" "分享好友" \
    || file_contains_label "$file" "立即报单" \
    || file_contains_label "$file" "已选：" \
    || file_contains_label "$file" "已发送"
  then
    return 0
  fi

  # 部分版本仍在小程序中，但详情页元素没有立刻刷新；
  # 只要右上角小程序胶囊存在，也说明已离开确认弹层。
  local close_payload=""
  if close_payload="$(
    find_top_right_mini_program_close_payload "$file" 2>/dev/null
  )"; then
    return 0
  fi

  return 1
}

confirm_share_to_group() {
  local group="$1"
  local file="$RUN_DIR/share-confirm.json"
  local after_file="$RUN_DIR/share-confirm-after-send.json"
  local payload=""
  local attempt=1
  local clicked=0
  local retried=0

  while [[ $attempt -le 12 ]]; do
    save_elements "$file"

    if is_share_confirm_file "$file" "$group"; then
      if payload="$(
        find_share_confirm_send_payload "$file" "$group"
      )"; then
        log "点击分享确认页右下角绿色“发送”按钮: ${payload}"
        phone_act "$payload" >/dev/null
        clicked=1
        break
      fi

      log \
        "确认弹层已出现，但元素树未暴露右下角发送按钮；"\
        "使用截图校准兜底坐标: x=${SHARE_CONFIRM_SEND_X} "\
        "y=${SHARE_CONFIRM_SEND_Y}"

      phone_act "$(
        json_tap_xy_payload \
          "$SHARE_CONFIRM_SEND_X" \
          "$SHARE_CONFIRM_SEND_Y"
      )" >/dev/null

      clicked=1
      retried=1
      break
    fi

    # 部分微信版本选择群聊后可能直接发送，不显示确认弹层。
    if file_contains_label "$file" "分享好友" \
      || file_contains_label "$file" "立即报单" \
      || file_contains_label "$file" "已发送"
    then
      log "未出现二次确认弹层，已回到商品详情，判断分享动作已完成"
      return 0
    fi

    sleep 1
    attempt=$((attempt + 1))
  done

  if [[ "$clicked" != "1" ]]; then
    die_json \
      "SHARE_CONFIRM_NOT_FOUND" \
      "未出现包含目标群名的分享确认弹层"
  fi

  attempt=1

  while [[ $attempt -le 8 ]]; do
    sleep 1
    save_elements "$after_file"

    if share_confirm_closed_file "$after_file" "$group"; then
      log "已验证分享确认弹层关闭，商品分享完成"
      return 0
    fi

    # 第一次按元素坐标点击后弹层仍存在，再使用截图校准坐标补点一次。
    if [[ "$attempt" -eq 3 && "$retried" != "1" ]]; then
      log \
        "分享确认弹层仍存在，补点右下角绿色发送按钮: "\
        "x=${SHARE_CONFIRM_SEND_X} y=${SHARE_CONFIRM_SEND_Y}"

      phone_act "$(
        json_tap_xy_payload \
          "$SHARE_CONFIRM_SEND_X" \
          "$SHARE_CONFIRM_SEND_Y"
      )" >/dev/null

      retried=1
    fi

    attempt=$((attempt + 1))
  done

  die_json \
    "SHARE_SEND_NOT_VERIFIED" \
    "已点击分享确认页发送按钮，但确认弹层仍未关闭"
}

close_mini_program_after_share() {
  local file="$RUN_DIR/after-share-close.json"
  local payload=""
  local attempt=1

  while [[ $attempt -le 8 ]]; do
    save_elements "$file"

    if payload="$(find_top_right_mini_program_close_payload "$file" 2>/dev/null)"; then
      log "分享完成，关闭小程序"
      phone_act "$payload" >/dev/null
      sleep 2
      return 0
    fi

    if is_chat_list_file "$file" || is_target_chat_file "$file" "$DEFAULT_TRANSFER_CHAT"; then
      return 0
    fi

    sleep 1
    attempt=$((attempt + 1))
  done

  log "未识别到小程序关闭按钮；下一件商品开始时将重新定位微信页面"
  return 0
}

append_result() {
  local index="$1"
  local link="$2"
  local ok="$3"
  local warning="$4"

  python3 - "$RESULTS_JSONL" "$index" "$link" "$ok" "$warning" <<'PY'
import json
import sys

path = sys.argv[1]
index = int(sys.argv[2])
link = sys.argv[3]
ok = sys.argv[4] == "1"
warning = sys.argv[5] or None

record = {
    "index": index,
    "product_link": link,
    "ok": ok,
    "warning": warning,
}

with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(record, ensure_ascii=False) + "\n")
PY
}

extract_links() {
  local promotion_file="$1"
  local output_file="$2"

  python3 - "$promotion_file" "$output_file" <<'PY'
import re
import sys
from pathlib import Path

source = Path(sys.argv[1])
output = Path(sys.argv[2])

text = source.read_text(encoding="utf-8")

links = re.findall(
    r"#小程序://[^\s]+",
    text,
)

deduped = []
seen = set()

for link in links:
    link = link.rstrip("。；;，,）)]}>")

    if link not in seen:
        seen.add(link)
        deduped.append(link)

output.write_text(
    "\n".join(deduped) + ("\n" if deduped else ""),
    encoding="utf-8",
)

print(len(deduped))
PY
}

process_one_link() {
  local index="$1"
  local total="$2"
  local link="$3"
  local transfer_chat="$4"
  local target_group="$5"

  log "处理第 ${index}/${total} 个商品链接: ${link}"

  open_chat_from_list "$transfer_chat"
  send_text_to_current_chat "$link"
  click_sent_link "$link"
  allow_open_mini_program
  wait_for_product_detail
  open_share_method_sheet
  click_wechat_friend_method
  select_share_target_group "$target_group"
  confirm_share_to_group "$target_group"
  close_mini_program_after_share

  append_result "$index" "$link" "1" ""

  log "第 ${index}/${total} 个商品已分享到群聊: ${target_group}"
}

write_summary() {
  local promotion_file="$1"
  local transfer_chat="$2"
  local target_group="$3"
  local target_count="$4"
  local success_count="$5"

  python3 - \
    "$promotion_file" \
    "$transfer_chat" \
    "$target_group" \
    "$target_count" \
    "$success_count" \
    "$RUN_DIR" \
    "$RESULTS_JSONL" <<'PY'
import json
import sys
from pathlib import Path

promotion_file = sys.argv[1]
transfer_chat = sys.argv[2]
target_group = sys.argv[3]
target_count = int(sys.argv[4])
success_count = int(sys.argv[5])
run_dir = sys.argv[6]
results_jsonl = sys.argv[7]

results = []

path = Path(results_jsonl)

if path.exists():
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            results.append(json.loads(line))

print(json.dumps({
    "ok": success_count == target_count,
    "action": "share-product-links",
    "promotion_file": promotion_file,
    "transfer_chat": transfer_chat,
    "target_group": target_group,
    "target_count": target_count,
    "success_count": success_count,
    "out_dir": run_dir,
    "results_jsonl": results_jsonl,
    "results": results,
}, ensure_ascii=False))
PY
}

usage() {
  cat <<'EOF'
用法：

  ./wechat-iphone-scenario4-v2-share-confirm-send.sh share-product-links [参数]

参数：

  --promotion-file <文件>     最终推广文案文件
                              默认：./scenario3-final-promotion.txt

  --transfer-chat <会话名>    默认：文件传输助手

  --target-group <群聊名>     默认：<TARGET_WECHAT_GROUP>

  --max-links <数量>          最多处理多少个商品链接
                              默认：全部；建议首次测试传 1

  --search-type-delay <秒>    搜索时逐字输入间隔
                              默认：0.25

  --share-confirm-send-x <比例>
                              分享确认页绿色发送按钮兜底横坐标
                              默认：0.675

  --share-confirm-send-y <比例>
                              分享确认页绿色发送按钮兜底纵坐标
                              默认：0.865

示例：

  先测试一个商品：

  ./wechat-iphone-scenario4-v2-share-confirm-send.sh share-product-links \
    --promotion-file "./scenario3-final-promotion.txt" \
    --target-group "<TARGET_WECHAT_GROUP>" \
    --max-links 1

  正式处理全部商品：

  ./wechat-iphone-scenario4-v2-share-confirm-send.sh share-product-links \
    --promotion-file "./scenario3-final-promotion.txt" \
    --target-group "<TARGET_WECHAT_GROUP>"
EOF
}

main() {
  local action="${1:-}"

  if [[ -z "$action" ]]; then
    usage
    exit 1
  fi

  shift || true

  local promotion_file="$DEFAULT_PROMOTION_FILE"
  local transfer_chat="$DEFAULT_TRANSFER_CHAT"
  local target_group="$DEFAULT_TARGET_GROUP"
  local max_links="0"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --promotion-file)
        promotion_file="${2:-}"
        shift 2
        ;;
      --transfer-chat)
        transfer_chat="${2:-}"
        shift 2
        ;;
      --target-group)
        target_group="${2:-}"
        shift 2
        ;;
      --max-links)
        max_links="${2:-0}"
        shift 2
        ;;
      --search-type-delay)
        SEARCH_TYPE_DELAY="${2:-0.25}"
        shift 2
        ;;
      --share-confirm-send-x)
        SHARE_CONFIRM_SEND_X="${2:-0.675}"
        shift 2
        ;;
      --share-confirm-send-y)
        SHARE_CONFIRM_SEND_Y="${2:-0.865}"
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        die_json "UNKNOWN_ARGUMENT" "未知参数: $1"
        ;;
    esac
  done

  if [[ "$action" != "share-product-links" ]]; then
    die_json "UNKNOWN_ACTION" "未知动作: $action"
  fi

  if [[ -z "$target_group" ]]; then
    die_json "TARGET_GROUP_EMPTY" "目标群聊名称不能为空；请传 --target-group 或设置 WECHAT_IPHONE_TARGET_GROUP"
  fi

  if [[ ! -f "$promotion_file" ]]; then
    die_json \
      "PROMOTION_FILE_NOT_FOUND" \
      "找不到最终推广文案文件: ${promotion_file}"
  fi

  if ! [[ "$max_links" =~ ^[0-9]+$ ]]; then
    die_json "INVALID_MAX_LINKS" "--max-links 必须是非负整数"
  fi

  init_runtime
  acquire_lock
  assert_ready

  RUN_DIR="$STATE_DIR/share-product-links-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$RUN_DIR"

  RESULTS_JSONL="$RUN_DIR/results.jsonl"
  LINKS_FILE="$RUN_DIR/product-links.txt"
  : > "$RESULTS_JSONL"

  local extracted_count=""
  extracted_count="$(extract_links "$promotion_file" "$LINKS_FILE")"

  if [[ "$extracted_count" -eq 0 ]]; then
    die_json \
      "NO_PRODUCT_LINKS" \
      "最终推广文案中没有提取到 #小程序:// 商品链接"
  fi

  if [[ "$max_links" -gt 0 ]]; then
    python3 - "$LINKS_FILE" "$max_links" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
limit = int(sys.argv[2])
links = [
    line.strip()
    for line in path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]
path.write_text(
    "\n".join(links[:limit]) + ("\n" if links[:limit] else ""),
    encoding="utf-8",
)
PY
  fi

  local target_count=""
  target_count="$(grep -cve '^[[:space:]]*$' "$LINKS_FILE")"

  log "从最终推广文案提取到 ${target_count} 个商品链接"
  log "输出目录: ${RUN_DIR}"

  local index=0
  local success_count=0
  local link=""

  while IFS= read -r link || [[ -n "$link" ]]; do
    [[ -n "$link" ]] || continue

    index=$((index + 1))

    if process_one_link \
      "$index" \
      "$target_count" \
      "$link" \
      "$transfer_chat" \
      "$target_group"
    then
      success_count=$((success_count + 1))
    else
      append_result \
        "$index" \
        "$link" \
        "0" \
        "处理过程中发生错误"
      break
    fi
  done < "$LINKS_FILE"

  write_summary \
    "$promotion_file" \
    "$transfer_chat" \
    "$target_group" \
    "$target_count" \
    "$success_count"
}

main "$@"
