"""Reusable tool-result cache for deterministic runtime tools."""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, Optional


class ToolResultCache:
    """Short-lived in-memory cache keyed by tool name and normalized arguments."""

    def __init__(self) -> None:
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, tool_name: str, tool_args: Dict[str, Any]) -> Optional[str]:
        """Return a cached result when the entry exists and is still fresh."""
        cache_key = self._build_key(tool_name, tool_args)
        now = time.monotonic()

        with self._lock:
            cached = self._entries.get(cache_key)
            if not cached:
                return None
            if cached["expires_at"] <= now:
                self._entries.pop(cache_key, None)
                return None
            return str(cached["result"])

    def set(self, tool_name: str, tool_args: Dict[str, Any], result: str, ttl_seconds: float) -> None:
        """Store a tool result under a normalized cache key."""
        if ttl_seconds <= 0:
            return

        cache_key = self._build_key(tool_name, tool_args)
        with self._lock:
            self._entries[cache_key] = {
                "result": str(result),
                "expires_at": time.monotonic() + ttl_seconds,
            }

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._entries.clear()

    def _build_key(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        serialized_args = json.dumps(tool_args or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"{tool_name}:{serialized_args}"


_tool_result_cache = ToolResultCache()


def get_tool_result_cache() -> ToolResultCache:
    """Return the process-global tool result cache."""
    return _tool_result_cache
