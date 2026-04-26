"""Reusable HTTP/SSE helpers for the server package."""

from __future__ import annotations

try:
    from services.server_service import (
        build_error_event,
        build_sse_event,
        ensure_exists,
        permission_request_to_dict,
        success_response,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.server_service import (
        build_error_event,
        build_sse_event,
        ensure_exists,
        permission_request_to_dict,
        success_response,
    )

__all__ = [
    "build_error_event",
    "build_sse_event",
    "ensure_exists",
    "permission_request_to_dict",
    "success_response",
]
