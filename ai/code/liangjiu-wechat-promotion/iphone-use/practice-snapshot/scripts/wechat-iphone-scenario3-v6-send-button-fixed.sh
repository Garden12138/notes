#!/usr/bin/env bash
# wechat-iphone-scenario3-v6 — 动态识别输入框右侧“发送”按钮，禁止危险的底部固定坐标兜底
# macOS / Bash 3.2 compatible

set -uo pipefail
IFS=$'\n\t'

STATE_DIR="${WECHAT_IPHONE_STATE_DIR:-$HOME/.iphone-use/wechat-iphone}"
TOKEN_FILE="${WECHAT_IPHONE_TOKEN_FILE:-$HOME/.iphone-use/agent-token}"
HOST="${WECHAT_IPHONE_HOST:-http://127.0.0.1:44321}"
APP_BUNDLE="${WECHAT_IPHONE_APP_BUNDLE:-com.tencent.xin}"

SEARCH_X="${WECHAT_IPHONE_SEARCH_X:-0.50}"
SEARCH_Y="${WECHAT_IPHONE_SEARCH_Y:-0.12}"
FIRST_RESULT_X="${WECHAT_IPHONE_FIRST_RESULT_X:-0.50}"
FIRST_RESULT_Y="${WECHAT_IPHONE_FIRST_RESULT_Y:-0.20}"
SEARCH_TYPE_DELAY="${WECHAT_IPHONE_SEARCH_TYPE_DELAY:-0.25}"

MESSAGE_INPUT_X="${WECHAT_IPHONE_MESSAGE_INPUT_X:-0.50}"
MESSAGE_INPUT_Y="${WECHAT_IPHONE_MESSAGE_INPUT_Y:-0.94}"
SEND_X="${WECHAT_IPHONE_SEND_X:-0.91}"
SEND_Y="${WECHAT_IPHONE_SEND_Y:-0.94}"

DEFAULT_GROUP="${WECHAT_IPHONE_TARGET_GROUP:-}"

DEFAULT_MESSAGE="${WECHAT_IPHONE_DEFAULT_MESSAGE:-}"

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
  command -v "$1" >/dev/null 2>&1 || die_json "MISSING_COMMAND" "缺少命令: $1"
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
  local raw

  if ! raw="$(phone_status 2>/dev/null)"; then
    die_json "IPHONE_USE_UNREACHABLE" "无法访问 ${HOST}/agent/status"
  fi

  if ! printf '%s' "$raw" | status_ready_from_stdin; then
    printf '%s\n' "$raw" >&2
    die_json "IPHONE_NOT_READY" "需要 ok=true, wda=true, wda_actionable=true, wda_locked=false, drivable=true, mode=agent"
  fi
}

save_elements() {
  local file="$1"

  if ! phone_elements > "$file"; then
    die_json "ELEMENTS_FAILED" "读取元素树失败"
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

normalize_text_python='
import re

def norm(value):
    value = str(value or "")
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u2000-\u200a]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value
'

is_chat_list_file() {
  local file="$1"

  python3 - "$file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

visible_labels = []
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
        visible_labels.append((label, y))

has_top_search = any("搜索" in label and y < 220 for label, y in visible_labels)
bottom_tabs = ("微信", "通讯录", "发现", "我")
tab_hits = sum(
    1 for tab in bottom_tabs
    if any(label == tab and y > 650 for label, y in visible_labels)
)

raise SystemExit(0 if has_top_search and tab_hits >= 2 else 1)
PY
}

