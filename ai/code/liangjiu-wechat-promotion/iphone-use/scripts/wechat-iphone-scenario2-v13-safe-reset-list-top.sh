#!/usr/bin/env bash
# wechat-iphone-scenario2-v13 - 使用列表内容区内的小幅滚动安全回到第一页,再逐个处理商品
# macOS / Bash 3.2 compatible

set -uo pipefail
IFS=$'\n\t'

STATE_DIR="${WECHAT_IPHONE_STATE_DIR:-$HOME/.iphone-use/wechat-iphone}"
TOKEN_FILE="${WECHAT_IPHONE_TOKEN_FILE:-$HOME/.iphone-use/agent-token}"
HOST="${WECHAT_IPHONE_HOST:-http://127.0.0.1:44321}"
APP_BUNDLE="${WECHAT_IPHONE_APP_BUNDLE:-com.tencent.xin}"

# 微信搜索 / 小程序入口坐标。沿用你前面已验证可用的布局。
SEARCH_X="${WECHAT_IPHONE_SEARCH_X:-0.50}"
SEARCH_Y="${WECHAT_IPHONE_SEARCH_Y:-0.12}"
FIRST_RESULT_X="${WECHAT_IPHONE_FIRST_RESULT_X:-0.50}"
FIRST_RESULT_Y="${WECHAT_IPHONE_FIRST_RESULT_Y:-0.20}"
MINI_PROGRAM_RESULT_X="${WECHAT_IPHONE_MINI_PROGRAM_RESULT_X:-$FIRST_RESULT_X}"
MINI_PROGRAM_RESULT_Y="${WECHAT_IPHONE_MINI_PROGRAM_RESULT_Y:-$FIRST_RESULT_Y}"
NEW_PRODUCTS_X="${WECHAT_IPHONE_NEW_PRODUCTS_X:-0.105}"
NEW_PRODUCTS_Y="${WECHAT_IPHONE_NEW_PRODUCTS_Y:-0.805}"

# 商品列表滚动。正数 dy 是"向上滑动页面,浏览更下面内容",避免触发下拉刷新。
# 当前两列商品卡片一屏约展示 2 行/4 件。默认每次前进约两行,减少上下屏重叠。
PRODUCT_SCROLL_X="${WECHAT_IPHONE_PRODUCT_SCROLL_X:-0.50}"
PRODUCT_SCROLL_Y="${WECHAT_IPHONE_PRODUCT_SCROLL_Y:-0.72}"
PRODUCT_SCROLL_DY="${WECHAT_IPHONE_PRODUCT_SCROLL_DY:-640}"
PRODUCT_TAP_MIN_Y="${WECHAT_IPHONE_PRODUCT_TAP_MIN_Y:-260}"
PRODUCT_TAP_MAX_Y="${WECHAT_IPHONE_PRODUCT_TAP_MAX_Y:-780}"
PRODUCT_ALIGN_SCROLL_DY="${WECHAT_IPHONE_PRODUCT_ALIGN_SCROLL_DY:-220}"

# 场景二开始时先把"新品首发"列表恢复到第一页。
# 必须从商品列表内容区内部做小幅滚动,不能让手势轨迹碰到屏幕顶部状态栏。
# 旧版 y=0.38、dy=-650 的终点会越过顶部安全区,可能拉出通知中心/锁屏界面。
# 当前默认从屏幕下半部开始,每次只向上浏览 240px,整个手势始终留在小程序内容区。
LIST_TOP_SCROLL_X="${WECHAT_IPHONE_LIST_TOP_SCROLL_X:-$PRODUCT_SCROLL_X}"
LIST_TOP_SCROLL_Y="${WECHAT_IPHONE_LIST_TOP_SCROLL_Y:-0.72}"
LIST_TOP_SCROLL_DY="${WECHAT_IPHONE_LIST_TOP_SCROLL_DY:--240}"
LIST_TOP_MAX_SCROLLS="${WECHAT_IPHONE_LIST_TOP_MAX_SCROLLS:-30}"

# 屏幕逻辑尺寸,用于把元素树 rect 转为 iphone-use 的比例坐标。
# 你当前元素树看起来是 393x852 点。
SCREEN_WIDTH="${WECHAT_IPHONE_SCREEN_WIDTH:-393}"
SCREEN_HEIGHT="${WECHAT_IPHONE_SCREEN_HEIGHT:-852}"

# 详情页右上角更多按钮,以及分享面板"复制链接"兜底坐标。
MORE_X="${WECHAT_IPHONE_MORE_X:-0.78}"
MORE_Y="${WECHAT_IPHONE_MORE_Y:-0.095}"
DETAIL_BACK_X="${WECHAT_IPHONE_DETAIL_BACK_X:-0.055}"
DETAIL_BACK_Y="${WECHAT_IPHONE_DETAIL_BACK_Y:-0.095}"
COPY_LINK_X="${WECHAT_IPHONE_COPY_LINK_X:-0.82}"
COPY_LINK_Y="${WECHAT_IPHONE_COPY_LINK_Y:-0.88}"

# 商品链接读取模式:shortcut(推荐)、host(旧版通用剪贴板)、auto(先 Shortcut,失败后尝试 host)。
LINK_READ_MODE="${WECHAT_IPHONE_LINK_READ_MODE:-shortcut}"
CLIPBOARD_SHORTCUT_NAME="${WECHAT_IPHONE_CLIPBOARD_SHORTCUT_NAME:-IU Clipboard Export}"
CLIPBOARD_SHORTCUT_TIMEOUT="${WECHAT_IPHONE_CLIPBOARD_SHORTCUT_TIMEOUT:-25}"
SHORTCUTS_APP_BUNDLE="${WECHAT_IPHONE_SHORTCUTS_APP_BUNDLE:-com.apple.shortcuts}"
SHORTCUTS_APP_WAIT="${WECHAT_IPHONE_SHORTCUTS_APP_WAIT:-3}"
SHORTCUT_RUN_X="${WECHAT_IPHONE_SHORTCUT_RUN_X:-0.86}"
SHORTCUT_RUN_Y="${WECHAT_IPHONE_SHORTCUT_RUN_Y:-0.94}"

DETAIL_SCROLL_X="${WECHAT_IPHONE_DETAIL_SCROLL_X:-0.50}"
DETAIL_SCROLL_Y="${WECHAT_IPHONE_DETAIL_SCROLL_Y:-0.72}"
DETAIL_SCROLL_DY="${WECHAT_IPHONE_DETAIL_SCROLL_DY:-280}"

DEFAULT_PRODUCTS=""

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
  command -v "$1" >/dev/null 2>&1 || die_json "MISSING_COMMAND" "缺少命令: $1"
}

