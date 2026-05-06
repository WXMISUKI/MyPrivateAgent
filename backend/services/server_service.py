"""Reusable HTTP/SSE helpers for server-layer adapters."""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import HTTPException, status


def build_sse_event(payload: Dict[str, Any] | str) -> str:
    """Encode a payload as an SSE event chunk."""
    if isinstance(payload, str):
        return f"data: {payload}\n\n"
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def build_error_event(message: str, **extra: Any) -> str:
    """Build a standard SSE error event."""
    payload = {"type": "error", "error": message}
    payload.update(extra)
    return build_sse_event(payload)


def ensure_exists(resource: Any, detail: str = "资源不存在") -> Any:
    """Return the resource or raise a standard 404 error."""
    if resource is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
    return resource


def success_response(message: str, **extra: Any) -> Dict[str, Any]:
    """Build a conventional success response payload."""
    payload = {"success": True, "message": message}
    payload.update(extra)
    return payload


def permission_request_to_dict(request: Any, *, include_result: bool = False) -> Dict[str, Any]:
    """Serialize a permission request into an API-friendly payload."""
    payload = {
        "id": request.id,
        "tool_name": request.tool_name,
        "tool_args": request.tool_args,
        "permission_level": request.permission_level,
        "conversation_id": request.conversation_id,
        "plan_id": getattr(request, "plan_id", None),
        "plan_item_id": getattr(request, "plan_item_id", None),
        "run_id": getattr(request, "run_id", None),
        "parent_run_id": getattr(request, "parent_run_id", None),
        "child_run_id": getattr(request, "child_run_id", None),
        "scheduler_run_id": getattr(request, "scheduler_run_id", None),
        "run_kind": getattr(request, "run_kind", None),
        "runtime_scope": {
            "plan_id": getattr(request, "plan_id", None),
            "plan_item_id": getattr(request, "plan_item_id", None),
            "run_id": getattr(request, "run_id", None),
            "parent_run_id": getattr(request, "parent_run_id", None),
            "child_run_id": getattr(request, "child_run_id", None),
            "scheduler_run_id": getattr(request, "scheduler_run_id", None),
            "run_kind": getattr(request, "run_kind", None),
        },
        "request_metadata": dict(getattr(request, "request_metadata", {}) or {}),
        "status": request.status.value if hasattr(request.status, "value") else str(request.status),
        "created_at": request.created_at.isoformat() if hasattr(request.created_at, "isoformat") else str(request.created_at),
    }
    if include_result:
        payload["result"] = request.result
    return payload
