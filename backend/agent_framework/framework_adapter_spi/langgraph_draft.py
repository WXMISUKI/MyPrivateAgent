"""LangGraph draft adapter readiness implementation."""

from __future__ import annotations

from importlib.util import find_spec
import sys
from typing import Any

from .health import FrameworkAdapterHealth
from .noop import NoopFrameworkAdapter


def _is_python_package_available(package_name: str) -> bool:
    normalized_name = str(package_name or "").strip()
    if not normalized_name:
        return False
    try:
        return find_spec(normalized_name) is not None
    except Exception:
        return False


def _public_attr(name: str, default: Any) -> Any:
    for module_name in ("backend.agent_framework.framework_adapters", "agent_framework.framework_adapters"):
        module = sys.modules.get(module_name)
        if module is not None and hasattr(module, name):
            return getattr(module, name)
    return default


class LangGraphDraftAdapter(NoopFrameworkAdapter):
    """Phase D draft adapter that exposes configuration readiness before real execution is bound."""

    def __init__(self):
        super().__init__(
            adapter_id="langgraph_draft",
            framework_name="LangGraph",
            supported_run_kinds=("chat", "workflow"),
            capability_requirements=("tool_runtime", "adapter_health", "audit", "runtime_trace"),
            required_env=("LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"),
            required_packages=("langgraph",),
            detail="LangGraph draft adapter is registered as a Phase D placeholder; runtime execution is not enabled.",
        )

    def health_check(self) -> FrameworkAdapterHealth:
        endpoint = _public_attr("LANGGRAPH_RUNTIME_ENDPOINT", "")
        assistant_id = _public_attr("LANGGRAPH_ASSISTANT_ID", "")
        missing_env = tuple(
            env_name for env_name, env_value in (
                ("LANGGRAPH_RUNTIME_ENDPOINT", endpoint),
                ("LANGGRAPH_ASSISTANT_ID", assistant_id),
            )
            if not str(env_value or "").strip()
        )
        package_available = _public_attr("_is_python_package_available", _is_python_package_available)
        package_installed = bool(package_available("langgraph"))
        runtime_enabled = bool(_public_attr("ENABLE_LANGGRAPH_RUNTIME_EXECUTION", False))
        missing_packages = ("langgraph",) if not package_installed else ()

        if missing_packages:
            configuration_status = "missing_package"
            execution_block_reason = "missing required package: langgraph"
        elif missing_env:
            configuration_status = "missing_env"
            execution_block_reason = f"missing required env: {', '.join(missing_env)}"
        elif not runtime_enabled:
            configuration_status = "runtime_disabled"
            execution_block_reason = "runtime execution is not enabled"
        else:
            configuration_status = "ready"
            execution_block_reason = ""

        return FrameworkAdapterHealth(
            adapter_id=self.adapter_id,
            framework_name=self.framework_name,
            status="not_configured" if configuration_status != "ready" else "healthy",
            detail=(
                "LangGraph draft adapter is registered and ready for runtime binding."
                if configuration_status == "ready"
                else f"LangGraph draft adapter is blocked: {execution_block_reason}"
            ),
            supported_run_kinds=self.supported_run_kinds,
            capability_requirements=self.capability_requirements,
            package_installed=package_installed,
            runtime_enabled=runtime_enabled,
            execution_mode="draft_external_runtime",
            required_env=self.required_env,
            execution_block_reason=execution_block_reason,
            configuration_status=configuration_status,
            missing_env=missing_env,
            missing_packages=missing_packages,
            required_packages=self.required_packages,
        )

    def can_execute(self) -> tuple[bool, str]:
        health = self.health_check()
        if str(health.configuration_status or "").strip() != "ready":
            return False, str(health.execution_block_reason or health.detail or "").strip()
        if not bool(_public_attr("ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)):
            return False, "external pilot is not enabled"
        return True, ""