init_runtime() {
  require_cmd curl
  require_cmd python3
  require_cmd pbpaste
  require_cmd pbcopy

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

json_tap_xy_payload() {
  python3 - "$1" "$2" <<'PY'
import json, sys
print(json.dumps({"type": "tap", "x": float(sys.argv[1]), "y": float(sys.argv[2])}, ensure_ascii=False))
PY
}

json_scroll_payload() {
  python3 - "$1" "$2" "$3" <<'PY'
import json, sys
print(json.dumps({"type": "scroll", "x": float(sys.argv[1]), "y": float(sys.argv[2]), "dx": 0, "dy": int(float(sys.argv[3]))}, ensure_ascii=False))
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
    die_json "IPHONE_NOT_READY" "需要 ok=true, wda=true, wda_actionable=true, wda_locked=false, drivable=true, mode=agent"
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
    die_json "ELEMENTS_INVALID_JSON" "元素树不是有效 JSON: $file"
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

find_new_products_tab_payload() {
  local file="$1"
  python3 - "$file" "$SCREEN_WIDTH" "$SCREEN_HEIGHT" "$NEW_PRODUCTS_X" "$NEW_PRODUCTS_Y" <<'PY_NEW_PRODUCTS_TAB'
import json, sys

path = sys.argv[1]
fallback_x = float(sys.argv[4])
fallback_y = float(sys.argv[5])

with open(path, encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or sys.argv[2])
screen_h = float(screen.get("height") or sys.argv[3])

choices = []
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    kind = str(e.get("kind", ""))
    rect = e.get("rect") or []
    if label != "新品首发" or len(rect) != 4 or kind not in {"StaticText", "Button", "Other"}:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    cx = x + w / 2
    cy = y + h / 2
    # 只接受顶部 tab 栏里的"新品首发"。商品卡片里的角标或离屏内容不能当入口。
    if 0 <= cx <= screen_w * 0.45 and screen_h * 0.12 <= cy <= screen_h * 0.36:
        choices.append((abs(cx - screen_w * 0.25) + abs(cy - screen_h * 0.25), cx, cy))

if choices:
    _, cx, cy = sorted(choices)[0]
    print(json.dumps({"type": "tap", "x": cx / screen_w, "y": cy / screen_h}, ensure_ascii=False))
else:
    print(json.dumps({"type": "tap", "x": fallback_x, "y": fallback_y}, ensure_ascii=False))
PY_NEW_PRODUCTS_TAB
}

select_new_products_tab_from_file() {
  local file="$1"
  local verify="$STATE_DIR/scenario2-new-products-tab-verify.json"
  local payload

  payload="$(find_new_products_tab_payload "$file")"
  log "确认点选新品首发标签: ${payload}"
  phone_act "$payload" >/dev/null || true
  sleep 1.5

  save_elements "$verify"
  if is_new_products_file "$verify"; then
    return 0
  fi

  return 1
}


is_shortcut_editor_file() {
  local file="$1"
  local shortcut_name="$2"
  python3 - "$file" "$shortcut_name" <<'PY_SHORTCUT_EDITOR'
import json, re, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
shortcut_name = sys.argv[2]

def norm(value):
    value = str(value or "")
    # 快捷指令标题有时带零宽字符、窄空格等装饰字符。
    value = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff\u2000-\u200a]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value

labels = [norm(e.get("label", "")) for e in data.get("elements", [])]
name = norm(shortcut_name)
has_title = any(name and name in label for label in labels)
has_editor_ui = any(
    keyword in label
    for label in labels
    for keyword in ("搜索操作", "添加操作", "撤销", "重做", "显示操作")
)
raise SystemExit(0 if has_title and has_editor_ui else 1)
PY_SHORTCUT_EDITOR
}


is_any_shortcut_editor_file() {
  local file="$1"
  python3 - "$file" <<'PY_ANY_SHORTCUT_EDITOR'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
labels = [str(e.get("label", "")).strip() for e in data.get("elements", [])]
hits = sum(1 for key in ("搜索操作", "添加操作", "撤销", "重做") if any(key in label for label in labels))
raise SystemExit(0 if hits >= 1 else 1)
PY_ANY_SHORTCUT_EDITOR
}

is_shortcut_title_menu_file() {
  local file="$1"
  python3 - "$file" <<'PY_SHORTCUT_TITLE_MENU'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
labels = [str(e.get("label", "")).strip() for e in data.get("elements", [])]
strong = ("重命名", "选取图标", "添加到主屏幕", "导出文件")
raise SystemExit(0 if any(any(key in label for key in strong) for label in labels) else 1)
PY_SHORTCUT_TITLE_MENU
}

dismiss_shortcut_title_menu() {
  local file="$1"
  local after_file="$STATE_DIR/clipboard-shortcut-title-menu-dismissed.json"

  if ! is_shortcut_title_menu_file "$file"; then
    return 0
  fi

  log "检测到快捷指令顶部名称下拉菜单,先点击标题将菜单收起"
  phone_act '{"type":"tap","x":0.52,"y":0.095}' >/dev/null 2>&1 || true
  sleep 1
  save_elements "$after_file" >/dev/null 2>&1 || return 1

  if is_shortcut_title_menu_file "$after_file"; then
    log "标题菜单仍未关闭,发送 Escape 再尝试关闭"
    phone_act '{"type":"key","name":"escape"}' >/dev/null 2>&1 || true
    sleep 1
    save_elements "$after_file" >/dev/null 2>&1 || return 1
  fi

  if is_shortcut_title_menu_file "$after_file"; then
    log "快捷指令标题菜单仍然存在"
    return 1
  fi

  return 0
}

find_shortcut_run_payload() {
  local file="$1"
  python3 - "$file" "$SCREEN_WIDTH" "$SCREEN_HEIGHT" "$SHORTCUT_RUN_X" "$SHORTCUT_RUN_Y" <<'PY_SHORTCUT_RUN'
import json, sys
path = sys.argv[1]
sw = float(sys.argv[2])
sh = float(sys.argv[3])
fallback_x = float(sys.argv[4])
fallback_y = float(sys.argv[5])
with open(path, encoding="utf-8") as f:
    data = json.load(f)

# 当前 iPhone 快捷指令编辑器元素树明确暴露:
# Button label="播放", rect=[304,772,51,50]。
# 优先让 WDA 按可访问性标签点击,不再把 rect 换算成坐标后点击。
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    kind = str(e.get("kind", ""))
    rect = e.get("rect") or []
    if kind != "Button" or label != "播放" or len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    cx = x + w / 2
    cy = y + h / 2
    if cx < sw * 0.62 or cy < sh * 0.84:
        continue
    print(json.dumps({"type": "tap", "label": "播放"}, ensure_ascii=False))
    raise SystemExit(0)

# 兼容其他 iOS 语言或版本:寻找底部右侧明确的运行类按钮。
for wanted in ("运行快捷指令", "运行", "执行"):
    for e in data.get("elements", []):
        label = str(e.get("label", "")).strip()
        kind = str(e.get("kind", ""))
        rect = e.get("rect") or []
        if kind != "Button" or label != wanted or len(rect) != 4:
            continue
        try:
            x, y, w, h = map(float, rect)
        except Exception:
            continue
        cx = x + w / 2
        cy = y + h / 2
        if cx >= sw * 0.62 and cy >= sh * 0.84:
            print(json.dumps({"type": "tap", "label": wanted}, ensure_ascii=False))
            raise SystemExit(0)

# 最后才使用坐标兜底。当前元素树中心约为 x=0.8384, y=0.9354。
print(json.dumps({"type": "tap", "x": fallback_x, "y": fallback_y}, ensure_ascii=False))
PY_SHORTCUT_RUN
}


run_shortcut_if_editor_opened() {
  local shortcut_name="$1"
  local after_file="$STATE_DIR/clipboard-shortcut-after-card.json"
  local ready_file="$STATE_DIR/clipboard-shortcut-editor-ready.json"
  local after_run_file="$STATE_DIR/clipboard-shortcut-after-run.json"
  local payload=""

  sleep 2
  save_elements "$after_file" >/dev/null 2>&1 || return 1

  if is_shortcut_editor_file "$after_file" "$shortcut_name"; then
    # 上一次失败可能让 App 留在编辑器,并且顶部标题菜单仍是打开状态。
    # 先关闭菜单,否则第一次点击右下角只会用于收起菜单,看起来像没有运行。
    dismiss_shortcut_title_menu "$after_file" || return 1
    save_elements "$ready_file" >/dev/null 2>&1 || return 1

    payload="$(find_shortcut_run_payload "$ready_file")"
    log "运行快捷指令编辑器中的播放按钮: ${payload}"
    phone_act "$payload" >/dev/null 2>&1 || return 1
    sleep 1
    save_elements "$after_run_file" >/dev/null 2>&1 || true

    # 极端情况下菜单状态没有被元素树及时识别,第一次点击只关闭了菜单。
    # 若点击后反而还能检测到名称菜单,关闭菜单后再补点一次运行键。
    if [[ -f "$after_run_file" ]] && is_shortcut_title_menu_file "$after_run_file"; then
      log "首次点击后仍检测到顶部名称菜单,关闭菜单并补点一次运行按钮"
      dismiss_shortcut_title_menu "$after_run_file" || return 1
      save_elements "$ready_file" >/dev/null 2>&1 || return 1
      payload="$(find_shortcut_run_payload "$ready_file")"
      phone_act "$payload" >/dev/null 2>&1 || return 1
      sleep 1
    fi
    return 0
  fi

  # iOS 点按快捷指令卡片时可能直接运行而不进入编辑器。
  # 不把缺失编辑器视为失败 —— 让调用方继续轮询 inbox。
  log "点击快捷指令卡片后未检测到编辑器(可能已直接运行),继续轮询 inbox"
  return 0
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

is_liangjiu_home_file() {
  local file="$1"
  python3 - "$file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
labels = [str(e.get("label", "")).strip() for e in data.get("elements", [])]
keywords = [
    "良久团购", "良久素材", "新品首发", "爆款加开", "日销尖货",
    "新人展业", "公益助农", "官方授权", "品质保证", "极速发货", "售后无忧",
]
ok = any(keyword in label for keyword in keywords for label in labels)
raise SystemExit(0 if ok else 1)
PY
}

is_product_detail_file() {
  local file="$1"
  python3 - "$file" <<'PY_PRODUCT_DETAIL_CHECK'
import json, sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_h = float(screen.get("height") or 852)

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
    if x < -100 or y < 0 or y > screen_h:
        continue
    visible.append((label, x, y, w, h))

texts = [label for label, *_ in visible]

# 商品详情页底部固定操作区和当前选中规格,是最可靠的页面特征。
strong_markers = [
    "分享好友",
    "立即报单",
    "已选:",
    "已选:",
]

if any(any(marker in text for marker in strong_markers) for text in texts):
    raise SystemExit(0)

# 视频商品顶部通常还会暴露这些播放器控件;至少命中两个才视为详情页。
video_markers = {"视频", "暂停", "播放", "进度条", "全屏"}
video_hits = sum(1 for text in texts if text in video_markers)
if video_hits >= 2:
    raise SystemExit(0)

raise SystemExit(1)
PY_PRODUCT_DETAIL_CHECK
}

is_share_menu_file() {
  local file="$1"
  python3 - "$file" <<'PY_SHARE_MENU_CHECK'
import json, sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_h = float(screen.get("height") or 852)
texts = []
for element in data.get("elements", []):
    label = str(element.get("label", "")).strip()
    rect = element.get("rect") or []
    if not label or len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    if x < -100 or y < 0 or y > screen_h:
        continue
    texts.append(label)

markers = ["复制链接", "转发给", "转发给朋友", "添加到桌面", "取消"]
hits = sum(1 for marker in markers if any(marker in text for text in texts))
raise SystemExit(0 if hits >= 2 else 1)
PY_SHARE_MENU_CHECK
}

is_new_products_file() {
  local file="$1"
  python3 - "$file" <<'PY_NEW_PRODUCTS_CHECK'
import json, re, sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

visible = []
for element in data.get("elements", []):
    label = str(element.get("label", "")).strip()
    kind = str(element.get("kind", ""))
    rect = element.get("rect") or []
    if not label or len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    # 只判断当前屏幕可见区域。详情页元素树会包含 y=数千的长页面内容,
    # 这些离屏商品推荐不能用于判断已经返回商品列表。
    if x < -100 or y < 0 or y > screen_h:
        continue
    visible.append((label, kind, x, y, w, h))

texts = [label for label, *_ in visible]

# 分享菜单不是商品列表。
share_markers = ["复制链接", "转发给", "转发给朋友", "添加到桌面", "取消"]
if sum(1 for marker in share_markers if any(marker in text for text in texts)) >= 2:
    raise SystemExit(1)

# 商品详情页不是商品列表。尤其不能因为详情页离屏区域含有推荐商品而误判。
detail_markers = ["分享好友", "立即报单", "已选:", "已选:"]
if any(any(marker in text for marker in detail_markers) for text in texts):
    raise SystemExit(1)

video_markers = {"视频", "暂停", "播放", "进度条", "全屏"}
if sum(1 for text in texts if text in video_markers) >= 2:
    raise SystemExit(1)

# 良久首页会同时出现多个入口。
home_nav = ["爆款加开", "日销尖货", "新人展业", "公益助农"]
if sum(1 for key in home_nav if any(key in text for text in texts)) >= 2:
    raise SystemExit(1)

blocked = {
    "微信", "更多", "关闭", "返回", "取消", "确定", "首页", "分类", "购物车", "我的",
    "新品首发", "限时团购", "分享", "加载中", "暂无更多", "没有更多",
}

spec_re = re.compile(
    r"^(规格|已选|共\\d+款|[¥¥]|\\d+(?:\\.\\d+)?|"
    r"\\d+\\s*(袋|盒|个|斤|瓶|支|条|箱|组|套)|"
    r"[XSML]{1,4}|\\d{2,3}\\s*[xX*]\\s*\\d{2,3})"
)

product_terms = [
    "防晒", "裤", "裙", "外套", "连衣裙", "鞋", "鞋架", "茶壶", "抹布",
    "保温壶", "虾仁", "拌饭酱", "火龙果", "天麻", "馅饼", "鸡排", "鱼排",
    "牛排", "肉串", "护颈枕", "夏凉被", "四件套", "凉席", "被套", "蚊帐",
    "乳", "霜", "套装", "果", "食品", "枕", "被", "席", "锅", "壶", "杯",
]

candidates = []
for label, kind, x, y, w, h in visible:
    if kind not in {"StaticText", "Button", "Other"}:
        continue
    if y < 120 or y > screen_h - 25:
        continue
    if label in blocked or len(label) < 4:
        continue
    if spec_re.search(label):
        continue
    if not re.search(r"[\\u4e00-\\u9fffA-Za-z]", label):
        continue

    # 新品首发列表为两列商品卡片,标题通常位于左右列且宽度较窄。
    in_left = 0 <= x <= screen_w * 0.48
    in_right = screen_w * 0.45 <= x <= screen_w
    card_shape = 55 <= w <= screen_w * 0.50 and 20 <= h <= 100
    product_like = any(term in label for term in product_terms) or len(label) >= 8
    if (in_left or in_right) and card_shape and product_like:
        candidates.append((label, x, y, w, h))

has_date_header = any(
    re.match(r"^\\d{4}[-/]\\d{1,2}[-/]\\d{1,2}", label)
    for label in texts
)
has_list_header = any("新品首发" in label and y < 250 for label, _, _, y, _, _ in visible)

# 当前可见区域至少有一个商品卡片,且没有详情/分享/首页特征,即视为商品列表。
ok = len(candidates) >= 1 or (has_date_header and has_list_header)
raise SystemExit(0 if ok else 1)
PY_NEW_PRODUCTS_CHECK
}

is_new_products_top_file() {
  local file="$1"
  python3 - "$file" <<'PY_NEW_PRODUCTS_TOP'
import json, re, sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

# 优先使用 iOS Accessibility 暴露的纵向滚动条百分比。
# 只接受右侧、接近整页高度的主滚动条,避免把卡片内部滚动条当成列表位置。
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    value = str(e.get("value", "")).strip()
    rect = e.get("rect") or []
    if "垂直滚动条" not in label or len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    if x < screen_w * 0.75 or h < screen_h * 0.45:
        continue
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*%", value)
    if match and float(match.group(1)) <= 1.0:
        raise SystemExit(0)

raise SystemExit(1)
PY_NEW_PRODUCTS_TOP
}

list_position_signature() {
  local file="$1"
  python3 - "$file" <<'PY_LIST_POSITION_SIGNATURE'
import hashlib, json, re, sys

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_w = float(screen.get("width") or 393)
screen_h = float(screen.get("height") or 852)

blocked = {
    "微信", "更多", "关闭", "返回", "取消", "确定", "首页", "分类", "购物车", "我的",
    "新品首发", "限时团购", "分享", "加载中", "暂无更多", "没有更多",
}
product_terms = [
    "防晒", "裤", "裙", "外套", "连衣裙", "鞋", "鞋架", "茶壶", "抹布",
    "保温壶", "虾仁", "拌饭酱", "火龙果", "天麻", "馅饼", "鸡排", "鱼排",
    "牛排", "肉串", "护颈枕", "夏凉被", "四件套", "凉席", "被套", "蚊帐",
    "乳", "霜", "套装", "果", "食品", "枕", "被", "席", "锅", "壶", "杯",
]

rows = []
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    kind = str(e.get("kind", ""))
    rect = e.get("rect") or []
    if not label or len(rect) != 4 or kind not in {"StaticText", "Button", "Other"}:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    if y < 120 or y > screen_h - 25 or x < -100:
        continue
    if label in blocked or len(label) < 4:
        continue
    # 排除价格、规格、倒计时。这样倒计时每秒变化不会破坏位置签名。
    if re.fullmatch(r"[¥¥]?\s*\d+(?:\.\d+)?", label):
        continue
    if label in {":", "天", "时", "分", "秒", "共1款", "共2款"}:
        continue
    if re.match(r"^(已选|规格|共\d+款|\d+\s*(袋|盒|个|斤|瓶|支|条|箱|组|套))", label):
        continue
    if not re.search(r"[\u4e00-\u9fffA-Za-z]", label):
        continue

    in_left = 0 <= x <= screen_w * 0.48
    in_right = screen_w * 0.45 <= x <= screen_w
    card_shape = 45 <= w <= screen_w * 0.55 and 18 <= h <= 110
    product_like = any(term in label for term in product_terms) or len(label) >= 8
    if (in_left or in_right) and card_shape and product_like:
        rows.append((label, round(x / 4) * 4, round(y / 4) * 4, round(w / 4) * 4, round(h / 4) * 4))

rows = sorted(set(rows))
blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
print(hashlib.sha256(blob).hexdigest() if rows else "")
PY_LIST_POSITION_SIGNATURE
}

reset_new_products_to_top() {
  local max_scrolls="$1"
  local before="$STATE_DIR/scenario2-list-top-before.json"
  local after="$STATE_DIR/scenario2-list-top-after.json"

  save_elements "$before"
  if ! is_new_products_file "$before"; then
    log "准备回到第一页时，is_new_products_file 校验未通过，但继续执行列表顶部复位"
  fi

  # 不直接相信滚动条的初始百分比:部分小程序页面在中部也可能错误暴露 0%。
  # 统一至少执行一次向上浏览,并以商品卡片位置是否还能变化作为到顶依据。
  local previous_signature
  previous_signature="$(list_position_signature "$before")"
  local stable_count=0
  local attempt=1

  log "场景二开始前,将新品首发列表恢复到第一页"

  while [[ $attempt -le $max_scrolls ]]; do
    log "在商品内容区安全向列表顶部浏览: ${attempt}/${max_scrolls}, x=${LIST_TOP_SCROLL_X}, y=${LIST_TOP_SCROLL_Y}, dy=${LIST_TOP_SCROLL_DY}"
    phone_act "$(json_scroll_payload "$LIST_TOP_SCROLL_X" "$LIST_TOP_SCROLL_Y" "$LIST_TOP_SCROLL_DY")" >/dev/null || true
    sleep 1.5
    save_elements "$after"

    # 到顶时可能触发很短的下拉刷新;如果暂时不是列表,再等待刷新完成后复查。
    if ! is_new_products_file "$after"; then
      sleep 2
      save_elements "$after"
    fi

    local current_signature
    current_signature="$(list_position_signature "$after")"
    if [[ -n "$current_signature" && -n "$previous_signature" && "$current_signature" == "$previous_signature" ]]; then
      stable_count=$((stable_count + 1))
    else
      stable_count=0
    fi

    # 商品卡片位置在一次完整向上浏览后不再变化,说明继续向上已经无法移动。
    # 到达第一页时这一次动作可能触发下拉刷新,等待后商品卡片仍会回到相同位置。
    if [[ $stable_count -ge 1 ]]; then
      log "商品卡片位置已稳定,确认新品首发列表已到第一页"
      return 0
    fi

    previous_signature="$current_signature"
    cp "$after" "$before"
    attempt=$((attempt + 1))
  done

  save_elements "$after"
  if is_new_products_file "$after"; then
    log "已完成 ${max_scrolls} 次向上浏览;未暴露可靠滚动条百分比,按当前最顶部位置继续"
    return 0
  fi

  die_json "RESET_LIST_TOP_FAILED" "尝试回到新品首发第一页后,当前页面不再是商品列表"
}

return_to_wechat_chat_list() {
  local tmp="$STATE_DIR/scenario2-current-elements.json"
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

clear_search_if_possible() {
  local tmp="$STATE_DIR/scenario2-search-elements.json"
  save_elements "$tmp"
  local label
  label="$(find_label_contains "$tmp" "清除")"
  if [[ -n "$label" ]]; then
    phone_act "$(json_tap_label_payload "$label")" >/dev/null || true
    sleep 0.5
  fi
}

open_mini_program_internal() {
  local mini_program="$1"
  local tmp="$STATE_DIR/scenario2-mini-program-elements.json"

  log "打开微信"
  phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null
  sleep 3

  log "强制从微信聊天列表重新搜索小程序"
  if ! return_to_wechat_chat_list; then
    log "第一次返回聊天列表失败, 重新启动微信后再试一次"
    phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null || true
    sleep 3
    return_to_wechat_chat_list || die_json "CHAT_LIST_NOT_FOUND" "无法返回微信聊天列表"
  fi

  log "搜索小程序: ${mini_program}"
  phone_act "{\"type\":\"tap\",\"x\":$SEARCH_X,\"y\":$SEARCH_Y}" >/dev/null
  sleep 1

  clear_search_if_possible

  phone_act "$(json_text_payload "$mini_program")" >/dev/null
  sleep 2

  log "点击最近使用过的小程序第一条记录: x=${MINI_PROGRAM_RESULT_X} y=${MINI_PROGRAM_RESULT_Y}"
  phone_act "{\"type\":\"tap\",\"x\":$MINI_PROGRAM_RESULT_X,\"y\":$MINI_PROGRAM_RESULT_Y}" >/dev/null
  sleep 5

  local verify_attempt=1
  while [[ $verify_attempt -le 8 ]]; do
    save_elements "$tmp"
    if is_liangjiu_home_file "$tmp"; then
      log "已验证进入良久小程序"
      return 0
    fi
    sleep 1
    verify_attempt=$((verify_attempt + 1))
  done

  die_json "MINI_PROGRAM_NOT_VERIFIED" "未能验证进入小程序: ${mini_program}"
}

enter_new_products_internal() {
  local tmp="$STATE_DIR/scenario2-new-products-elements.json"
  local verify="$STATE_DIR/scenario2-new-products-verify.json"

  save_elements "$tmp"

  if is_new_products_file "$tmp"; then
    # 列表结构在"新品首发"和"爆款加开"下很像，元素树又不暴露文字颜色/下划线。
    # 即使已经像商品列表，也强制点一次左侧"新品首发"tab，避免停在相邻 tab。
    if select_new_products_tab_from_file "$tmp"; then
      :
    else
      # --skip-open 或 WDA 健康衔接时，页面已确认为商品列表，
      # 切回新品首发标签校验失败不阻塞，继续执行。
      log "切回新品首发标签校验未通过，但当前页面已确认为商品列表，继续执行"
    fi
  else
    local payload
    payload="$(find_new_products_tab_payload "$tmp")"
    log "通过顶部标签/坐标点击新品首发: ${payload}"
    phone_act "$payload" >/dev/null
  fi

  local attempt=1
  while [[ $attempt -le 8 ]]; do
    sleep 1
    save_elements "$verify"
    if is_new_products_file "$verify"; then
      log "已验证进入新品首发商品列表"
      return 0
    fi
    attempt=$((attempt + 1))
  done

  die_json "NEW_PRODUCTS_NOT_VERIFIED" "点击新品首发后,未能验证进入商品列表"
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
    if 120 <= y < 820:
        rows.append((str(e.get("kind", "")), label, round(x), round(y), round(w), round(h)))
rows.sort()
blob = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
print(hashlib.sha256(blob).hexdigest())
PY
}

find_product_candidate() {
  local file="$1"
  local title="$2"
  python3 - "$file" "$title" "$SCREEN_WIDTH" "$SCREEN_HEIGHT" "$PRODUCT_TAP_MIN_Y" "$PRODUCT_TAP_MAX_Y" "$PRODUCT_ALIGN_SCROLL_DY" <<'PY'
import json, re, sys
path, target = sys.argv[1], sys.argv[2].strip()
sw, sh = float(sys.argv[3]), float(sys.argv[4])
tap_min_y, tap_max_y = float(sys.argv[5]), float(sys.argv[6])
align_dy = int(float(sys.argv[7]))
with open(path, encoding="utf-8") as f:
    data = json.load(f)

def norm(s):
    return re.sub(r"[\s\u3000,,。.!!::;;、|/\\\--_()()\[\]【】]+", "", str(s or "").lower())

target_key = norm(target)
candidates = []
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    rect = e.get("rect") or []
    kind = str(e.get("kind", ""))
    if not label or len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    if y < 80 or y > 830 or w < 8 or h < 6:
        continue
    key = norm(label)
    if not key:
        continue
    if target in label or label in target or target_key in key or key in target_key:
        cy_px = y + h / 2
        safe_tap = tap_min_y <= cy_px <= tap_max_y
        if cy_px < tap_min_y:
            align_scroll_dy = -align_dy
            align_reason = "too_high"
        elif cy_px > tap_max_y:
            align_scroll_dy = align_dy
            align_reason = "too_low"
        else:
            align_scroll_dy = 0
            align_reason = ""
        # 靠上、面积大的标题优先。
        score = 0
        if safe_tap:
            score -= 80
        if target == label:
            score -= 100
        if target in label:
            score -= 50
        if target_key == key:
            score -= 30
        score += abs(int(cy_px - ((tap_min_y + tap_max_y) / 2)))
        score -= int(w * h / 100)
        cx = (x + w / 2) / sw
        cy = cy_px / sh
        candidates.append((
            score,
            label,
            max(0.01, min(0.99, cx)),
            max(0.01, min(0.99, cy)),
            [x, y, w, h],
            kind,
            safe_tap,
            cy_px,
            align_scroll_dy,
            align_reason,
        ))

if candidates:
    candidates.sort(key=lambda item: item[0])
    score, label, tx, ty, rect, kind, safe_tap, cy_px, align_scroll_dy, align_reason = candidates[0]
    print(json.dumps({
        "label": label,
        "tap_x": tx,
        "tap_y": ty,
        "tap_y_px": cy_px,
        "safe_tap": safe_tap,
        "align_scroll_dy": align_scroll_dy,
        "align_reason": align_reason,
        "rect": rect,
        "kind": kind,
    }, ensure_ascii=False))
PY
}

candidate_safe_tap() {
  local candidate_json="$1"
  python3 - "$candidate_json" <<'PY'
import json, sys
c = json.loads(sys.argv[1])
raise SystemExit(0 if c.get("safe_tap") is True else 1)
PY
}

candidate_align_scroll_dy() {
  local candidate_json="$1"
  python3 - "$candidate_json" <<'PY'
import json, sys
c = json.loads(sys.argv[1])
print(int(c.get("align_scroll_dy") or 0))
PY
}

tap_product_candidate() {
  local candidate_json="$1"
  python3 - "$candidate_json" <<'PY'
import json, sys
c = json.loads(sys.argv[1])
print(json.dumps({"type":"tap", "x": float(c["tap_x"]), "y": float(c["tap_y"])}, ensure_ascii=False))
PY
}

detail_file_matches_target() {
  local file="$1"
  local title="$2"
  python3 - "$file" "$title" <<'PY_DETAIL_MATCH'
import json, re, sys

path, target = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as f:
    data = json.load(f)

screen = data.get("screen") or {}
screen_h = float(screen.get("height") or 852)

def norm(value):
    return re.sub(r"[\s\u3000,,。.!!::;;、|/\\\--_()()\[\]【】]+", "", str(value or "").lower())

target_key = norm(target)
if len(target_key) < 4:
    raise SystemExit(1)

for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    rect = e.get("rect") or []
    if not label or len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    if x < -100 or y < 0 or y > screen_h:
        continue
    key = norm(label)
    if len(key) >= 4 and (target_key in key or key in target_key):
        raise SystemExit(0)

raise SystemExit(1)
PY_DETAIL_MATCH
}

wait_for_target_product_detail() {
  local out_dir="$1"
  local safe_name="$2"
  local title="$3"
  local verify_file="$out_dir/after-open-${safe_name}.json"
  local attempt=1

  while [[ $attempt -le 6 ]]; do
    sleep 1
    save_elements "$verify_file"

    if is_product_detail_file "$verify_file" && detail_file_matches_target "$verify_file" "$title"; then
      return 0
    fi

    # 如果连续几次仍然是列表,说明刚才没有点进详情页;继续复制会有误链风险。
    if [[ $attempt -ge 3 ]] && is_new_products_file "$verify_file"; then
      return 1
    fi

    attempt=$((attempt + 1))
  done

  return 1
}

find_and_open_product_from_list() {
  local title="$1"
  local max_scrolls="$2"
  local out_dir="$3"
  local safe_name="$4"

  local scroll_index=0
  local previous_signature=""
  local align_attempts=0

  while [[ $scroll_index -le $max_scrolls ]]; do
    local list_file="$out_dir/list-${safe_name}-$(printf '%02d' "$scroll_index").json"
    save_elements "$list_file"

    local candidate
    candidate="$(find_product_candidate "$list_file" "$title")"
    if [[ -n "$candidate" ]]; then
      if ! candidate_safe_tap "$candidate"; then
        local align_dy
        align_dy="$(candidate_align_scroll_dy "$candidate")"
        align_attempts=$((align_attempts + 1))
        log "找到 ${title},但候选不在安全点击区,先小幅对齐: ${candidate}, dy=${align_dy}"
        if [[ $align_attempts -gt 3 ]]; then
          log "候选连续多次无法进入安全点击区,停止该商品: ${title}"
          return 1
        fi
        if [[ "$align_dy" != "0" ]]; then
          phone_act "$(json_scroll_payload "$PRODUCT_SCROLL_X" "$PRODUCT_SCROLL_Y" "$align_dy")" >/dev/null || true
          sleep 1.5
          continue
        fi
      fi
      align_attempts=0

      log "找到商品: ${title}"
      log "点击候选: ${candidate}"
      phone_act "$(tap_product_candidate "$candidate")" >/dev/null
      if wait_for_target_product_detail "$out_dir" "$safe_name" "$title"; then
        printf '%s\n' "$candidate"
        return 0
      fi

      log "点击候选后未验证进入目标详情页,停止该商品,避免复制错误链接: ${title}"
      return_to_new_products_list || true
      return 1
    fi

    local current_signature
    current_signature="$(page_signature "$list_file")"
    if [[ -n "$previous_signature" && "$current_signature" == "$previous_signature" ]]; then
      log "列表页面没有变化, 停止查找: ${title}"
      break
    fi
    previous_signature="$current_signature"

    if [[ $scroll_index -ge $max_scrolls ]]; then
      break
    fi

    log "当前未找到 ${title}, 继续向下浏览"
    phone_act "$(json_scroll_payload "$PRODUCT_SCROLL_X" "$PRODUCT_SCROLL_Y" "$PRODUCT_SCROLL_DY")" >/dev/null
    sleep 2
    align_attempts=0
    scroll_index=$((scroll_index + 1))
  done

  return 1
}

collect_detail_pages() {
  local out_dir="$1"
  local safe_name="$2"
  local detail_scrolls="$3"

  local page=0
  while [[ $page -le $detail_scrolls ]]; do
    local file="$out_dir/detail-${safe_name}-$(printf '%02d' "$page").json"
    save_elements "$file"

    if [[ $page -lt $detail_scrolls ]]; then
      phone_act "$(json_scroll_payload "$DETAIL_SCROLL_X" "$DETAIL_SCROLL_Y" "$DETAIL_SCROLL_DY")" >/dev/null || true
      sleep 1
    fi

    page=$((page + 1))
  done
}

extract_detail_info() {
  local out_dir="$1"
  local safe_name="$2"
  local target_title="$3"
  python3 - "$out_dir" "$safe_name" "$target_title" <<'PY_DETAIL_EXTRACT'
import glob, json, re, sys

out_dir, safe_name, target = sys.argv[1], sys.argv[2], sys.argv[3]
files = sorted(glob.glob(f"{out_dir}/detail-{safe_name}-*.json"))


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


rows = []
for page_no, file in enumerate(files):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)
    for element in data.get("elements", []):
        label = norm(element.get("label", ""))
        rect = element.get("rect") or []
        kind = str(element.get("kind", ""))
        if not label or len(rect) != 4:
            continue
        try:
            x, y, w, h = map(float, rect)
        except Exception:
            continue
        if y < 55 or y > 825 or w < 3 or h < 3:
            continue
        rows.append({
            "label": label,
            "rect": [x, y, w, h],
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "cx": x + w / 2,
            "cy": y + h / 2,
            "kind": kind,
            "page": page_no,
        })

blocked_exact = {
    "返回", "更多", "关闭", "分享", "首页", "购物车", "客服", "我的",
    "新品首发", "确定", "取消", "复制链接", "分享好友", "静音", "全屏",
    "暂停", "播放", "进度条", "视频", "共1款", "|",
}
noise_contains = [
    "微信", "小程序", "良久素材", "良久团购", "加载中",
    "官方授权", "品质保证", "极速发货", "售后无忧",
]


def is_noise(value):
    if value in blocked_exact:
        return True
    if any(key in value for key in noise_contains):
        return True
    return len(value) < 1


# 商品名称:优先使用目标名称;元素树存在更完整的同名标题时,取最长匹配项。
name = target.strip()
name_candidates = []
for row in rows:
    value = row["label"]
    if is_noise(value):
        continue
    if target in value or value in target:
        name_candidates.append(value)
if name_candidates:
    name = sorted(set(name_candidates), key=len, reverse=True)[0]

# 价格:优先首屏上半部的货币符号+数字,兼容完整价格文本。
currency_number_re = re.compile(r"[¥¥]\s*(\d{1,6}(?:\.\d{1,2})?)")
keyword_number_re = re.compile(r"(?:商品价格|价格|售价|供货价|到手价|券后价|团购价|现价|活动价)[::\s]*[¥¥]?\s*(\d{1,6}(?:\.\d{1,2})?)")
standalone_number_re = re.compile(r"^\d{1,6}(?:\.\d{1,2})?$")

price_candidates = []
for row in rows:
    value = row["label"]
    match = currency_number_re.search(value)
    if match:
        price_candidates.append((0, row["page"], row["y"], f"¥{match.group(1)}", match.group(1)))
        continue
    match = keyword_number_re.search(value)
    if match:
        # 首屏商品区优先于详情长页中的营销文本价格。
        priority = 1 if row["page"] == 0 and row["y"] < 800 else 3
        price_candidates.append((priority, row["page"], row["y"], value, match.group(1)))

currency_rows = [row for row in rows if row["label"] in {"¥", "¥"}]
number_rows = [row for row in rows if standalone_number_re.fullmatch(row["label"])]
for currency in currency_rows:
    nearby = []
    for number in number_rows:
        if number["page"] != currency["page"]:
            continue
        dx = abs(number["cx"] - currency["cx"])
        dy = abs(number["cy"] - currency["cy"])
        if dy <= 45 and dx <= 150:
            nearby.append((dy + dx * 0.1, -number["h"], number))
    if nearby:
        nearby.sort(key=lambda item: (item[0], item[1]))
        number = nearby[0][2]
        priority = 0 if currency["page"] == 0 and currency["y"] < 800 else 2
        price_candidates.append((priority, currency["page"], min(currency["y"], number["y"]), f"{currency['label']}{number['label']}", number["label"]))

price_text = ""
price_value = None
if price_candidates:
    price_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    _, _, _, price_text, price_value = price_candidates[0]

# 规格:详情首屏已经明确暴露"已选:xxx",有该字段时只使用它,避免倒计时数字 42 被误判为尺码。
selected_values = []
selected_re = re.compile(r"已选\s*[::]\s*(.+)$")
for row in rows:
    value = row["label"]
    selected = selected_re.search(value)
    if not selected:
        continue
    selected_value = selected.group(1).strip(" ||")
    if selected_value and selected_value not in selected_values:
        selected_values.append(selected_value)

specs = []
if selected_values:
    specs = selected_values[:4]
else:
    # 没有"已选"时,才退化到明确的规格字段;不接受独立纯数字。
    explicit_spec_re = re.compile(r"^(?:【规格】|规格\s*[::]|规格[一二三四五六七八九十]\s*[::]|净含量\s*[::])\s*(.+)$", re.I)
    strong_spec_re = re.compile(
        r"(?:\d+\s*(?:袋|斤|个|瓶|支|条|箱|片|包|组|套|g|kg|mL|ml|L)(?:[/((]|$)|"
        r"\d+\s*[xX*]\s*\d+|XS|XXS|XL|XXL|2XL|3XL|4XL)",
        re.I,
    )
    for row in rows:
        value = row["label"]
        if is_noise(value) or value in {name, target}:
            continue
        if standalone_number_re.fullmatch(value):
            continue
        if currency_number_re.search(value) or keyword_number_re.search(value):
            continue
        explicit = explicit_spec_re.search(value)
        if explicit:
            candidate = explicit.group(1).strip() or value.strip()
        elif strong_spec_re.search(value) and len(value) <= 70:
            candidate = value.strip()
        else:
            continue
        if candidate and candidate not in specs:
            specs.append(candidate)

print(json.dumps({
    "name": name,
    "price_text": price_text,
    "price_value": price_value,
    "specs": specs[:8],
    "raw_label_count": len(rows),
}, ensure_ascii=False))
PY_DETAIL_EXTRACT
}

build_initial_copy() {
  local detail_json="$1"
  local product_link="$2"
  python3 - "$detail_json" "$product_link" <<'PY'
import json, sys

info = json.loads(sys.argv[1]) if sys.argv[1] else {}
link = sys.argv[2].strip()

name = str(info.get("name") or "").strip()
price_text = str(info.get("price_text") or "").strip()
price_value = info.get("price_value")
specs = [str(x).strip() for x in (info.get("specs") or []) if str(x).strip()]

if not price_text and price_value:
    price_text = f"¥{price_value}"
if not price_text:
    price_text = "未识别"

spec_text = ";".join(dict.fromkeys(specs)) if specs else "未识别"

lines = [
    f"商品名称:{name or '未识别'}",
    f"商品价格:{price_text}",
    f"商品规格:{spec_text}",
    f"商品链接:{link or '未获取'}",
]
print("\n".join(lines))
PY
}

read_host_clipboard() {
  local value=""
  value="$(pbpaste 2>/dev/null || true)"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
    return 0
  fi
  osascript -e 'the clipboard as text' 2>/dev/null || true
}

find_copy_link_payload() {
  local file="$1"
  python3 - "$file" "$SCREEN_WIDTH" "$SCREEN_HEIGHT" <<'PY_FIND_COPY'
import json, sys
path = sys.argv[1]
sw = float(sys.argv[2])
sh = float(sys.argv[3])
with open(path, encoding="utf-8") as f:
    data = json.load(f)
items = []
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    rect = e.get("rect") or []
    if "复制链接" not in label or len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue
    if x < 0 or y < 0 or x > sw or y > sh:
        continue
    tx = (x + w / 2) / sw
    ty = (y + h / 2) / sh
    items.append((y, x, tx, ty, label, [x, y, w, h]))
if items:
    items.sort(key=lambda v: (v[0], v[1]))
    _, _, tx, ty, label, rect = items[0]
    print(json.dumps({
        "type": "tap",
        "x": max(0.01, min(0.99, tx)),
        "y": max(0.01, min(0.99, ty)),
    }, ensure_ascii=False))
PY_FIND_COPY
}

find_top_right_more_payload() {
  local file="$1"
  python3 - "$file" "$SCREEN_WIDTH" "$SCREEN_HEIGHT" <<'PY_FIND_MORE'
import json, sys

path = sys.argv[1]
sw = float(sys.argv[2])
sh = float(sys.argv[3])

with open(path, encoding="utf-8") as f:
    data = json.load(f)

candidates = []
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    rect = e.get("rect") or []
    if len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    if "更多" not in label or "关闭" in label:
        continue
    if y > 180 or x + w < sw * 0.55:
        continue

    if w >= sw * 0.16:
        tx = x + w * 0.25
    else:
        tx = x + w / 2
    ty = y + h / 2

    tx = min(tx, sw * 0.83)
    candidates.append((y, x, tx / sw, ty / sh, label, [x, y, w, h]))

if candidates:
    candidates.sort(key=lambda item: (item[0], -item[1]))
    _, _, tx, ty, label, rect = candidates[0]
    print(json.dumps({
        "type": "tap",
        "x": max(0.01, min(0.99, tx)),
        "y": max(0.01, min(0.99, ty)),
    }, ensure_ascii=False))
PY_FIND_MORE
}

find_top_left_back_payload() {
  local file="$1"
  python3 - "$file" "$SCREEN_WIDTH" "$SCREEN_HEIGHT" <<'PY_FIND_BACK'
import json, sys

path = sys.argv[1]
sw = float(sys.argv[2])
sh = float(sys.argv[3])

with open(path, encoding="utf-8") as f:
    data = json.load(f)

candidates = []
for e in data.get("elements", []):
    label = str(e.get("label", "")).strip()
    rect = e.get("rect") or []
    if len(rect) != 4:
        continue
    try:
        x, y, w, h = map(float, rect)
    except Exception:
        continue

    label_ok = (
        label == "返回"
        or label.startswith("返回")
        or label in {"<", "‹", "〈", "左箭头"}
        or "返回上一页" in label
    )
    if not label_ok:
        continue
    if x > sw * 0.30 or y > 190:
        continue

    tx = x + w / 2
    ty = y + h / 2
    candidates.append((y, x, tx / sw, ty / sh, label, [x, y, w, h]))

if candidates:
    candidates.sort(key=lambda item: (item[0], item[1]))
    _, _, tx, ty, label, rect = candidates[0]
    print(json.dumps({
        "type": "tap",
        "x": max(0.01, min(0.99, tx)),
        "y": max(0.01, min(0.99, ty)),
    }, ensure_ascii=False))
PY_FIND_BACK
}


phone_inbox_get() {
  curl --noproxy "*" -sS --max-time 10 \
    -H "Authorization: Bearer $TOKEN" \
    "$HOST/agent/inbox"
}

drain_phone_inbox() {
  phone_inbox_get >/dev/null 2>&1 || true
}

extract_clipboard_from_inbox_json() {
  python3 -c '
import json, sys
try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)

candidates = []

def walk(value):
    if isinstance(value, dict):
        verb = str(value.get("verb") or value.get("type") or value.get("action") or "")
        data = value.get("data")
        texts = []
        for key in ("text", "clipboard", "value", "content", "product_link", "link"):
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                texts.append(item.strip())
        if isinstance(data, dict):
            for key in ("text", "clipboard", "value", "content", "product_link", "link"):
                item = data.get(key)
                if isinstance(item, str) and item.strip():
                    texts.append(item.strip())
        if verb in {"clipboard_export", "clipboard", "ios_clipboard", "product_link"}:
            candidates.extend(texts)
        elif texts:
            for item in texts:
                if "#小程序://" in item or item.startswith(("http://", "https://", "weixin://")):
                    candidates.append(item)
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)

walk(payload)
for item in reversed(candidates):
    if item:
        print(item)
        raise SystemExit(0)
raise SystemExit(1)
'
}

