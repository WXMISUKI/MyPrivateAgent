"""Continuation descriptor lifecycle evidence for durable recovery gates."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


CONTINUATION_DESCRIPTOR_LIFECYCLE_CONTRACT_VERSION = (
    "phase-ii-continuation-descriptor-lifecycle-governance-v1"
)
CONTINUATION_DESCRIPTOR_LIFECYCLE_STATES = [
    "created",
    "bound",
    "ready",
    "stale",
    "resolved",
    "unsafe",
]


def build_continuation_descriptor_lifecycle_contract() -> Dict[str, Any]:
    return {
        "contract_version": CONTINUATION_DESCRIPTOR_LIFECYCLE_CONTRACT_VERSION,
        "governed": True,
        "states": list(CONTINUATION_DESCRIPTOR_LIFECYCLE_STATES),
        "executes_recovery": False,
        "deserializes_callables": False,
        "unsafe_payloads_fail_closed": True,
    }


def build_continuation_descriptor_lifecycle_evidence(
    *,
    descriptors: Iterable[Mapping[str, Any]],
    fail_closed_reason: str = "",
    unsafe_descriptor_keys: Iterable[str] | None = None,
) -> Dict[str, Any]:
    descriptor_items = [dict(descriptor or {}) for descriptor in descriptors]
    states = [
        str(descriptor.get("lifecycle_state") or "").strip()
        for descriptor in descriptor_items
        if str(descriptor.get("lifecycle_state") or "").strip()
    ]
    unsafe_keys = [
        str(key).strip()
        for key in list(unsafe_descriptor_keys or [])
        if str(key or "").strip()
    ]
    return {
        "contract_version": CONTINUATION_DESCRIPTOR_LIFECYCLE_CONTRACT_VERSION,
        "governed": True,
        "allowed_states": list(CONTINUATION_DESCRIPTOR_LIFECYCLE_STATES),
        "descriptor_count": len(descriptor_items),
        "states": list(dict.fromkeys(states)),
        "all_ready": bool(descriptor_items) and all(state == "ready" for state in states),
        "unsafe_descriptor_keys": list(dict.fromkeys(unsafe_keys)),
        "fail_closed_reason": str(fail_closed_reason or "").strip(),
        "executes_recovery": False,
        "deserializes_callables": False,
    }


def classify_descriptor_state(
    *,
    binding_ids: Mapping[str, str] | None = None,
    missing_binding_ids: Iterable[str] | None = None,
    unsafe: bool = False,
    stale: bool = False,
    resolved: bool = False,
) -> str:
    if unsafe:
        return "unsafe"
    if stale:
        return "stale"
    if resolved:
        return "resolved"
    normalized_bindings = {
        str(key).strip(): str(value).strip()
        for key, value in dict(binding_ids or {}).items()
        if str(key or "").strip() and str(value or "").strip()
    }
    missing = [str(item).strip() for item in list(missing_binding_ids or []) if str(item or "").strip()]
    if not normalized_bindings:
        return "created"
    if missing:
        return "bound"
    return "ready"
