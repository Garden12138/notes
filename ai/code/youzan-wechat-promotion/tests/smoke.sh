#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WECHAT="$ROOT/iphone-use/scripts/wechat-iphone"
RUNNER="$ROOT/iphone-use/scripts/run-wechat-task.sh"
FAKE="$ROOT/tests/fixtures/fake-wechat-iphone"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

bash -n "$WECHAT"
bash -n "$RUNNER"
bash -n "$FAKE"
"$WECHAT" --help >/dev/null

printf '%s\n' 'single line message <PRODUCT_LINK>' > "$TMP_DIR/message.txt"
printf '%s\n' 'unverified message <PRODUCT_LINK>' > "$TMP_DIR/unverified.txt"

env WECHAT_IPHONE_BIN="$FAKE" WECHAT_TASK_ROOT="$TMP_DIR/tasks" \
  "$RUNNER" --task-id preflight-001 --mode preflight > "$TMP_DIR/preflight.json"
env WECHAT_IPHONE_BIN="$FAKE" WECHAT_TASK_ROOT="$TMP_DIR/tasks" \
  "$RUNNER" --task-id dry-run-001 --mode dry-run --group '<TARGET_WECHAT_GROUP>' \
  --message-file "$TMP_DIR/message.txt" > "$TMP_DIR/dry-run.json"
env WECHAT_IPHONE_BIN="$FAKE" WECHAT_TASK_ROOT="$TMP_DIR/tasks" \
  "$RUNNER" --task-id send-001 --mode send --group '<TARGET_WECHAT_GROUP>' \
  --message-file "$TMP_DIR/message.txt" > "$TMP_DIR/send.json"

if env WECHAT_IPHONE_BIN="$FAKE" WECHAT_TASK_ROOT="$TMP_DIR/tasks" \
  "$RUNNER" --task-id send-001 --mode send --group '<TARGET_WECHAT_GROUP>' \
  --message-file "$TMP_DIR/message.txt" > "$TMP_DIR/retry.json"; then
  printf '%s\n' 'send-once guard failed' >&2
  exit 1
fi

set +e
env WECHAT_IPHONE_BIN="$FAKE" WECHAT_TASK_ROOT="$TMP_DIR/tasks" \
  "$RUNNER" --task-id unverified-001 --mode send --group '<TARGET_WECHAT_GROUP>' \
  --message-file "$TMP_DIR/unverified.txt" > "$TMP_DIR/unverified.json"
unverified_exit=$?
set -e
[[ $unverified_exit -eq 2 ]]

python3 - "$TMP_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])

def read(name):
    return json.loads((root / name).read_text(encoding="utf-8"))

assert read("preflight.json")["status"] == "PREFLIGHT_READY"
assert read("dry-run.json")["status"] == "DRY_RUN_READY"
assert read("send.json")["status"] == "SUCCESS"
assert read("retry.json")["error"] == "SEND_ALREADY_INVOKED"
assert read("unverified.json")["status"] == "SENT_UNVERIFIED"
assert (root / "tasks/send-001/send-invoked/marker.json").is_file()
assert (root / "tasks/unverified-001/send-invoked/marker.json").is_file()
PY

printf '%s\n' 'smoke test passed'