trigger_clipboard_shortcut_via_app() {
  local shortcut_name="$1"
  local app_file="$STATE_DIR/clipboard-shortcut-app.json"
  local search_file="$STATE_DIR/clipboard-shortcut-search.json"
  local launch_result=""
  local shortcut_label=""
  local nav_label=""
  local search_label=""

  log "在 iPhone 上直接打开快捷指令 App: bundle=${SHORTCUTS_APP_BUNDLE}"
  launch_result="$(phone_act "$(json_launch_payload "$SHORTCUTS_APP_BUNDLE")" 2>/dev/null || true)"
  sleep "$SHORTCUTS_APP_WAIT"

  if ! save_elements "$app_file" >/dev/null 2>&1; then
    log "打开快捷指令 App 后无法读取元素树: ${launch_result}"
    return 1
  fi

  # 关键修复:Shortcuts 会恢复上次停留页面。若已经停在目标编辑器,
  # 不能再按名称点击,否则点中的正是顶部标题,会弹出"重命名"等菜单。
  if is_shortcut_editor_file "$app_file" "$shortcut_name"; then
    log "快捷指令 App 已停留在目标编辑器,跳过标题点击,直接运行"
    run_shortcut_if_editor_opened "$shortcut_name" || return 1
    return 0
  fi

  # 若停留在其他快捷指令的编辑器,先返回列表。
  if is_any_shortcut_editor_file "$app_file"; then
    log "快捷指令 App 停留在其他编辑器,点击左上角返回快捷指令列表"
    phone_act '{"type":"tap","x":0.075,"y":0.095}' >/dev/null 2>&1 || true
    sleep 2
    save_elements "$app_file" >/dev/null 2>&1 || return 1
  fi

  # 最快路径:目标快捷指令已经显示在当前列表页。
  shortcut_label="$(find_label_contains "$app_file" "$shortcut_name")"
  if [[ -n "$shortcut_label" ]]; then
    log "在 iPhone 快捷指令列表中打开目标卡片: ${shortcut_label}"
    phone_act "$(json_tap_label_payload "$shortcut_label")" >/dev/null 2>&1 || return 1
    run_shortcut_if_editor_opened "$shortcut_name" || return 1
    return 0
  fi

  # 可能停留在"自动化/图库/文件夹"等页面,先尝试进入"快捷指令/所有快捷指令"。
  nav_label="$(find_label_contains "$app_file" "所有快捷指令")"
  if [[ -z "$nav_label" ]]; then
    nav_label="$(find_label_contains "$app_file" "快捷指令")"
  fi
  if [[ -n "$nav_label" ]]; then
    log "切换到快捷指令列表: ${nav_label}"
    phone_act "$(json_tap_label_payload "$nav_label")" >/dev/null 2>&1 || true
    sleep 2
    save_elements "$app_file" >/dev/null 2>&1 || true

    if is_shortcut_editor_file "$app_file" "$shortcut_name"; then
      log "切换后已经进入目标编辑器,直接运行"
      run_shortcut_if_editor_opened "$shortcut_name" || return 1
      return 0
    fi

    shortcut_label="$(find_label_contains "$app_file" "$shortcut_name")"
    if [[ -n "$shortcut_label" ]]; then
      log "在快捷指令列表中打开目标卡片: ${shortcut_label}"
      phone_act "$(json_tap_label_payload "$shortcut_label")" >/dev/null 2>&1 || return 1
      run_shortcut_if_editor_opened "$shortcut_name" || return 1
      return 0
    fi
  fi

  # 仍未出现时,使用快捷指令 App 内部搜索,不调用 macOS/iOS Spotlight。
  search_label="$(find_label_contains "$app_file" "搜索")"
  if [[ -n "$search_label" ]]; then
    log "使用快捷指令 App 内部搜索: ${shortcut_name}"
    phone_act "$(json_tap_label_payload "$search_label")" >/dev/null 2>&1 || true
  else
    log "元素树未暴露搜索框,点击快捷指令 App 顶部搜索区域"
    phone_act '{"type":"tap","x":0.50,"y":0.095}' >/dev/null 2>&1 || true
  fi

  sleep 1
  phone_act "$(json_text_payload "$shortcut_name")" >/dev/null 2>&1 || true
  sleep 2
  save_elements "$search_file" >/dev/null 2>&1 || true

  shortcut_label="$(find_label_contains "$search_file" "$shortcut_name")"
  if [[ -n "$shortcut_label" ]]; then
    log "通过快捷指令 App 搜索结果打开目标卡片: ${shortcut_label}"
    phone_act "$(json_tap_label_payload "$shortcut_label")" >/dev/null 2>&1 || return 1
    run_shortcut_if_editor_opened "$shortcut_name" || return 1
    return 0
  fi

  log "未在 iPhone 快捷指令 App 中找到: ${shortcut_name}"
  return 1
}