find_label_contains() {
  local file="$1"
  local needle="$2"

  python3 - "$file" "$needle" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

needle = sys.argv[2]
for element in data.get("elements", []):
    label = str(element.get("label", "")).strip()
    if needle in label:
        print(label)
        break
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

# 微信小程序右上角胶囊通常同时存在“更多”和“关闭”两个按钮。
has_more = any(
    kind == "Button"
    and "更多" in label
    and x > screen_w * 0.60
    and y < 150
    for kind, label, x, y, w, h in visible
)

close_candidates = []
for kind, label, x, y, w, h in visible:
    if (
        kind == "Button"
        and "关闭" in label
        and x > screen_w * 0.72
        and y < 150
    ):
        close_candidates.append((x, y, w, h, label))

if not has_more or not close_candidates:
    raise SystemExit(1)

x, y, w, h, label = sorted(close_candidates, key=lambda row: -row[0])[0]

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

return_to_wechat_chat_list() {
  local file="$STATE_DIR/scenario3-return-chat-list.json"
  local attempt=1
  local payload=""

  while [[ $attempt -le 14 ]]; do
    save_elements "$file"

    if is_chat_list_file "$file"; then
      log "已返回微信聊天列表"
      return 0
    fi

    payload=""

    # 场景二结束后通常停留在微信小程序商品列表。
    # 此时应点击右上角胶囊中的“关闭”，而不是反复点击左上角返回。
    if payload="$(find_top_right_mini_program_close_payload "$file" 2>/dev/null)"; then
      log "检测到微信小程序页面，点击右上角“关闭”退出小程序: ${payload}"
      phone_act "$payload" >/dev/null 2>&1 || true
      sleep 2
      attempt=$((attempt + 1))
      continue
    fi

    # 关闭小程序后，微信可能回到之前的聊天页或搜索页。
    # 再使用页面左上角真正的返回按钮逐级回到聊天列表。
    if payload="$(find_top_left_back_payload "$file" 2>/dev/null)"; then
      log "点击微信页面左上角返回按钮: ${payload}"
      phone_act "$payload" >/dev/null 2>&1 || true
    else
      log "当前页面未暴露返回元素，使用左上角安全坐标返回"
      phone_act "$(json_tap_xy_payload 0.055 0.085)" >/dev/null 2>&1 || true
    fi

    sleep 1.5
    attempt=$((attempt + 1))
  done

  save_elements "$file"

  if is_chat_list_file "$file"; then
    log "已返回微信聊天列表"
    return 0
  fi

  return 1
}


clear_search_if_possible() {
  local file="$STATE_DIR/scenario3-search-before-clear.json"

  save_elements "$file"
  local clear_label
  clear_label="$(find_label_contains "$file" "清除")"

  if [[ -n "$clear_label" ]]; then
    phone_act "$(json_tap_label_payload "$clear_label")" >/dev/null 2>&1 || true
    sleep 0.5
  fi
}


type_text_character_by_character() {
  local text="$1"
  local delay="${2:-0.25}"

  log "在微信搜索框逐字输入群名，字符间隔 ${delay} 秒"

  python3 - "$text" <<'PY' |
import json
import sys

for char in sys.argv[1]:
    print(json.dumps({
        "type": "text",
        "text": char,
    }, ensure_ascii=False))
PY
  while IFS= read -r payload; do
    [[ -n "$payload" ]] || continue
    phone_act "$payload" >/dev/null
    sleep "$delay"
  done
}

find_safe_group_result_payload() {
  local file="$1"
  local group="$2"

  python3 - "$file" "$group" <<'PY'
import json
import re
import sys

path = sys.argv[1]
target_raw = sys.argv[2]

with open(path, encoding="utf-8") as f:
    data = json.load(f)

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
for index, element in enumerate(data.get("elements", [])):
    label = norm(element.get("label", ""))
    value = norm(element.get("value", ""))
    kind = str(element.get("kind", ""))
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

    rows.append({
        "index": index,
        "kind": kind,
        "label": label,
        "value": value,
        "text": label or value,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    })

def first_y_containing(terms):
    matches = [
        row["y"]
        for row in rows
        if any(term in row["text"] for term in terms)
    ]
    return min(matches) if matches else None

# 截图中的正确结果位于“最常使用”区域；
# 下面依次是“聊天记录”和“搜索网络结果”，这两个区域都不能点击。
chat_records_y = first_y_containing(("聊天记录", "更多聊天记录"))
network_search_y = first_y_containing(
    ("搜索网络结果", "搜一搜", "网络搜索", "搜索网络")
)

upper_limit = screen_h * 0.70
if chat_records_y is not None:
    upper_limit = min(upper_limit, chat_records_y - 2)
if network_search_y is not None:
    upper_limit = min(upper_limit, network_search_y - 2)

group_markers = [
    row
    for row in rows
    if row["text"] == "群聊"
]

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

count_suffix_pattern = re.compile(
    rf"^{re.escape(target)}\s*[（(]\s*\d+\s*[)）]$"
)

candidates = []
for row in rows:
    label = row["label"]
    value = row["value"]
    combined = norm(f"{label} {value}")

    exact = label == target or value == target
    title_with_count = bool(
        count_suffix_pattern.fullmatch(label)
        or count_suffix_pattern.fullmatch(value)
    )
    button_group_result = (
        row["kind"] == "Button"
        and target
        and target in combined
        and "群聊" in combined
    )

    if not (exact or title_with_count or button_group_result):
        continue

    # 排除顶部搜索框本身。
    if row["y"] < 115:
        continue

    # 核心安全条件：候选必须位于“聊天记录”和“搜索网络结果”之前。
    if row["y"] >= upper_limit:
        continue

    if any(term in combined for term in negative_terms):
        continue

    nearby_group_marker = any(
        abs(marker["y"] - row["y"]) <= 95
        and marker["y"] >= row["y"] - 10
        for marker in group_markers
    )

    score = 0
    if exact:
        score += 500
    if title_with_count:
        score += 450
    if button_group_result:
        score += 350
    if nearby_group_marker:
        score += 250
    if row["kind"] == "Button":
        score += 50

    # 同分时始终选择页面上方的结果。
    score -= int(row["y"])

    candidates.append((score, row, nearby_group_marker))

print(
    "[wechat-iphone] 搜索结果安全边界: "
    f"chat_records_y={chat_records_y}, "
    f"network_search_y={network_search_y}, "
    f"upper_limit={upper_limit}",
    file=sys.stderr,
)

for _, row, nearby_group_marker in sorted(
    candidates,
    key=lambda item: item[1]["y"],
):
    print(
        "[wechat-iphone] 群聊候选: "
        f"label={row['label']!r}, "
        f"value={row['value']!r}, "
        f"kind={row['kind']}, "
        f"rect={[row['x'], row['y'], row['w'], row['h']]}, "
        f"nearby_group_marker={nearby_group_marker}",
        file=sys.stderr,
    )

if not candidates:
    raise SystemExit(1)

score, row, nearby_group_marker = sorted(
    candidates,
    key=lambda item: (-item[0], item[1]["y"], item[1]["x"]),
)[0]

# 点击目标名称所在行。对于 StaticText，使用屏幕中部横坐标，
# 避免文字区域过窄；纵坐标仍使用目标名称中心。
tap_x = 0.50
tap_y = (row["y"] + row["h"] / 2) / screen_h

print(
    "[wechat-iphone] 选中顶部群聊结果: "
    f"label={row['label']!r}, "
    f"kind={row['kind']}, "
    f"rect={[row['x'], row['y'], row['w'], row['h']]}, "
    f"tap_x={tap_x}, tap_y={tap_y}",
    file=sys.stderr,
)

print(json.dumps({
    "type": "tap",
    "x": tap_x,
    "y": tap_y,
}, ensure_ascii=False))
PY
}


is_target_chat_file() {
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

def strip_member_count(value):
    value = norm(value)

    # 微信群标题常见形式：
    # <TARGET_WECHAT_GROUP> (8)
    # <TARGET_WECHAT_GROUP>(8)
    # <TARGET_WECHAT_GROUP>（8）
    value = re.sub(
        r"\s*[（(]\s*\d+\s*[)）]\s*$",
        "",
        value,
    ).strip()

    # 少数版本可能将成员数以逗号附加到无障碍标签中。
    value = re.sub(
        r"\s*,\s*\d+\s*(?:人|位成员|个成员)?\s*$",
        "",
        value,
    ).strip()

    return value

target_norm = strip_member_count(target)

screen = data.get("screen") or {}
screen_h = float(screen.get("height") or 852)
screen_w = float(screen.get("width") or 393)

visible = []
for element in data.get("elements", []):
    label = norm(element.get("label", ""))
    value = norm(element.get("value", ""))
    kind = str(element.get("kind", ""))
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
        "x": x,
        "y": y,
        "w": w,
        "h": h,
    })

