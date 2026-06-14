"""Read-only acceptance gate for external provider onboarding."""

from __future__ import annotations

from typing import Any

from .provider_consumption_service import ProviderConsumptionService, get_provider_consumption_service
from .provider_onboarding_catalog import (
    ProviderOnboardingCatalogService,
    get_provider_onboarding_catalog_service,
)


CONTRACT_VERSION = "provider-onboarding-acceptance-gate-v1"
ACCEPTED_PROVIDER_STATUSES = {"ready", "review"}
BLOCKED_PROVIDER_STATUSES = {"blocked", "unreachable", "disabled", "unconfigured"}


class ProviderOnboardingAcceptanceGate:
    """Build deterministic acceptance evidence without invoking providers."""

    def __init__(
        self,
        *,
        onboarding_catalog: ProviderOnboardingCatalogService | None = None,
        provider_consumption: ProviderConsumptionService | None = None,
    ):
        self.onboarding_catalog = onboarding_catalog or get_provider_onboarding_catalog_service()
        self.provider_consumption = provider_consumption or get_provider_consumption_service()

    def evaluate_onboarding(self, onboarding_id: str) -> dict[str, Any]:
        onboarding = self._load_onboarding(onboarding_id)
        return self._evaluate(onboarding)

    def evaluate_provider(self, provider_id: str) -> dict[str, Any]:
        onboarding_id = self.onboarding_catalog.onboarding_id_for_provider(provider_id)
        if not onboarding_id:
            return self._unknown_provider(provider_id)
        return self.evaluate_onboarding(onboarding_id)

    def _evaluate(self, onboarding: dict[str, Any]) -> dict[str, Any]:
        provider_id = str(onboarding.get("provider_id") or "")
        readiness = self.onboarding_catalog.get_readiness(str(onboarding.get("onboarding_id") or ""))
        service_provider = self._find_service_provider(provider_id)
        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        if readiness.get("configuration_status") != "configured":
            missing_checks = [
                self._compact_check(check)
                for check in readiness.get("checks") or []
                if str(check.get("status") or "") == "missing"
            ]
            blockers.append(
                {
                    "code": "ONBOARDING_CONFIGURATION_INCOMPLETE",
                    "message": "Provider onboarding configuration is not complete.",
                    "checks": missing_checks,
                }
            )

        if not service_provider:
            blockers.append(
                {
                    "code": "SERVICE_PROVIDER_NOT_REGISTERED",
                    "message": "Provider is not present in the service-provider management list.",
                    "provider_id": provider_id,
                }
            )
        else:
            provider_status = str(service_provider.get("overall_status") or "unknown")
            if provider_status in BLOCKED_PROVIDER_STATUSES:
                blockers.append(
                    {
                        "code": "SERVICE_PROVIDER_NOT_READY",
                        "message": "Provider live status blocks explicit managed use.",
                        "provider_id": provider_id,
                        "overall_status": provider_status,
                    }
                )
            elif provider_status not in ACCEPTED_PROVIDER_STATUSES:
                warnings.append(
                    {
                        "code": "SERVICE_PROVIDER_REQUIRES_REVIEW",
                        "message": "Provider live status is not fully ready.",
                        "provider_id": provider_id,
                        "overall_status": provider_status,
                    }
                )
            missing_capabilities = self._missing_capabilities(onboarding, service_provider)
            if missing_capabilities:
                blockers.append(
                    {
                        "code": "SERVICE_PROVIDER_CAPABILITY_MISMATCH",
                        "message": "Provider does not own every capability declared by onboarding.",
                        "missing_capability_ids": missing_capabilities,
                    }
                )

        decision = "accepted" if not blockers else "blocked"
        recommended_action = (
            "continue_caller_side_governed_explicit_use"
            if decision == "accepted"
            else "fix_provider_configuration_or_availability_before_explicit_use"
        )
        return {
            "contract_version": CONTRACT_VERSION,
            "decision": decision,
            "decision_scope": "explicit_managed_provider_consumption_only",
            "provider_identity": self._provider_identity(onboarding),
            "onboarding": self._onboarding_summary(onboarding, readiness),
            "service_provider": self._service_provider_summary(service_provider),
            "expected_capability_ids": list(onboarding.get("capability_ids") or []),
            "owned_capability_ids": self._owned_capability_ids(service_provider),
            "blockers": blockers,
            "warnings": warnings + self._provider_warnings(service_provider),
            "boundaries": self._boundary_summary(onboarding, readiness, service_provider),
            "recommended_action": recommended_action,
            "side_effects": {
                "provider_invocation": "not_performed",
                "capability_test": "not_performed",
                "chat_grounding": "not_changed",
                "graphrag_execution": "not_performed",
                "source_binding_automation": "not_performed",
                "configuration_write": "not_performed",
                "provider_startup": "not_performed",
                "audit_or_memory_mutation": "not_performed",
            },
        }

    def _load_onboarding(self, onboarding_id: str) -> dict[str, Any]:
        payload = self.onboarding_catalog.get_entry(onboarding_id)
        entry = payload.get("entry")
        if not isinstance(entry, dict):
            raise LookupError(f"Provider onboarding entry not found: {onboarding_id}")
        return entry

    def _find_service_provider(self, provider_id: str) -> dict[str, Any] | None:
        providers = self.provider_consumption.list_providers().get("providers") or []
        for provider in providers:
            if str(provider.get("provider_id") or "") == provider_id:
                return provider
        return None

    @staticmethod
    def _unknown_provider(provider_id: str) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "decision": "blocked",
            "decision_scope": "explicit_managed_provider_consumption_only",
            "provider_identity": {
                "provider_id": provider_id,
                "onboarding_id": "",
                "kind": "unknown",
            },
            "onboarding": {
                "configuration_status": "unknown",
                "recommended_action": "select_known_provider_onboarding_entry",
                "checks": [],
            },
            "service_provider": None,
            "expected_capability_ids": [],
            "owned_capability_ids": [],
            "blockers": [
                {
                    "code": "PROVIDER_ONBOARDING_NOT_FOUND",
                    "message": "No known onboarding entry maps to this provider id.",
                    "provider_id": provider_id,
                }
            ],
            "warnings": [],
            "boundaries": _default_acceptance_boundaries(),
            "recommended_action": "select_known_provider_onboarding_entry",
            "side_effects": _default_side_effects(),
        }

    @staticmethod
    def _provider_identity(onboarding: dict[str, Any]) -> dict[str, Any]:
        return {
            "onboarding_id": str(onboarding.get("onboarding_id") or ""),
            "provider_id": str(onboarding.get("provider_id") or ""),
            "kind": str(onboarding.get("kind") or ""),
            "default_base_url": str(onboarding.get("default_base_url") or ""),
        }

    @staticmethod
    def _onboarding_summary(onboarding: dict[str, Any], readiness: dict[str, Any]) -> dict[str, Any]:
        management = onboarding.get("management") if isinstance(onboarding.get("management"), dict) else {}
        return {
            "configuration_status": str(readiness.get("configuration_status") or "unknown"),
            "recommended_action": str(readiness.get("recommended_action") or ""),
            "checks": [
                ProviderOnboardingAcceptanceGate._compact_check(check)
                for check in readiness.get("checks") or []
            ],
            "management": {
                "service_provider_detail": str(management.get("service_provider_detail") or ""),
                "service_provider_evidence_preview": str(
                    management.get("service_provider_evidence_preview") or ""
                ),
            },
        }

    @staticmethod
    def _service_provider_summary(provider: dict[str, Any] | None) -> dict[str, Any] | None:
        if not provider:
            return None
        return {
            "provider_id": str(provider.get("provider_id") or ""),
            "kind": str(provider.get("kind") or ""),
            "transport": str(provider.get("transport") or ""),
            "base_url": str(provider.get("base_url") or ""),
            "configured": bool(provider.get("configured")),
            "enabled": bool(provider.get("enabled")),
            "overall_status": str(provider.get("overall_status") or "unknown"),
            "reason": str(provider.get("reason") or ""),
            "onboarding_id": str(provider.get("onboarding_id") or ""),
            "onboarding_path": str(provider.get("onboarding_path") or ""),
            "capabilities": [
                {
                    "capability_id": str(capability.get("capability_id") or ""),
                    "kind": str(capability.get("kind") or ""),
                    "transport": str(capability.get("transport") or ""),
                    "status": str(capability.get("status") or "unknown"),
                    "invocation_boundary": str(capability.get("invocation_boundary") or "explicit_only"),
                }
                for capability in provider.get("capabilities") or []
            ],
            "gates": [
                {
                    "capability_id": str(gate.get("capability_id") or ""),
                    "status": str(gate.get("status") or "unknown"),
                    "reason": str(gate.get("reason") or ""),
                }
                for gate in provider.get("gates") or []
            ],
        }

    @staticmethod
    def _compact_check(check: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(check.get("id") or ""),
            "status": str(check.get("status") or "unknown"),
            "env_var": str(check.get("env_var") or ""),
            "path": str(check.get("path") or ""),
            "value_present": bool(check.get("value_present")),
        }

    @staticmethod
    def _missing_capabilities(onboarding: dict[str, Any], provider: dict[str, Any] | None) -> list[str]:
        expected = {str(item) for item in onboarding.get("capability_ids") or []}
        owned = set(ProviderOnboardingAcceptanceGate._owned_capability_ids(provider))
        return sorted(expected - owned)

    @staticmethod
    def _owned_capability_ids(provider: dict[str, Any] | None) -> list[str]:
        if not provider:
            return []
        return sorted(
            str(capability.get("capability_id") or "")
            for capability in provider.get("capabilities") or []
            if str(capability.get("capability_id") or "")
        )

    @staticmethod
    def _provider_warnings(provider: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not provider:
            return []
        return [
            {
                "code": "SERVICE_PROVIDER_WARNING",
                "capability_id": str(warning.get("capability_id") or ""),
                "message": str(warning.get("reason") or warning.get("message") or ""),
            }
            for warning in provider.get("warnings") or []
        ]

    @staticmethod
    def _boundary_summary(
        onboarding: dict[str, Any],
        readiness: dict[str, Any],
        provider: dict[str, Any] | None,
    ) -> dict[str, str]:
        boundaries = _default_acceptance_boundaries()
        for source in (
            onboarding.get("boundaries"),
            readiness.get("boundaries"),
            provider.get("boundaries") if provider else None,
        ):
            if isinstance(source, dict):
                for key, value in source.items():
                    boundaries[str(key)] = str(value)
        boundaries["acceptance_scope"] = "explicit_managed_provider_consumption_only"
        boundaries["future_runtime_promotion"] = "requires_separate_gate"
        return boundaries


def _default_acceptance_boundaries() -> dict[str, str]:
    return {
        "default_chat_grounding": "not_promoted",
        "graphrag_execution": "not_promoted",
        "source_binding_automation": "not_promoted",
        "provider_service_startup": "not_performed",
        "audit_or_memory_mutation": "not_performed",
        "final_answer_policy": "not_changed",
    }


def _default_side_effects() -> dict[str, str]:
    return {
        "provider_invocation": "not_performed",
        "capability_test": "not_performed",
        "chat_grounding": "not_changed",
        "graphrag_execution": "not_performed",
        "source_binding_automation": "not_performed",
        "configuration_write": "not_performed",
        "provider_startup": "not_performed",
        "audit_or_memory_mutation": "not_performed",
    }


def get_provider_onboarding_acceptance_gate() -> ProviderOnboardingAcceptanceGate:
    return ProviderOnboardingAcceptanceGate()