read_iphone_clipboard_via_shortcut() {
  local shortcut_name="$1"
  local timeout_seconds="$2"
  local raw=""
  local value=""
  local elapsed=0

  # 清空上次 Shortcut 回传,避免把旧商品链接当成当前链接。
  drain_phone_inbox
  if ! trigger_clipboard_shortcut_via_app "$shortcut_name"; then
    return 1
  fi

  while [[ $elapsed -lt $timeout_seconds ]]; do
    sleep 1
    elapsed=$((elapsed + 1))
    raw="$(phone_inbox_get 2>/dev/null || true)"
    if [[ -z "$raw" ]]; then
      continue
    fi
    value="$(printf '%s' "$raw" | extract_clipboard_from_inbox_json 2>/dev/null || true)"
    if [[ -n "$value" ]]; then
      log "已通过 iOS Shortcut /agent/inbox 收到商品链接"
      printf '%s\n' "$value"
      return 0
    fi
  done

  return 1
}

restore_wechat_after_shortcut() {
  local tmp="$STATE_DIR/after-clipboard-shortcut-wechat.json"
  log "结束快捷指令读取流程,重新切回微信"
  phone_act "$(json_launch_payload "$APP_BUNDLE")" >/dev/null 2>&1 || true
  sleep 2
  save_elements "$tmp" >/dev/null 2>&1 || true
}

