"""Continuation registry seam for reattaching executable continuations."""

from __future__ import annotations

from typing import Any, Dict, Protocol


class EmbeddedContinuationRegistry(Protocol):
    def identify(self, handler: Any) -> str | None:
        ...

    def resolve(self, binding_id: str) -> Any | None:
        ...

    def build_catalog(self) -> Dict[str, Any]:
        ...


class InMemoryEmbeddedContinuationRegistry:
    """Simple binding registry for controlled continuation reattachment."""

    def __init__(self, bindings: Dict[str, Any] | None = None):
        self._bindings: Dict[str, Any] = {}
        self._reverse_bindings: Dict[int, str] = {}
        self._binding_metadata: Dict[str, Dict[str, Any]] = {}
        for binding_id, handler in dict(bindings or {}).items():
            self.register(binding_id, handler)

    def register(
        self,
        binding_id: str,
        handler: Any,
        *,
        binding_kind: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        normalized_binding_id = str(binding_id or "").strip()
        if not normalized_binding_id:
            raise ValueError("binding_id is required.")
        self._bindings[normalized_binding_id] = handler
        self._reverse_bindings[id(handler)] = normalized_binding_id
        handler_name = getattr(handler, "__name__", None) or handler.__class__.__name__
        self._binding_metadata[normalized_binding_id] = {
            "binding_id": normalized_binding_id,
            "binding_kind": str(binding_kind or "generic").strip() or "generic",
            "handler_name": str(handler_name or "unknown_handler").strip() or "unknown_handler",
            "metadata": dict(metadata or {}),
        }

    def identify(self, handler: Any) -> str | None:
        if handler is None:
            return None
        return self._reverse_bindings.get(id(handler))

    def resolve(self, binding_id: str) -> Any | None:
        normalized_binding_id = str(binding_id or "").strip()
        if not normalized_binding_id:
            return None
        return self._bindings.get(normalized_binding_id)

    def build_catalog(self) -> Dict[str, Any]:
        entries = [
            {
                "binding_id": item["binding_id"],
                "binding_kind": item["binding_kind"],
                "handler_name": item["handler_name"],
                "metadata": dict(item.get("metadata") or {}),
            }
            for item in self._binding_metadata.values()
        ]
        entries.sort(key=lambda item: (item["binding_kind"], item["binding_id"]))
        return {
            "registry_type": self.__class__.__name__,
            "total_bindings": len(entries),
            "bindings": entries,
        }


_embedded_continuation_registry_singleton: InMemoryEmbeddedContinuationRegistry | None = None


def get_embedded_continuation_registry() -> InMemoryEmbeddedContinuationRegistry:
    global _embedded_continuation_registry_singleton
    if _embedded_continuation_registry_singleton is None:
        _embedded_continuation_registry_singleton = InMemoryEmbeddedContinuationRegistry()
    return _embedded_continuation_registry_singleton
