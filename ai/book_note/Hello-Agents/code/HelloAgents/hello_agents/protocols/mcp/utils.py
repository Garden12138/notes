"""Small helpers for constructing and validating MCP-facing context data."""

from __future__ import annotations

import json
from typing import Any, Dict, List


def create_context(
    messages: List[Dict[str, Any]] | None = None,
    tools: List[Dict[str, Any]] | None = None,
    resources: List[Dict[str, Any]] | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Create a predictable context dictionary for an MCP-backed Agent."""
    return {
        "messages": list(messages or ()),
        "tools": list(tools or ()),
        "resources": list(resources or ()),
        "metadata": dict(metadata or {}),
    }


def parse_context(payload: str | Dict[str, Any]) -> Dict[str, Any]:
    """Parse JSON or a dictionary and validate its collection fields."""
    if isinstance(payload, str):
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(f"无效的 JSON 上下文: {exc}") from exc
    elif isinstance(payload, dict):
        value = dict(payload)
    else:
        raise ValueError("上下文必须是字典或 JSON 对象")

    if not isinstance(value, dict):
        raise ValueError("上下文必须是字典或 JSON 对象")
    for field in ("messages", "tools", "resources"):
        current = value.setdefault(field, [])
        if not isinstance(current, list):
            raise ValueError(f"上下文字段 {field} 必须是列表")
    metadata = value.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("上下文字段 metadata 必须是字典")
    return value


def create_error_response(
    error_message: str,
    error_code: str = "UNKNOWN_ERROR",
    details: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a serializable error envelope for application adapters."""
    error: Dict[str, Any] = {
        "message": error_message,
        "code": error_code,
    }
    if details:
        error["details"] = dict(details)
    return {"success": False, "error": error}


def create_success_response(
    data: Any,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a serializable success envelope for application adapters."""
    response: Dict[str, Any] = {"success": True, "data": data}
    if metadata:
        response["metadata"] = dict(metadata)
    return response


__all__ = [
    "create_context",
    "create_error_response",
    "create_success_response",
    "parse_context",
]
