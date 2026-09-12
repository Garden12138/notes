"""Small SSE serialization helpers shared by the API and tests."""

from __future__ import annotations

import json

try:
    from .models import ResearchEvent
except ImportError:  # Support direct execution through ``src/main.py``.
    from models import ResearchEvent  # type: ignore[no-redef]


def encode_sse(event: ResearchEvent) -> str:
    """Serialize one research event as an SSE data frame."""
    payload = event.model_dump(mode="json", exclude_none=True)
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
