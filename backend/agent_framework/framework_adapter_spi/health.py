"""Health contract for external framework adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Sequence


@dataclass(frozen=True)
class FrameworkAdapterHealth:
    """Governance-facing health snapshot for an external framework adapter."""

    adapter_id: str
    framework_name: str
    status: str = "not_configured"
    detail: str = ""
    display_name: str = ""
    adapter_type: str = "agent_framework"
    supported_run_kinds: Sequence[str] = field(default_factory=tuple)
    capability_requirements: Sequence[str] = field(default_factory=tuple)
    package_installed: bool = False
    runtime_enabled: bool = False
    execution_mode: str = "placeholder"
    required_env: Sequence[str] = field(default_factory=tuple)
    execution_block_reason: str = ""
    configuration_status: str = "not_configured"
    missing_env: Sequence[str] = field(default_factory=tuple)
    missing_packages: Sequence[str] = field(default_factory=tuple)
    required_packages: Sequence[str] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "display_name": self.display_name or self.framework_name or self.adapter_id,
            "framework_name": self.framework_name,
            "adapter_type": self.adapter_type,
            "status": self.status,
            "detail": self.detail,
            "supported_run_kinds": list(self.supported_run_kinds),
            "capability_requirements": list(self.capability_requirements),
            "package_installed": self.package_installed,
            "runtime_enabled": self.runtime_enabled,
            "execution_mode": self.execution_mode,
            "required_env": list(self.required_env),
            "execution_block_reason": self.execution_block_reason,
            "configuration_status": self.configuration_status,
            "missing_env": list(self.missing_env),
            "missing_packages": list(self.missing_packages),
            "required_packages": list(self.required_packages),
        }
