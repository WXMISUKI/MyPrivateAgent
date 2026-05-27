"""Provider-neutral capability runtime contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


CONTRACT_VERSION = "capability-runtime-v1"

CapabilityInvoker = Callable[[dict[str, Any]], Any]
CapabilityHealthChecker = Callable[[], dict[str, Any]]
CapabilityHeartbeatChecker = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class CapabilityDefinition:
    capability_id: str
    kind: str
    transport: str
    provider: str
    title: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    endpoint: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    invoker: CapabilityInvoker | None = field(default=None, repr=False, compare=False)
    health_checker: CapabilityHealthChecker | None = field(default=None, repr=False, compare=False)
    heartbeat_checker: CapabilityHeartbeatChecker | None = field(default=None, repr=False, compare=False)

    def to_contract(self, *, status: str = "unknown", reason: str = "") -> dict[str, Any]:
        payload = {
            "capability_id": self.capability_id,
            "kind": self.kind,
            "transport": self.transport,
            "provider": self.provider,
            "title": self.title,
            "description": self.description,
            "status": status,
            "reason": reason,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "metadata": self.metadata,
        }
        if self.endpoint:
            payload["endpoint"] = self.endpoint
        return payload
