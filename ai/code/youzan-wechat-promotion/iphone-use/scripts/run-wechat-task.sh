#!/usr/bin/env bash
# Task-level evidence and send-once guard around the original wechat-iphone snapshot.
# macOS / Bash 3.2 compatible

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WECHAT_BIN="${WECHAT_IPHONE_BIN:-$SCRIPT_DIR/wechat-iphone}"
TASK_ROOT="${WECHAT_TASK_ROOT:-$HOME/.iphone-use/wechat-iphone/tasks}"

usage() {
  printf '%s\n' \
    'Usage:' \
    '  run-wechat-task.sh --task-id ID --mode preflight' \
    '  run-wechat-task.sh --task-id ID --mode dry-run --group GROUP --message-file FILE' \
    '  run-wechat-task.sh --task-id ID --mode send --group GROUP --message-file FILE' \
    '' \
    'Exit codes: 0=ready/success, 1=failed, 2=sent but not fully verified, 75=busy.'
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

task_id=""
mode=""
group=""
message_file=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-id) task_id="${2:-}"; shift 2 ;;
    --mode) mode="${2:-}"; shift 2 ;;
    --group) group="${2:-}"; shift 2 ;;
    --message-file) message_file="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) die_json "INVALID_ARGUMENT" "unknown argument: $1" ;;
  esac
done

[[ "$task_id" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$ ]] || \
  die_json "INVALID_TASK_ID" "task-id must match [A-Za-z0-9][A-Za-z0-9._-]{0,127}"
case "$mode" in
  preflight) ;;
  dry-run|send)
    [[ -n "$group" ]] || die_json "GROUP_REQUIRED" "--group is required"
    [[ -f "$message_file" ]] || die_json "MESSAGE_FILE_REQUIRED" "message file not found: $message_file"
    ;;
  *) die_json "INVALID_MODE" "mode must be preflight, dry-run, or send" ;;
esac
[[ -x "$WECHAT_BIN" ]] || die_json "WECHAT_IPHONE_NOT_EXECUTABLE" "not executable: $WECHAT_BIN"

mkdir -p "$TASK_ROOT"
runner_lock="${WECHAT_TASK_LOCK_DIR:-$TASK_ROOT/.phone-controller.lock}"
if ! mkdir "$runner_lock" 2>/dev/null; then
  die_json "PHONE_CONTROLLER_BUSY" "another managed phone task is running" 75
fi
printf '%s\n' "$$" > "$runner_lock/pid"
cleanup_lock() {
  rm -f "$runner_lock/pid"
  rmdir "$runner_lock" 2>/dev/null || true
}
trap cleanup_lock EXIT
trap 'exit 130' INT TERM HUP

task_dir="$TASK_ROOT/$task_id"
run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$-$mode"
run_dir="$task_dir/invocations/$run_id"
state_dir="$run_dir/state"
mkdir -p "$state_dir"

message=""
if [[ "$mode" != "preflight" ]]; then
  message="$(<"$message_file")"
  [[ -n "$message" ]] || die_json "MESSAGE_EMPTY" "message file is empty"

  if ! python3 - "$task_dir/task.json" "$task_id" "$group" "$message" <<'PY'
import hashlib
import json
import os
import sys

path, task_id, group, message = sys.argv[1:]
identity = {
    "task_id": task_id,
    "group": group,
    "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
}
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        current = json.load(f)
    if current != identity:
        raise SystemExit(3)
else:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp = path + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(identity, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(temp, path)
PY
  then
    die_json "TASK_IDENTITY_CONFLICT" "task-id was already bound to a different group or message"
  fi
  printf '%s\n' "$message" > "$run_dir/message.txt"
fi

result_file="$run_dir/wechat-result.json"
doctor_file="$run_dir/doctor.json"
status_file="$run_dir/status.json"
command_exit=0
send_invoked=false

if [[ "$mode" == "preflight" ]]; then
  set +e
  WECHAT_IPHONE_STATE_DIR="$state_dir" "$WECHAT_BIN" doctor \
    >"$doctor_file" 2>"$run_dir/doctor.log"
  doctor_exit=$?
  WECHAT_IPHONE_STATE_DIR="$state_dir" "$WECHAT_BIN" status \
    >"$status_file" 2>"$run_dir/status.log"
  status_exit=$?
  set -e
  if [[ $doctor_exit -ne 0 || $status_exit -ne 0 ]]; then
    command_exit=1
  fi
else
  send_marker="$task_dir/send-invoked"
  command=("$WECHAT_BIN" send --group "$group" --message "$message")
  if [[ "$mode" == "dry-run" ]]; then
    command+=(--dry-run)
  else
    if ! mkdir "$send_marker" 2>/dev/null; then
      die_json "SEND_ALREADY_INVOKED" "this task-id has already consumed its send attempt"
    fi
    send_invoked=true
    python3 - "$send_marker/marker.json" "$task_id" "$run_id" <<'PY'
import json, sys
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump({"task_id": sys.argv[2], "run_id": sys.argv[3], "send_invoked": True}, f, indent=2)
    f.write("\n")
PY
  fi

  set +e
  WECHAT_IPHONE_STATE_DIR="$state_dir" "${command[@]}" \
    >"$result_file" 2>"$run_dir/wechat.log"
  command_exit=$?
  set -e
fi

report_file="$run_dir/report.json"
python3 - "$report_file" "$task_id" "$mode" "$command_exit" "$send_invoked" \
  "$run_dir" "$result_file" "$doctor_file" "$status_file" <<'PY'
import json
import sys

report_path, task_id, mode, exit_code, send_invoked, evidence_dir, result_path, doctor_path, status_path = sys.argv[1:]
exit_code = int(exit_code)

def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

result = load(result_path)
doctor = load(doctor_path)
phone_status = load(status_path)
sent = result.get("sent") is True
verified = result.get("verified") is True
group_verified = result.get("group_still_open") is True
message_visible = result.get("message_visible") is True

if mode == "preflight":
    ok = exit_code == 0 and doctor.get("ok") is True and phone_status.get("ready") is True
    state = "PREFLIGHT_READY" if ok else "FAILED"
    warning = None if ok else "doctor/status did not satisfy the ready gate"
elif mode == "dry-run":
    ok = exit_code == 0 and result.get("ok") is True and result.get("dry_run") is True and result.get("prepared") is True
    state = "DRY_RUN_READY" if ok else "FAILED"
    warning = result.get("warning") or result.get("message")
else:
    ok = exit_code == 0 and sent and verified
    if sent and not verified:
        state = "SENT_UNVERIFIED"
    elif ok:
        state = "SUCCESS"
    else:
        state = "FAILED"
    warning = result.get("warning") or result.get("message")

report = {
    "ok": ok,
    "task_id": task_id,
    "mode": mode,
    "status": state,
    "command_exit_code": exit_code,
    "send_invoked": send_invoked == "true",
    "sent": sent,
    "verified": verified,
    "group_verified": group_verified,
    "message_visible": message_visible,
    "error": result.get("error"),
    "warning": warning,
    "evidence_dir": evidence_dir,
}
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
    f.write("\n")
print(json.dumps(report, ensure_ascii=False))
PY

if [[ "$mode" == "send" ]]; then
  if python3 - "$report_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    report = json.load(f)
raise SystemExit(0 if report["status"] == "SENT_UNVERIFIED" else 1)
PY
  then
    exit 2
  fi
fi

python3 - "$report_file" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    report = json.load(f)
raise SystemExit(0 if report["ok"] else 1)
PY
