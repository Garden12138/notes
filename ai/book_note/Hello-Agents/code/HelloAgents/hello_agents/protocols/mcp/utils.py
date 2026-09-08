"""Context serialization helpers reserved by the chapter architecture."""

from __future__ import annotations

import json
from typing import Any, Dict


def create_context(**values: Any) -> str:
    """Serialize shared context to deterministic JSON text."""
    return json.dumps(values, ensure_ascii=False, sort_keys=True)


def parse_context(payload: str) -> Dict[str, Any]:
    """Parse context JSON and require an object at the top level."""
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError("上下文必须是 JSON 对象")
    return value