read_link_from_host_clipboard_change() {
  local before_clipboard="$1"
  local attempt=1
  local value=""
  while [[ $attempt -le 12 ]]; do
    value="$(read_host_clipboard)"
    if [[ -n "$value" && "$value" != "$before_clipboard" ]]; then
      printf '%s\n' "$value"
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  return 1
}

copy_product_link_from_detail() {
  local out_dir="$1"
  local safe_name="$2"
  local target_title="${3:-}"
  local detail_file="$out_dir/before-share-${safe_name}.json"
  local menu_file="$out_dir/share-menu-${safe_name}.json"
  local after_copy_file="$out_dir/after-copy-${safe_name}.json"
  local copy_status_file="$out_dir/copy-status-${safe_name}.json"

  save_elements "$detail_file"

  if ! is_product_detail_file "$detail_file"; then
    die_json "DETAIL_NOT_VERIFIED_BEFORE_COPY" "复制链接前未验证到商品详情页,已停止,避免复制错误链接"
  fi
  if [[ -n "$target_title" ]] && ! detail_file_matches_target "$detail_file" "$target_title"; then
    die_json "DETAIL_TARGET_MISMATCH_BEFORE_COPY" "复制链接前详情页标题与目标商品不匹配: ${target_title}"
  fi

  local more_payload
  more_payload="$(find_top_right_more_payload "$detail_file")"

  if [[ -n "$more_payload" ]]; then
    log "通过顶部右侧元素点击更多按钮: ${more_payload}"
    phone_act "$more_payload" >/dev/null
  else
    log "元素树未找到顶部更多按钮, 使用安全坐标: x=${MORE_X} y=${MORE_Y}"
    phone_act "$(json_tap_xy_payload "$MORE_X" "$MORE_Y")" >/dev/null
  fi

  sleep 2
  save_elements "$menu_file"

  if is_chat_list_file "$menu_file"; then
    die_json "MORE_BUTTON_HIT_CLOSE" "点击详情页更多按钮时误触了小程序关闭按钮; 当前 MORE_X=${MORE_X}, MORE_Y=${MORE_Y}"
  fi

  local copy_payload
  copy_payload="$(find_copy_link_payload "$menu_file")"
  local before_clipboard
  before_clipboard="$(read_host_clipboard)"

  if [[ -n "$copy_payload" ]]; then
    log "通过分享菜单中的唯一坐标点击复制链接: ${copy_payload}"
    phone_act "$copy_payload" >/dev/null
  else
    log "分享菜单未识别到复制链接, 使用兜底坐标: x=${COPY_LINK_X} y=${COPY_LINK_Y}"
    phone_act "$(json_tap_xy_payload "$COPY_LINK_X" "$COPY_LINK_Y")" >/dev/null
  fi

  sleep 2
  save_elements "$after_copy_file" || true

  local still_copy_label
  still_copy_label="$(find_label_contains "$after_copy_file" "复制链接")"
  local copy_action_verified=false
  if [[ -z "$still_copy_label" ]] && ! is_chat_list_file "$after_copy_file"; then
    copy_action_verified=true
    log "已验证复制链接按钮执行后分享菜单关闭"
  else
    log "复制后分享菜单仍打开, 尝试点击取消"
    local cancel_label
    cancel_label="$(find_label_contains "$after_copy_file" "取消")"
    if [[ -n "$cancel_label" ]]; then
      phone_act "$(json_tap_label_payload "$cancel_label")" >/dev/null || true
    else
      phone_act "$(json_tap_xy_payload 0.50 0.22)" >/dev/null || true
    fi
    sleep 1
  fi

  local product_link=""
  local status="copy_button_not_verified"
  local actual_mode="$LINK_READ_MODE"

  case "$LINK_READ_MODE" in
    shortcut)
      if product_link="$(read_iphone_clipboard_via_shortcut "$CLIPBOARD_SHORTCUT_NAME" "$CLIPBOARD_SHORTCUT_TIMEOUT")"; then
        status="iphone_shortcut_inbox_received"
      else
        status="iphone_shortcut_inbox_timeout"
        product_link=""
      fi
      restore_wechat_after_shortcut
      ;;
    host)
      if product_link="$(read_link_from_host_clipboard_change "$before_clipboard")"; then
        status="host_clipboard_received"
      elif [[ "$copy_action_verified" == "true" ]]; then
        status="iphone_copy_verified_host_not_synced"
        product_link=""
      fi
      ;;
    auto)
      if product_link="$(read_iphone_clipboard_via_shortcut "$CLIPBOARD_SHORTCUT_NAME" "$CLIPBOARD_SHORTCUT_TIMEOUT")"; then
        status="iphone_shortcut_inbox_received"
        actual_mode="shortcut"
      else
        restore_wechat_after_shortcut
        if product_link="$(read_link_from_host_clipboard_change "$before_clipboard")"; then
          status="host_clipboard_received"
          actual_mode="host"
        elif [[ "$copy_action_verified" == "true" ]]; then
          status="iphone_copy_verified_but_no_return_channel"
          product_link=""
        fi
      fi
      # Shortcut 成功时也必须切回微信。
      if [[ "$status" == "iphone_shortcut_inbox_received" ]]; then
        restore_wechat_after_shortcut
      fi
      ;;
    *)
      die_json "INVALID_LINK_READ_MODE" "--link-read-mode 仅支持 shortcut、host、auto"
      ;;
  esac

  python3 - "$copy_status_file" "$status" "$copy_action_verified" "$actual_mode" "$product_link" <<'PY_COPY_STATUS'
