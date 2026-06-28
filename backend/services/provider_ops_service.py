"""Read-only provider operations control plane."""

from __future__ import annotations

from typing import Any

try:
    from services.provider_config_service import ProviderConfigService, get_provider_config_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.provider_config_service import ProviderConfigService, get_provider_config_service


CONTRACT_VERSION = "provider-ops-control-plane-v1"


class ProviderOpsService:
    """Build a compact operations view over configured providers."""

    def __init__(self, provider_config_service: ProviderConfigService | None = None):
        self.provider_config_service = provider_config_service or get_provider_config_service()

    def list_provider_ops(self) -> dict[str, Any]:
        providers = [self._build_provider_entry(provider) for provider in self.provider_config_service.list_providers()]
        summary = self._build_summary(providers)
        return {
            "contract_version": CONTRACT_VERSION,
            "summary": summary,
            "providers": providers,
        }

    def _build_provider_entry(self, provider: dict[str, Any]) -> dict[str, Any]:
        configured = bool(provider.get("configured"))
        requires_api_key = bool(provider.get("requires_api_key"))
        config_source = str(provider.get("config_source") or "unknown").strip() or "unknown"

        credential_posture = "configured" if configured else "unconfigured"
        if not requires_api_key and configured:
            credential_posture = "not_required"

        quota_posture = "unknown"
        rate_limit_posture = "unknown"
        cost_posture = "unknown"
        sla_posture = "unknown"

        overall_status = self._overall_status(
            credential_posture=credential_posture,
            quota_posture=quota_posture,
            rate_limit_posture=rate_limit_posture,
            cost_posture=cost_posture,
            sla_posture=sla_posture,
        )

        reason = self._reason(
            credential_posture=credential_posture,
            config_source=config_source,
            overall_status=overall_status,
        )
        next_action = self._next_action(overall_status=overall_status, credential_posture=credential_posture)

        return {
            "provider_id": provider.get("name") or "",
            "display_name": provider.get("display_name") or provider.get("name") or "",
            "configured": configured,
            "enabled": True,
            "overall_status": overall_status,
            "reason": reason,
            "next_action": next_action,
            "config_source": config_source,
            "credential_posture": credential_posture,
            "quota_posture": quota_posture,
            "rate_limit_posture": rate_limit_posture,
            "cost_posture": cost_posture,
            "sla_posture": sla_posture,
            "fallback_posture": "ready" if configured else "blocked",
            "requires_api_key": requires_api_key,
            "api_key_masked": provider.get("api_key_masked"),
            "base_url": provider.get("base_url") or "",
            "model_name": provider.get("model_name") or "",
        }

    @staticmethod
    def _overall_status(
        *,
        credential_posture: str,
        quota_posture: str,
        rate_limit_posture: str,
        cost_posture: str,
        sla_posture: str,
    ) -> str:
        if credential_posture == "unconfigured":
            return "unconfigured"
        if any(posture == "blocked" for posture in (quota_posture, rate_limit_posture, cost_posture, sla_posture)):
            return "blocked"
        if any(posture in {"unknown", "review"} for posture in (quota_posture, rate_limit_posture, cost_posture, sla_posture)):
            return "review"
        return "ready"

    @staticmethod
    def _reason(*, credential_posture: str, config_source: str, overall_status: str) -> str:
        if credential_posture == "unconfigured":
            return f"provider_configuration_missing:{config_source}"
        if overall_status == "review":
            return "operational_limits_not_declared"
        if overall_status == "blocked":
            return "operational_posture_blocked"
        return "operational_posture_ready"

    @staticmethod
    def _next_action(*, overall_status: str, credential_posture: str) -> str:
        if credential_posture == "unconfigured":
            return "configure_provider_credentials_before_use"
        if overall_status == "review":
            return "review_provider_operational_limits_before_broader_use"
        if overall_status == "blocked":
            return "resolve_provider_ops_blockers_before_use"
        return "continue_governed_explicit_use"

    @staticmethod
    def _build_summary(providers: list[dict[str, Any]]) -> dict[str, int]:
        summary = {"total": 0, "ready": 0, "review": 0, "blocked": 0, "unconfigured": 0}
        for provider in providers:
            summary["total"] += 1
            status = str(provider.get("overall_status") or "unknown")
            if status in summary:
                summary[status] += 1
        return summary


_provider_ops_service: ProviderOpsService | None = None


def get_provider_ops_service() -> ProviderOpsService:
    global _provider_ops_service
    if _provider_ops_service is None:
        _provider_ops_service = ProviderOpsService()
    return _provider_ops_service
