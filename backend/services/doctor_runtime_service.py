"""Runtime wrapper around doctor diagnostics for UI-triggered execution."""

from __future__ import annotations

from typing import Any, Dict

try:
    from services.startup_diagnostics_service import get_startup_diagnostics_service
    from scripts.doctor import _build_capability_gap_report, _build_knowledge_runtime_report
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service
    from backend.scripts.doctor import _build_capability_gap_report, _build_knowledge_runtime_report


class DoctorRuntimeService:
    """Expose doctor diagnostics through a service boundary for API callers."""

    def run_startup_report(self) -> Dict[str, Any]:
        report = get_startup_diagnostics_service().collect_report()
        report["scope"] = "startup"
        report["exit_code"] = 0 if report.get("status") != "fail" else 1
        return report

    def run_capability_gap_report(
        self,
        *,
        limit: int = 100,
        window_days: int = 0,
        max_open_actions: int | None = None,
        max_long_blocked_actions: int | None = None,
    ) -> Dict[str, Any]:
        report = _build_capability_gap_report(
            limit=limit,
            window_days=window_days,
            max_open_actions=max_open_actions,
            max_long_blocked_actions=max_long_blocked_actions,
        )
        report["exit_code"] = 0 if report.get("gate_passed") else 2
        return report

    def run_knowledge_runtime_report(
        self,
        *,
        provider_base_url: str,
        provider_api_key: str | None = None,
        agent_id: str,
        domain: str | None,
        query: str,
        top_k: int = 3,
        timeout_seconds: float = 5,
    ) -> Dict[str, Any]:
        return _build_knowledge_runtime_report(
            provider_base_url=provider_base_url,
            provider_api_key=provider_api_key,
            agent_id=agent_id,
            domain=domain,
            query=query,
            top_k=top_k,
            timeout_seconds=timeout_seconds,
        )


_doctor_runtime_service: DoctorRuntimeService | None = None


def get_doctor_runtime_service() -> DoctorRuntimeService:
    global _doctor_runtime_service
    if _doctor_runtime_service is None:
        _doctor_runtime_service = DoctorRuntimeService()
    return _doctor_runtime_service