import json, sys
path, status, verified, mode, value = sys.argv[1:]
with open(path, "w", encoding="utf-8") as f:
    json.dump({
        "status": status,
        "copy_action_verified": verified == "true",
        "read_mode": mode,
        "product_link": value,
    }, f, ensure_ascii=False, indent=2)
PY_COPY_STATUS

  printf '%s\n' "$product_link"
}

return_to_new_products_list() {
  local before="$STATE_DIR/scenario2-before-detail-back.json"
  local after="$STATE_DIR/scenario2-after-detail-back.json"
  local attempt=1
  local back_clicks=0

  # 等待"已复制"提示和分享菜单动画完成,再读取最新元素树。
  sleep 1
  save_elements "$before" || true

  # 若分享菜单仍覆盖在详情页,先明确关闭菜单。
  if is_share_menu_file "$before"; then
    local cancel_label
    cancel_label="$(find_label_contains "$before" "取消")"
    if [[ -n "$cancel_label" ]]; then
      log "返回商品列表前先关闭分享菜单: ${cancel_label}"
      phone_act "$(json_tap_label_payload "$cancel_label")" >/dev/null || true
    else
      log "分享菜单仍打开,点击菜单上方空白区域关闭"
      phone_act "$(json_tap_xy_payload 0.50 0.22)" >/dev/null || true
    fi
    sleep 1
    save_elements "$before" || true
  fi

  # 只有经过严格的可见区域判断,才能认为已经在列表页。
  if is_new_products_file "$before"; then
    if select_new_products_tab_from_file "$before"; then
      log "严格验证:当前确实已经在新品首发商品列表"
    else
      log "切回新品首发标签校验未通过，但当前页面已确认为商品列表，继续执行"
    fi
    return 0
  fi

  if is_chat_list_file "$before"; then
    die_json "DETAIL_STATE_LEFT_MINI_PROGRAM" "复制链接后已经退出到微信聊天列表,无法执行详情页返回"
  fi

  if is_liangjiu_home_file "$before" && ! is_product_detail_file "$before"; then
    log "复制链接后位于良久首页,重新进入新品首发"
    enter_new_products_internal
    return 0
  fi

  # 正常情况下此刻仍在商品详情页。优先使用元素树里的左上角返回按钮;
  # 若小程序未暴露返回按钮,则使用截图校准后的固定坐标。
  local back_payload
  back_payload="$(find_top_left_back_payload "$before")"

  if [[ -n "$back_payload" ]]; then
    log "点击详情页左上角返回按钮: ${back_payload}"
    phone_act "$back_payload" >/dev/null || true
  else
    log "详情页元素树未暴露返回按钮,使用固定坐标: x=${DETAIL_BACK_X} y=${DETAIL_BACK_Y}"
    phone_act "$(json_tap_xy_payload "$DETAIL_BACK_X" "$DETAIL_BACK_Y")" >/dev/null || true
  fi
  back_clicks=1

  while [[ $attempt -le 8 ]]; do
    sleep 1
    save_elements "$after" || true

    if is_new_products_file "$after"; then
      if select_new_products_tab_from_file "$after"; then
        log "已严格验证返回新品首发商品列表"
      else
        log "返回后切回新品首发标签校验未通过，但页面已确认为商品列表，继续执行"
      fi
      return 0
    fi

    if is_chat_list_file "$after"; then
      die_json "DETAIL_BACK_LEFT_MINI_PROGRAM" "点击详情页左上角返回按钮后退出到了微信聊天列表;已停止,避免继续误操作"
    fi

    if is_share_menu_file "$after"; then
      local cancel_label
      cancel_label="$(find_label_contains "$after" "取消")"
      if [[ -n "$cancel_label" ]]; then
        log "检测到分享菜单重新出现,先点击取消"
        phone_act "$(json_tap_label_payload "$cancel_label")" >/dev/null || true
      else
        phone_act "$(json_tap_xy_payload 0.50 0.22)" >/dev/null || true
      fi
      sleep 1
    elif is_product_detail_file "$after"; then
      # 第一次点击可能被"已复制"提示或动画吞掉;在第 3 次检查时补点一次。
      if [[ $attempt -eq 3 && $back_clicks -lt 2 ]]; then
        log "仍停留在商品详情页,补点一次左上角返回坐标: x=${DETAIL_BACK_X} y=${DETAIL_BACK_Y}"
        phone_act "$(json_tap_xy_payload "$DETAIL_BACK_X" "$DETAIL_BACK_Y")" >/dev/null || true
        back_clicks=$((back_clicks + 1))
      fi
    elif is_liangjiu_home_file "$after"; then
      log "返回后落在良久首页,自动重新进入新品首发"
      enter_new_products_internal
      return 0
    fi

    attempt=$((attempt + 1))
  done

  die_json "NEW_PRODUCTS_LIST_NOT_VERIFIED" "已点击详情页左上角返回按钮,但 8 秒内未验证回到新品首发列表"
}