header_matches = []
for row in visible:
    if row["y"] >= 155:
        continue

    for raw in (row["label"], row["value"]):
        if not raw:
            continue

        stripped = strip_member_count(raw)

        if stripped == target_norm:
            header_matches.append(row)
            break

        # NavigationBar 的无障碍标签有时会附带“聊天信息”等描述。
        if (
            row["kind"] == "NavigationBar"
            and target_norm
            and target_norm in stripped
        ):
            header_matches.append(row)
            break

has_target_header = bool(header_matches)

# 搜索结果页顶部也有搜索框，必须明确排除。
has_top_search_field = any(
    row["kind"] == "SearchField"
    and row["y"] < 180
    for row in visible
)

has_search_result_markers = any(
    any(
        marker in f"{row['label']} {row['value']}"
        for marker in (
            "搜索网络结果",
            "聊天记录",
            "更多聊天记录",
            "最常使用",
        )
    )
    for row in visible
)

chat_bottom_terms = (
    "输入",
    "发送",
    "表情",
    "语音",
    "按住说话",
    "切换到按住说话",
    "更多功能",
    "添加",
)

has_chat_bottom_controls = False
for row in visible:
    if row["y"] < screen_h * 0.68:
        continue

    combined = f"{row['label']} {row['value']}"

    if row["kind"] in {"TextView", "TextField"}:
        has_chat_bottom_controls = True
        break

    if any(term in combined for term in chat_bottom_terms):
        has_chat_bottom_controls = True
        break

