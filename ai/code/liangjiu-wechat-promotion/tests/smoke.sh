#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPTS="$ROOT/iphone-use/scripts"
FIXTURES="$ROOT/tests/fixtures"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

for script in "$SCRIPTS"/*.sh; do
  bash -n "$script"
done

export PYTHONPYCACHEPREFIX="$TMP_DIR/pycache"
python3 -m py_compile \
  "$SCRIPTS/iu_clipboard_relay.py" \
  "$SCRIPTS/select_safe_products.py" \
  "$SCRIPTS/build_verified_promotion.py"

python3 "$SCRIPTS/select_safe_products.py" \
  --input "$FIXTURES/products.jsonl" \
  --count 6 \
  --output "$TMP_DIR/selected-products.txt" \
  --report "$TMP_DIR/selection.json" >/dev/null

python3 "$SCRIPTS/build_verified_promotion.py" \
  --results "$FIXTURES/results.jsonl" \
  --expected-count 2 \
  --time 12:00 \
  --output "$TMP_DIR/final-promotion.txt" \
  --report "$TMP_DIR/final-promotion.report.json" >/dev/null

python3 - "$ROOT" "$TMP_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])

selection = json.loads((tmp / "selection.json").read_text(encoding="utf-8"))
assert selection["ok"] is True
assert selection["selected_category"] == "小家电"
assert selection["selected_count"] == 6
assert len((tmp / "selected-products.txt").read_text(encoding="utf-8").splitlines()) == 6

report = json.loads(
    (tmp / "final-promotion.report.json").read_text(encoding="utf-8")
)
copy = (tmp / "final-promotion.txt").read_text(encoding="utf-8")
assert report["ok"] is True
assert report["verified_count"] == 2
assert copy.count("#小程序://") == 2
assert "现货" not in copy and "早拍早发" not in copy

for skill in (root / "openclaw/skills").glob("*/SKILL.md"):
    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    frontmatter = text.split("---", 2)[1]
    keys = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if ":" in line
    }
    assert keys == {"name", "description"}, (skill, keys)
PY

printf '%s\n' "smoke test passed"

