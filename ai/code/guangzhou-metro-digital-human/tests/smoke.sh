#!/usr/bin/env bash

set -euo pipefail

OPENAVATAR_ROOT="${OPENAVATAR_ROOT:-}"
DIFY_DATA_DIR="${DIFY_DATA_DIR:-}"
SERVICE_URL="${SERVICE_URL:-https://127.0.0.1:8282}"

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

pass() {
  echo "[PASS] $*"
}

[[ -n "$OPENAVATAR_ROOT" ]] || fail "set OPENAVATAR_ROOT"
[[ -n "$DIFY_DATA_DIR" ]] || fail "set DIFY_DATA_DIR"

required_models=(
  "models/musetalk/musetalkV15/unet.pth"
  "models/musetalk/musetalkV15/musetalk.json"
  "models/musetalk/whisper/pytorch_model.bin"
  "models/face-parse-bisent/79999_iter.pth"
)

for path in "${required_models[@]}"; do
  [[ -s "$OPENAVATAR_ROOT/$path" ]] || fail "missing $path"
done
pass "model files"

required_data=(
  alias.json
  poi.json
  stations.json
  amap_subway.json
  toilets.json
  ticket_guide.json
  food_list.json
)

for name in "${required_data[@]}"; do
  [[ -s "$DIFY_DATA_DIR/$name" ]] || fail "missing data/$name"
  python3 -m json.tool "$DIFY_DATA_DIR/$name" >/dev/null
done
pass "Dify sandbox data"

curl -kfsS -o /dev/null "$SERVICE_URL/" || fail "service unavailable: $SERVICE_URL"
pass "OpenAvatarChat HTTPS"

if command -v docker >/dev/null 2>&1; then
  docker inspect openavatarchat-redis \
    --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
    2>/dev/null | grep -Eq 'healthy|running' || fail "Redis container not healthy"
  pass "Redis container"
else
  echo "[SKIP] Docker not installed"
fi

echo "Static smoke checks completed. No model conversation was executed."