# 微信聊天页顶部通常有返回按钮，以及聊天信息/更多按钮。
has_top_back = any(
    row["kind"] == "Button"
    and "返回" in row["label"]
    and row["x"] < screen_w * 0.30
    and row["y"] < 160
    for row in visible
)

has_top_chat_action = any(
    row["kind"] == "Button"
    and row["x"] > screen_w * 0.65
    and row["y"] < 160
    and any(
        term in f"{row['label']} {row['value']}"
        for term in ("聊天信息", "更多", "群聊信息")
    )
    for row in visible
)

not_search_page = not (
    has_top_search_field
    or has_search_result_markers
)

# 强验证：
# 1. 顶部标题去掉“(成员数)”后与目标群名匹配；
# 2. 当前不是搜索结果页；
# 3. 能看到聊天底部控件，或能看到聊天页的返回/聊天信息导航控件。
chat_surface_confirmed = (
    has_chat_bottom_controls
    or (has_top_back and has_top_chat_action)
    or has_top_back
)

ok = (
    has_target_header
    and not_search_page
    and chat_surface_confirmed
)

if not ok:
    print(
        "[wechat-iphone] 群聊验证诊断: "
        f"target={target_norm!r}, "
        f"has_target_header={has_target_header}, "
        f"has_top_search_field={has_top_search_field}, "
        f"has_search_result_markers={has_search_result_markers}, "
        f"has_chat_bottom_controls={has_chat_bottom_controls}, "
        f"has_top_back={has_top_back}, "
        f"has_top_chat_action={has_top_chat_action}",
        file=sys.stderr,
    )

    top_labels = [
        {
            "kind": row["kind"],
            "label": row["label"],
            "value": row["value"],
            "rect": [
                row["x"],
                row["y"],
                row["w"],
                row["h"],
            ],
        }
        for row in visible
        if row["y"] < 170
        and (row["label"] or row["value"])
    ]

    print(
        "[wechat-iphone] 群聊页面顶部元素: "
        + json.dumps(top_labels, ensure_ascii=False),
        file=sys.stderr,
    )

raise SystemExit(0 if ok else 1)
PY
}