safe_filename() {
  python3 - "$1" <<'PY'
import re, sys
s = sys.argv[1]
s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", s).strip("-")
print((s[:40] or "product"))
PY
}

parse_products_to_file() {
  local products="$1"
  local products_file="$2"
  python3 - "$products" "$products_file" <<'PY'
import re, sys
raw, path = sys.argv[1], sys.argv[2]
items = [x.strip() for x in re.split(r"[,,\n]+", raw) if x.strip()]
with open(path, "w", encoding="utf-8") as f:
    for item in items:
        f.write(item + "\n")
print(len(items))
PY
}

cmd_promote_products() {
  local mini_program="良久素材"
  local products="$DEFAULT_PRODUCTS"
  local products_file=""
  local out_dir=""
  local max_scrolls_per_product=8
  local detail_scrolls=0
  local top_scrolls="$LIST_TOP_MAX_SCROLLS"
  local reset_list_top=1
  local skip_open=0
  local dry_run=0

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mini-program) mini_program="${2:-}"; shift 2 ;;
      --products) products="${2:-}"; shift 2 ;;
      --products-file) products_file="${2:-}"; shift 2 ;;
      --out-dir) out_dir="${2:-}"; shift 2 ;;
      --max-scrolls-per-product) max_scrolls_per_product="${2:-}"; shift 2 ;;
      --detail-scrolls) detail_scrolls="${2:-}"; shift 2 ;;
      --top-scrolls) top_scrolls="${2:-}"; shift 2 ;;
      --no-reset-list-top) reset_list_top=0; shift ;;
      --new-products-x) NEW_PRODUCTS_X="${2:-}"; shift 2 ;;
      --new-products-y) NEW_PRODUCTS_Y="${2:-}"; shift 2 ;;
      --copy-link-x) COPY_LINK_X="${2:-}"; shift 2 ;;
      --copy-link-y) COPY_LINK_Y="${2:-}"; shift 2 ;;
      --more-x) MORE_X="${2:-}"; shift 2 ;;
      --more-y) MORE_Y="${2:-}"; shift 2 ;;
      --detail-back-x) DETAIL_BACK_X="${2:-}"; shift 2 ;;
      --detail-back-y) DETAIL_BACK_Y="${2:-}"; shift 2 ;;
      --link-read-mode) LINK_READ_MODE="${2:-}"; shift 2 ;;
      --clipboard-shortcut-name) CLIPBOARD_SHORTCUT_NAME="${2:-}"; shift 2 ;;
      --shortcut-timeout) CLIPBOARD_SHORTCUT_TIMEOUT="${2:-}"; shift 2 ;;
      --skip-open) skip_open=1; shift ;;
      --dry-run) dry_run=1; shift ;;
      *) die_json "INVALID_ARGUMENT" "未知参数: $1" ;;
    esac
  done

  [[ "$max_scrolls_per_product" =~ ^[0-9]+$ ]] || die_json "INVALID_MAX_SCROLLS" "--max-scrolls-per-product 必须是整数"
  [[ "$detail_scrolls" =~ ^[0-9]+$ ]] || die_json "INVALID_DETAIL_SCROLLS" "--detail-scrolls 必须是整数"
  [[ "$top_scrolls" =~ ^[0-9]+$ ]] || die_json "INVALID_TOP_SCROLLS" "--top-scrolls 必须是整数"
  [[ "$LIST_TOP_SCROLL_DY" =~ ^-?[0-9]+$ ]] || die_json "INVALID_TOP_SCROLL_DY" "WECHAT_IPHONE_LIST_TOP_SCROLL_DY 必须是整数"
  [[ "$PRODUCT_SCROLL_DY" =~ ^-?[0-9]+$ ]] || die_json "INVALID_PRODUCT_SCROLL_DY" "WECHAT_IPHONE_PRODUCT_SCROLL_DY 必须是整数"
  [[ "$PRODUCT_TAP_MIN_Y" =~ ^[0-9]+$ ]] || die_json "INVALID_PRODUCT_TAP_MIN_Y" "WECHAT_IPHONE_PRODUCT_TAP_MIN_Y 必须是整数"
  [[ "$PRODUCT_TAP_MAX_Y" =~ ^[0-9]+$ ]] || die_json "INVALID_PRODUCT_TAP_MAX_Y" "WECHAT_IPHONE_PRODUCT_TAP_MAX_Y 必须是整数"
  [[ "$PRODUCT_ALIGN_SCROLL_DY" =~ ^[0-9]+$ ]] || die_json "INVALID_PRODUCT_ALIGN_SCROLL_DY" "WECHAT_IPHONE_PRODUCT_ALIGN_SCROLL_DY 必须是整数"
  [[ "$PRODUCT_TAP_MIN_Y" -lt "$PRODUCT_TAP_MAX_Y" ]] || die_json "INVALID_PRODUCT_TAP_RANGE" "商品点击安全区必须满足 min_y < max_y"

  # 防止自定义参数再次把手势终点带到顶部状态栏。
  # 按当前 WDA 滚动实现估算:终点 = y * 屏幕高度 + dy。
  # 终点至少保留在屏幕 28% 以下,同时限制单次上滑幅度不超过 320px。
  if ! python3 - "$LIST_TOP_SCROLL_Y" "$LIST_TOP_SCROLL_DY" "$SCREEN_HEIGHT" <<'PY_SAFE_TOP_GESTURE'
import sys
y = float(sys.argv[1])
dy = int(sys.argv[2])
h = float(sys.argv[3])
start = y * h
end = start + dy
safe = (0.55 <= y <= 0.85 and -320 <= dy <= -80 and end >= h * 0.28)
raise SystemExit(0 if safe else 1)
PY_SAFE_TOP_GESTURE
  then
    die_json "UNSAFE_TOP_SCROLL_GESTURE" "回到顶部的手势参数不安全;建议使用 y=0.72、dy=-240,避免拉出状态栏或锁屏界面"
  fi
  [[ "$CLIPBOARD_SHORTCUT_TIMEOUT" =~ ^[0-9]+$ ]] || die_json "INVALID_SHORTCUT_TIMEOUT" "--shortcut-timeout 必须是整数"
  case "$LINK_READ_MODE" in shortcut|host|auto) ;; *) die_json "INVALID_LINK_READ_MODE" "--link-read-mode 仅支持 shortcut、host、auto" ;; esac

  init_runtime
  assert_ready
  acquire_lock

  if [[ -z "$out_dir" ]]; then
    out_dir="$STATE_DIR/promote-products-$(date +%Y%m%d-%H%M%S)"
  fi
  mkdir -p "$out_dir"

  local product_list_file="$out_dir/target-products.txt"
  if [[ -n "$products_file" ]]; then
    [[ -f "$products_file" ]] || die_json "PRODUCTS_FILE_NOT_FOUND" "找不到商品文件: $products_file"
    cp "$products_file" "$product_list_file"
  else
    parse_products_to_file "$products" "$product_list_file" >/dev/null
  fi

  local product_count
  product_count="$(grep -cve '^[[:space:]]*$' "$product_list_file" || true)"
  [[ "$product_count" -gt 0 ]] || die_json "PRODUCTS_REQUIRED" "需要 --products 或 --products-file"

  if [[ $skip_open -eq 0 ]]; then
    open_mini_program_internal "$mini_program"
  else
    log "已启用 --skip-open, 跳过打开微信和搜索小程序"
  fi

  if [[ $skip_open -eq 1 ]]; then
    log "--skip-open: WDA 衔接模式, 跳过 enter_new_products_internal, 直接回到列表顶部"
  else
    enter_new_products_internal
  fi

  if [[ $reset_list_top -eq 1 ]]; then
    reset_new_products_to_top "$top_scrolls"
  else
    log "已启用 --no-reset-list-top, 保留当前商品列表滚动位置"
  fi

  if [[ $dry_run -eq 1 ]]; then
    python3 - "$mini_program" "$out_dir" "$product_list_file" <<'PY'
