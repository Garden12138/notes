#!/usr/bin/env python3

from __future__ import annotations

import base64
import gzip
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "generated"

ARTIFACTS = {
    ROOT / "artifacts/backend/openavatarchat-guangzhou-metro.patch.gz.b64":
        OUTPUT_DIR / "openavatarchat-guangzhou-metro.patch",
    ROOT / "artifacts/dify/guangzhou-metro-scene-workflow.sanitized.yml.gz.b64":
        OUTPUT_DIR / "guangzhou-metro-scene-workflow.sanitized.yml",
    ROOT / "artifacts/dify/guangzhou-metro-interaction-workflow.sanitized.yml.gz.b64":
        OUTPUT_DIR / "guangzhou-metro-interaction-workflow.sanitized.yml",
}


def decode_artifact(source: Path, target: Path) -> None:
    encoded = "".join(source.read_text(encoding="ascii").split())
    compressed = base64.b64decode(encoded, validate=True)
    content = gzip.decompress(compressed)
    target.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    print(f"{target.relative_to(ROOT)}  sha256={digest}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for source, target in ARTIFACTS.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        decode_artifact(source, target)


if __name__ == "__main__":
    main()