open_target_group() {
  local group="$1"
  local search_file="$STATE_DIR/scenario3-group-search-results.json"
  local verify_file="$STATE_DIR/scenario3-target-chat-verify.json"

  log "打开微信"
  phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null
  sleep 3

  log "返回微信聊天列表"
  if ! return_to_wechat_chat_list; then
    die_json "CHAT_LIST_NOT_FOUND" "无法返回微信聊天列表"
  fi

  log "搜索群聊: ${group}"
  phone_act "$(json_tap_xy_payload "$SEARCH_X" "$SEARCH_Y")" >/dev/null
  sleep 1

  clear_search_if_possible

  # 一次性粘贴完整群名时，微信可能优先展示文章或“搜一搜”结果。
  # 改为逐字输入，让微信实时生成“群聊”分类。
  type_text_character_by_character "$group" "$SEARCH_TYPE_DELAY"

  local payload=""
  local search_attempt=1

  while [[ $search_attempt -le 8 ]]; do
    sleep 1
    save_elements "$search_file"

    if payload="$(find_safe_group_result_payload "$search_file" "$group")"; then
      log "点击页面顶部安全区域中的群聊结果: ${group}"
      phone_act "$payload" >/dev/null
      break
    fi

    log "等待微信生成群聊搜索结果: ${search_attempt}/8"
    search_attempt=$((search_attempt + 1))
  done

  if [[ -z "$payload" ]]; then
    die_json \
      "GROUP_SEARCH_RESULT_NOT_FOUND" \
      "未在聊天记录和网络搜索区域之前找到目标群聊: ${group}；为避免误点，已停止操作"
  fi

  local attempt=1
  while [[ $attempt -le 8 ]]; do
    sleep 1
    save_elements "$verify_file"

    if is_target_chat_file "$verify_file" "$group"; then
      log "已严格验证进入目标群聊: ${group}"
      return 0
    fi

    attempt=$((attempt + 1))
  done

  die_json "TARGET_CHAT_NOT_VERIFIED" "未能验证进入指定群聊: ${group}"
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

    if x < -50 or y < screen_h * 0.72 or y > screen_h:
        continue

    text = f"{label} {value}"
    score = 0

    if kind in {"TextView", "TextField"}:
        score += 10
    if "输入" in text:
        score += 8
    if w > screen_w * 0.35:
        score += 4
    if 25 <= h <= 120:
        score += 2

    if score > 0:
        candidates.append((score, y, x, w, h, kind, label))

if not candidates:
    raise SystemExit(1)

score, y, x, w, h, kind, label = sorted(
    candidates,
    key=lambda row: (-row[0], -row[1], row[2])
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

for index, element in enumerate(data.get("elements", [])):
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

    if (
        x < -50
        or y < 0
        or y > screen_h
        or w <= 0
        or h <= 0
    ):
        continue

    combined = f"{label} {value}".strip()

    # 微信在键盘弹出时，“发送”按钮会移动到输入框右侧、屏幕中部附近，
    # 因此不能再要求 y > 65% 屏幕高度。
    exact_send = label == "发送" or value == "发送"
    contains_send = "发送" in combined

    if not exact_send and not contains_send:
        continue

    # 必须位于屏幕右侧，且不能落入状态栏或键盘最底部/系统手势区域。
    center_x = x + w / 2
    center_y = y + h / 2

    if center_x < screen_w * 0.68:
        continue

    if center_y < screen_h * 0.30:
        continue

    if center_y > screen_h * 0.82:
        continue

    score = 0

    if exact_send:
        score += 500

    if kind == "Button":
        score += 300
    elif kind == "StaticText":
        score += 80

    # 微信绿色发送按钮通常宽高约 40~100pt，排除异常大区域。
    if 25 <= w <= 130:
        score += 80
    if 25 <= h <= 90:
        score += 80

    score += int(center_x)

    candidates.append({
        "score": score,
        "index": index,
        "kind": kind,
        "label": label,
        "value": value,
        "x": x,
        "y": y,
        "w": w,
        "h": h,
        "center_x": center_x,
        "center_y": center_y,
    })

for row in sorted(
    candidates,
    key=lambda item: (-item["score"], item["y"]),
):
    print(
        "[wechat-iphone] 发送按钮候选: "
        f"index={row['index']}, "
        f"kind={row['kind']}, "
        f"label={row['label']!r}, "
        f"value={row['value']!r}, "
        f"rect={[row['x'], row['y'], row['w'], row['h']]}",
        file=sys.stderr,
    )

if not candidates:
    raise SystemExit(1)

selected = sorted(
    candidates,
    key=lambda item: (-item["score"], item["y"]),
)[0]

print(
    "[wechat-iphone] 选中发送按钮: "
    f"index={selected['index']}, "
    f"kind={selected['kind']}, "
    f"label={selected['label']!r}, "
    f"rect={[selected['x'], selected['y'], selected['w'], selected['h']]}, "
    f"normalized_center="
    f"({selected['center_x'] / screen_w:.6f}, "
    f"{selected['center_y'] / screen_h:.6f})",
    file=sys.stderr,
)

# “发送”在当前微信聊天界面应当是唯一按钮。
# 优先按无障碍标签点击，避免受键盘高度变化影响。
if selected["kind"] == "Button" and selected["label"] == "发送":
    print(json.dumps({
        "type": "tap",
        "label": "发送",
    }, ensure_ascii=False))
else:
    print(json.dumps({
        "type": "tap",
        "x": selected["center_x"] / screen_w,
        "y": selected["center_y"] / screen_h,
    }, ensure_ascii=False))
PY
}

message_visible_file() {
  local file="$1"
  local message="$2"

  python3 - "$file" "$message" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

message = sys.argv[2]
lines = [line.strip() for line in message.splitlines() if line.strip()]
markers = [line.replace("⏰", "") for line in lines[:3]]

text_blob = "\n".join(
    [
        str(element.get("label", ""))
        + "\n"
        + str(element.get("value", ""))
        for element in data.get("elements", [])
    ]
)

hits = sum(1 for marker in markers if marker and marker in text_blob)
required_hits = min(2, len(markers))
raise SystemExit(0 if required_hits > 0 and hits >= required_hits else 1)
PY
}

send_promotion() {
  local group="$1"
  local message="$2"
  local dry_run="$3"

  local before_input="$STATE_DIR/scenario3-before-input.json"
  local before_send="$STATE_DIR/scenario3-before-send.json"
  local after_send="$STATE_DIR/scenario3-after-send.json"

  open_target_group "$group"

  save_elements "$before_input"

  local input_payload=""
  if input_payload="$(find_message_input_payload "$before_input" 2>/dev/null)"; then
    log "点击群聊消息输入框: ${input_payload}"
    phone_act "$input_payload" >/dev/null
  else
    log "元素树未暴露消息输入框，使用兜底坐标: x=${MESSAGE_INPUT_X} y=${MESSAGE_INPUT_Y}"
    phone_act "$(json_tap_xy_payload "$MESSAGE_INPUT_X" "$MESSAGE_INPUT_Y")" >/dev/null
  fi

  sleep 0.8

  log "输入最终推广文案"
  phone_act "$(json_text_payload "$message")" >/dev/null
  sleep 1.5

  save_elements "$before_send"

  if ! is_target_chat_file "$before_send" "$group"; then
    die_json "WRONG_CHAT_BEFORE_SEND" "发送前群聊名称校验失败，已阻止发送"
  fi

  log "发送前再次确认群聊名称完全匹配: ${group}"

  if [[ "$dry_run" == "1" ]]; then
    python3 - "$group" "$message" <<'PY'
import json
import sys

print(json.dumps({
    "ok": True,
    "action": "send-promotion",
    "dry_run": True,
    "group": sys.argv[1],
    "message": sys.argv[2],
    "sent": False,
}, ensure_ascii=False))
PY
    return 0
  fi

  local send_payload=""

  if send_payload="$(find_send_payload "$before_send")"; then
    log "点击输入框右侧发送按钮: ${send_payload}"
    phone_act "$send_payload" >/dev/null
  else
    # 禁止再使用 y=0.94 一类固定坐标：
    # 键盘弹出时该位置属于键盘或系统手势区域，可能误触换行、
    # Home 指示器或 App 切换器。
    die_json \
      "SEND_BUTTON_NOT_FOUND" \
      "未在输入框右侧识别到“发送”按钮，已停止操作，未执行固定坐标点击"
  fi

  local attempt=1
  local verified=0

  while [[ $attempt -le 10 ]]; do
    sleep 1
    save_elements "$after_send"

    if ! is_target_chat_file "$after_send" "$group"; then
      die_json "CHAT_CHANGED_AFTER_SEND" "发送后离开了目标群聊，无法确认结果"
    fi

    if message_visible_file "$after_send" "$message"; then
      verified=1
      break
    fi

    attempt=$((attempt + 1))
  done

  local output_dir
  output_dir="$STATE_DIR/send-promotion-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$output_dir"

  printf '%s\n' "$message" > "$output_dir/final-promotion.txt"
  cp "$before_send" "$output_dir/before-send.json" 2>/dev/null || true
  cp "$after_send" "$output_dir/after-send.json" 2>/dev/null || true

  python3 - "$group" "$message" "$verified" "$output_dir" <<'PY'
import json
import sys

verified = sys.argv[3] == "1"

print(json.dumps({
    "ok": verified,
    "action": "send-promotion",
    "group": sys.argv[1],
    "message": sys.argv[2],
    "sent": True,
    "send_verified": verified,
    "out_dir": sys.argv[4],
    "warning": None if verified else "发送动作已执行，但元素树未能确认完整文案出现在聊天区域。",
}, ensure_ascii=False))
PY

  if [[ "$verified" != "1" ]]; then
    exit 2
  fi
}

usage() {
  cat <<'EOF'
用法：

  ./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion [参数]

参数：

  --group <群聊名称>          默认：<TARGET_WECHAT_GROUP>
  --message <推广文案>        直接传入文案
  --message-file <文件>       从 UTF-8 文本文件读取文案
  --dry-run                   只输入并校验群聊，不点击发送
  --search-x <比例>
  --search-y <比例>
  --first-result-x <比例>
  --first-result-y <比例>
  --search-type-delay <秒>  逐字输入群名的字符间隔，默认 0.25
  --input-x <比例>
  --input-y <比例>
  --send-x <比例>            保留兼容参数，v6 默认不再使用固定坐标发送
  --send-y <比例>            保留兼容参数，v6 默认不再使用固定坐标发送

示例：

  ./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion \
    --group "<TARGET_WECHAT_GROUP>" \
    --message-file "./scenario3-final-promotion.txt"

测试但不发送：

  ./wechat-iphone-scenario3-v6-send-button-fixed.sh send-promotion \
    --group "<TARGET_WECHAT_GROUP>" \
    --message-file "./scenario3-final-promotion.txt" \
    --dry-run
EOF
}

main() {
  local action="${1:-}"
  if [[ -z "$action" ]]; then
    usage
    exit 1
  fi
  shift || true

  local group="$DEFAULT_GROUP"
  local message="$DEFAULT_MESSAGE"
  local message_file=""
  local dry_run="0"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --group)
        group="${2:-}"
        shift 2
        ;;
      --message)
        message="${2:-}"
        shift 2
        ;;
      --message-file)
        message_file="${2:-}"
        shift 2
        ;;
      --dry-run)
        dry_run="1"
        shift
        ;;
      --search-x)
        SEARCH_X="${2:-}"
        shift 2
        ;;
      --search-y)
        SEARCH_Y="${2:-}"
        shift 2
        ;;
      --first-result-x)
        FIRST_RESULT_X="${2:-}"
        shift 2
        ;;
      --first-result-y)
        FIRST_RESULT_Y="${2:-}"
        shift 2
        ;;
      --search-type-delay)
        SEARCH_TYPE_DELAY="${2:-}"
        shift 2
        ;;
      --input-x)
        MESSAGE_INPUT_X="${2:-}"
        shift 2
        ;;
      --input-y)
        MESSAGE_INPUT_Y="${2:-}"
        shift 2
        ;;
      --send-x)
        SEND_X="${2:-}"
        shift 2
        ;;
      --send-y)
        SEND_Y="${2:-}"
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

  if [[ -n "$message_file" ]]; then
    if [[ ! -f "$message_file" ]]; then
      die_json "MESSAGE_FILE_NOT_FOUND" "找不到文案文件: $message_file"
    fi
    message="$(cat "$message_file")"
  fi

  if [[ -z "$group" ]]; then
    die_json "GROUP_EMPTY" "群聊名称不能为空"
  fi

  if [[ -z "$message" ]]; then
    die_json "MESSAGE_EMPTY" "推广文案不能为空"
  fi

  init_runtime
  acquire_lock
  assert_ready

  case "$action" in
    send-promotion)
      send_promotion "$group" "$message" "$dry_run"
      ;;
    *)
      die_json "UNKNOWN_ACTION" "未知动作: $action"
      ;;
  esac
}

main "$@"