import json, sys
products = [x.strip() for x in open(sys.argv[3], encoding="utf-8") if x.strip()]
print(json.dumps({
    "ok": True,
    "action": "promote-products",
    "dry_run": True,
    "mini_program": sys.argv[1],
    "out_dir": sys.argv[2],
    "products": products,
    "note": "dry-run 只进入新品首发, 不点击商品, 不复制链接。",
}, ensure_ascii=False))
PY
    return 0
  fi

  local result_jsonl="$out_dir/results.jsonl"
  local promotions_txt="$out_dir/initial-copies.txt"
  : > "$result_jsonl"
  : > "$promotions_txt"

  local index=0
  while IFS= read -r target_title || [[ -n "$target_title" ]]; do
    target_title="$(printf '%s' "$target_title" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -n "$target_title" ]] || continue

    index=$((index + 1))
    local safe_name
    safe_name="$(safe_filename "$(printf '%02d-%s' "$index" "$target_title")")"

    log "处理第 ${index}/${product_count} 个商品: ${target_title}"

    local candidate_json=""
    if ! candidate_json="$(find_and_open_product_from_list "$target_title" "$max_scrolls_per_product" "$out_dir" "$safe_name")"; then
      log "未找到商品: ${target_title}"
      python3 - "$result_jsonl" "$target_title" "$index" <<'PY'
import json, sys
path, title, index = sys.argv[1], sys.argv[2], int(sys.argv[3])
item = {"index": index, "target_title": title, "ok": False, "error": "PRODUCT_NOT_FOUND"}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(item, ensure_ascii=False) + "\n")
PY
      continue
    fi

    log "采集商品详情: ${target_title}"
    collect_detail_pages "$out_dir" "$safe_name" "$detail_scrolls"

    local detail_json
    detail_json="$(extract_detail_info "$out_dir" "$safe_name" "$target_title")"

    local product_link
    product_link="$(copy_product_link_from_detail "$out_dir" "$safe_name" "$target_title")"

    local initial_copy
    initial_copy="$(build_initial_copy "$detail_json" "$product_link")"

    printf '【%s】\n%s\n\n' "$target_title" "$initial_copy" >> "$promotions_txt"

    local copy_status_file="$out_dir/copy-status-${safe_name}.json"
    python3 - "$result_jsonl" "$index" "$target_title" "$candidate_json" "$detail_json" "$product_link" "$initial_copy" "$copy_status_file" <<'PY_RESULT_ITEM'
import json, os, sys
path = sys.argv[1]
copy_status = {}
if os.path.exists(sys.argv[8]):
    with open(sys.argv[8], encoding="utf-8") as f:
        copy_status = json.load(f)
status = copy_status.get("status")
warning = None
if not sys.argv[6]:
    if status == "iphone_shortcut_inbox_timeout":
        warning = "iPhone 已执行复制,但未收到快捷指令向 /agent/inbox 回传的链接。"
    elif status == "iphone_copy_verified_host_not_synced":
        warning = "已验证 iPhone 端复制链接动作成功,但通用剪贴板未同步到 Mac。"
    elif status == "iphone_copy_verified_but_no_return_channel":
        warning = "iPhone 端复制成功,但 Shortcut inbox 与通用剪贴板均未返回链接。"
    else:
        warning = "未获取商品链接,请检查复制链接动作和链接回传通道。"
item = {
    "index": int(sys.argv[2]),
    "target_title": sys.argv[3],
    "ok": True,
    "list_candidate": json.loads(sys.argv[4]) if sys.argv[4] else None,
    "detail": json.loads(sys.argv[5]) if sys.argv[5] else {},
    "product_link": sys.argv[6],
    "link_copy": copy_status,
    "initial_copy": sys.argv[7],
    "warning": warning,
}
with open(path, "a", encoding="utf-8") as f:
    f.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
PY_RESULT_ITEM

    return_to_new_products_list
  done < "$product_list_file"

  local summary_file="$out_dir/summary.json"
  python3 - "$mini_program" "$out_dir" "$result_jsonl" "$promotions_txt" "$summary_file" <<'PY'
import json, sys
mini_program, out_dir, result_jsonl, promotions_txt, summary_file = sys.argv[1:]
items = []
with open(result_jsonl, encoding="utf-8") as f:
    for line in f:
        if line.strip():
            items.append(json.loads(line))
success_count = sum(1 for x in items if x.get("ok"))
summary = {
    "ok": success_count == len(items) and len(items) > 0,
    "action": "promote-products",
    "mini_program": mini_program,
    "source_page": "新品首发",
    "target_count": len(items),
    "success_count": success_count,
    "out_dir": out_dir,
    "results_jsonl": result_jsonl,
    "initial_copies_txt": promotions_txt,
    "results": items,
    "warning": None if success_count == len(items) else "部分商品未找到或未复制到链接, 请查看 results。",
}
with open(summary_file, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False))
PY
}


cmd_test_clipboard_bridge() {
  local shortcut_name="$CLIPBOARD_SHORTCUT_NAME"
  local timeout_seconds="$CLIPBOARD_SHORTCUT_TIMEOUT"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --clipboard-shortcut-name) shortcut_name="${2:-}"; shift 2 ;;
      --shortcut-timeout) timeout_seconds="${2:-}"; shift 2 ;;
      *) die_json "INVALID_ARGUMENT" "未知参数: $1" ;;
    esac
  done

  [[ "$timeout_seconds" =~ ^[0-9]+$ ]] || die_json "INVALID_SHORTCUT_TIMEOUT" "--shortcut-timeout 必须是整数"
  init_runtime
  assert_ready
  acquire_lock

  local value=""
  if value="$(read_iphone_clipboard_via_shortcut "$shortcut_name" "$timeout_seconds")"; then
    restore_wechat_after_shortcut
    python3 - "$shortcut_name" "$value" <<'PY_TEST_BRIDGE'
import json, sys
print(json.dumps({
    "ok": True,
    "action": "test-clipboard-bridge",
    "shortcut_name": sys.argv[1],
    "clipboard": sys.argv[2],
}, ensure_ascii=False))
PY_TEST_BRIDGE
  else
    restore_wechat_after_shortcut
    die_json "CLIPBOARD_SHORTCUT_TIMEOUT" "未在 ${timeout_seconds} 秒内从 /agent/inbox 收到快捷指令回传"
  fi
}

usage() {
  cat <<'USAGE'
用法:
  wechat-iphone-scenario2 promote-products [参数]
  wechat-iphone-scenario2 test-clipboard-bridge [参数]

常用示例:
  ./wechat-iphone-scenario2-v13-safe-reset-list-top.sh promote-products \
    --products "<PRODUCT_1>,<PRODUCT_2>" \
    --new-products-x 0.105 \
    --new-products-y 0.805

参数:
  --products "商品1,商品2,..."              指定商品名, 支持中文逗号/英文逗号/换行
  --products-file FILE                     从文件读取商品名, 每行一个
  --max-scrolls-per-product N              每个商品最多向下找 N 次, 默认 8
  --detail-scrolls N                       详情页额外向下滚动 N 次, 默认 0;名称/价格/规格通常在首屏
  --top-scrolls N                          场景二开始前最多向上浏览 N 次, 默认 30
  --no-reset-list-top                      不自动回到新品首发第一页;默认会自动回到第一页
  --out-dir DIR                            输出目录
  --skip-open                              跳过打开微信和搜索小程序, 当前必须已在良久首页或新品首发
  --dry-run                                只进入新品首发, 不点击商品
  --new-products-x/y                       新品首发入口坐标, 当前建议 0.105 / 0.805
  --more-x/y                               商品详情页右上角"..."坐标, 默认 0.78 / 0.095; 0.88 会点到关闭按钮
  --detail-back-x/y                         商品详情页左上角返回按钮坐标, 默认 0.055 / 0.095
  --copy-link-x/y                          分享面板复制链接兜底坐标, 默认 0.82 / 0.88
  --link-read-mode MODE                    shortcut(默认)/ host / auto
  --clipboard-shortcut-name NAME           iPhone 快捷指令名称, 默认 IU Clipboard Export
  --shortcut-timeout N                     等待 /agent/inbox 回传秒数, 默认 25
  环境变量 WECHAT_IPHONE_SHORTCUTS_APP_BUNDLE  快捷指令 App Bundle ID, 默认 com.apple.shortcuts
  环境变量 WECHAT_IPHONE_SHORTCUT_RUN_X/Y       编辑器右下角运行按钮兜底坐标, 默认 0.86/0.94
  环境变量 WECHAT_IPHONE_SHORTCUTS_APP_WAIT    打开快捷指令 App 后等待秒数, 默认 3
  环境变量 WECHAT_IPHONE_PRODUCT_SCROLL_DY      商品列表向下查找的滚动距离, 默认 640(约两行/4件)
  环境变量 WECHAT_IPHONE_PRODUCT_TAP_MIN_Y/MAX_Y 商品标题安全点击区, 默认 260/780
  环境变量 WECHAT_IPHONE_LIST_TOP_SCROLL_DY    回到第一页时的滚动距离, 默认 -240
  环境变量 WECHAT_IPHONE_LIST_TOP_MAX_SCROLLS 最大向上浏览次数, 默认 30

输出:
  summary.json       汇总结果
  results.jsonl      每个商品一行结构化结果
  initial-copies.txt  商品详情信息与链接拼接后的初始文案, 每个商品一段
  detail-*.json      每个商品详情页原始元素树
  share-menu-*.json  分享菜单元素树
  copy-status-*.json 复制动作验证与主机剪贴板同步状态
USAGE
}

main() {
  local command="${1:-}"
  [[ $# -gt 0 ]] && shift

  case "$command" in
    promote-products|process-products) cmd_promote_products "$@" ;;
    test-clipboard-bridge) cmd_test_clipboard_bridge "$@" ;;
    help|-h|--help|"") usage ;;
    *) die_json "UNKNOWN_COMMAND" "未知命令: $command" ;;
  esac
}

main "$@"
