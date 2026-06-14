"""Provider-neutral external service consumption read model."""

from __future__ import annotations

from typing import Any

from .contracts import CapabilityDefinition
from .provider_onboarding_catalog import get_provider_onboarding_catalog_service
from .service import CapabilityRuntimeService, get_capability_runtime_service


CONTRACT_VERSION = "provider-service-consumption-v1"
STATUS_ORDER = {
    "unreachable": 0,
    "blocked": 1,
    "unconfigured": 2,
    "disabled": 3,
    "review": 4,
    "gated": 5,
    "unknown": 6,
    "ready": 7,
}


class ProviderConsumptionService:
    """Build a compact management view over configured capability providers."""

    def __init__(self, capability_service: CapabilityRuntimeService | None = None):
        self.capability_service = capability_service or get_capability_runtime_service()

    def list_providers(self) -> dict[str, Any]:
        providers = [self._build_provider_entry(group) for group in self._provider_groups().values()]
        return {
            "contract_version": CONTRACT_VERSION,
            "providers": providers,
        }

    def get_provider(self, provider_id: str) -> dict[str, Any]:
        group = self._provider_groups().get(provider_id)
        if group is None:
            raise LookupError(f"Service provider not found: {provider_id}")
        return {
            "contract_version": CONTRACT_VERSION,
            "provider": self._build_provider_entry(group, include_health=True),
        }

    def preview_evidence(self, provider_id: str) -> dict[str, Any]:
        provider = self.get_provider(provider_id)["provider"]
        status = str(provider.get("overall_status") or "unknown")
        blockers = [
            gate
            for gate in provider.get("gates", [])
            if str(gate.get("status") or "") in {"blocked", "unreachable"}
        ]
        warnings = list(provider.get("warnings") or [])
        recommended_action = self._recommended_action(status, blockers, warnings)
        return {
            "contract_version": CONTRACT_VERSION,
            "provider_id": provider["provider_id"],
            "evidence_package": {
                "provider_identity": {
                    "provider_id": provider["provider_id"],
                    "kind": provider.get("kind"),
                    "transport": provider.get("transport"),
                    "base_url": provider.get("base_url"),
                },
                "readiness": {
                    "overall_status": status,
                    "configured": provider.get("configured"),
                    "enabled": provider.get("enabled"),
                    "reason": provider.get("reason") or "",
                },
                "capabilities": provider.get("capabilities") or [],
                "gates": provider.get("gates") or [],
                "warnings": warnings,
                "boundaries": provider.get("boundaries") or {},
                "recommended_action": recommended_action,
                "provider_reopen_gate": {
                    "allowed_triggers": [
                        "real_caller_feedback_trigger",
                        "provider_owned_gap_trigger",
                        "repeated_cross_source_failure_class_trigger",
                        "runtime_strategy_evaluation_trigger",
                    ],
                    "default_action": "continue_caller_side_governed_explicit_use",
                },
            },
        }

    def invoke_provider_capability(
        self,
        provider_id: str,
        capability_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        group = self._provider_groups().get(provider_id)
        if group is None:
            raise LookupError(f"Service provider not found: {provider_id}")
        owned_capability_ids = {capability.capability_id for capability in group["capabilities"]}
        if capability_id not in owned_capability_ids:
            return {
                "ok": False,
                "provider_id": provider_id,
                "capability_id": capability_id,
                "error": {
                    "code": "SERVICE_PROVIDER_CAPABILITY_NOT_OWNED",
                    "message": "Requested capability is not owned by this service provider.",
                    "provider_id": provider_id,
                    "owned_capability_ids": sorted(owned_capability_ids),
                },
            }
        result = self.capability_service.invoke(capability_id, payload)
        result.setdefault("provider_id", provider_id)
        result["invocation_boundary"] = {
            "explicit_only": True,
            "default_chat_grounding": "not_changed",
            "source_binding_automation": "not_changed",
            "audit_or_memory_mutation": "not_performed",
        }
        return result

    def _provider_groups(self) -> dict[str, dict[str, Any]]:
        groups: dict[str, dict[str, Any]] = {}
        for capability in self.capability_service.registry.list():
            provider_id = self._provider_id(capability)
            base_url = str(capability.metadata.get("provider_base_url") or "").strip()
            group = groups.setdefault(
                provider_id,
                {
                    "provider_id": provider_id,
                    "provider": capability.provider,
                    "kind": self._provider_kind(capability),
                    "transport": capability.transport,
                    "base_url": base_url,
                    "configured": bool(base_url) or capability.transport == "local",
                    "enabled": True,
                    "capabilities": [],
                },
            )
            group["capabilities"].append(capability)
            if not group.get("base_url") and base_url:
                group["base_url"] = base_url
                group["configured"] = True
            if group.get("transport") != capability.transport:
                group["transport"] = "mixed"
        return groups

    def _build_provider_entry(self, group: dict[str, Any], *, include_health: bool = False) -> dict[str, Any]:
        capabilities: list[dict[str, Any]] = []
        statuses: list[str] = []
        gates: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        boundaries = self._default_boundaries()
        reason = ""
        for capability in group["capabilities"]:
            health = self.capability_service.get_capability_health(capability.capability_id)
            provider_health = health.get("provider_health") if isinstance(health.get("provider_health"), dict) else {}
            readiness = provider_health.get("governance_readiness") if isinstance(provider_health.get("governance_readiness"), dict) else {}
            status = self._normalize_status(str(health.get("status") or "unknown"), readiness)
            statuses.append(status)
            if not reason:
                reason = str(health.get("reason") or readiness.get("reason") or "")
            capability_entry = {
                "capability_id": capability.capability_id,
                "kind": capability.kind,
                "transport": capability.transport,
                "status": status,
                "provider": capability.provider,
                "invocation_boundary": "explicit_only",
            }
            if include_health:
                capability_entry["health"] = self._compact_health(health)
            capabilities.append(capability_entry)
            gates.extend(self._capability_gates(capability, status, readiness))
            warnings.extend(self._capability_warnings(capability, status, readiness, provider_health))
            boundaries.update(self._readiness_boundaries(readiness))

        overall_status = self._overall_status(statuses, group)
        onboarding_id = get_provider_onboarding_catalog_service().onboarding_id_for_provider(group["provider_id"])
        entry = {
            "provider_id": group["provider_id"],
            "kind": group["kind"],
            "transport": group["transport"],
            "base_url": group.get("base_url") or "",
            "configured": bool(group.get("configured")),
            "enabled": bool(group.get("enabled")),
            "overall_status": overall_status,
            "reason": reason,
            "capabilities": capabilities,
            "gates": gates,
            "warnings": warnings,
            "boundaries": boundaries,
        }
        if onboarding_id:
            entry["onboarding_id"] = onboarding_id
            entry["onboarding_path"] = f"/api/provider-onboarding/{onboarding_id}"
        return entry

    @staticmethod
    def _provider_id(capability: CapabilityDefinition) -> str:
        return str(capability.metadata.get("external_provider") or capability.provider or "unknown_provider")

    @staticmethod
    def _provider_kind(capability: CapabilityDefinition) -> str:
        if capability.capability_id.startswith("knowledge."):
            return "knowledge"
        if capability.capability_id.startswith("voice."):
            return "voice"
        if capability.capability_id.startswith("document.ocr"):
            return "ocr"
        if capability.capability_id.startswith("document.layout"):
            return "layout"
        if capability.capability_id.startswith("document.vlm"):
            return "vlm"
        return capability.kind or "capability"

    @staticmethod
    def _normalize_status(status: str, readiness: dict[str, Any]) -> str:
        overall = str(readiness.get("overall_status") or "").strip()
        if overall == "degraded":
            return "review"
        if overall in STATUS_ORDER:
            return overall
        if status == "degraded":
            return "review"
        if status in STATUS_ORDER:
            return status
        if status == "ok":
            return "ready"
        return "unknown"

    @staticmethod
    def _overall_status(statuses: list[str], group: dict[str, Any]) -> str:
        if not group.get("enabled"):
            return "disabled"
        if not group.get("configured"):
            return "unconfigured"
        if not statuses:
            return "unknown"
        if any(status == "unreachable" for status in statuses):
            return "unreachable"
        if any(status in {"blocked", "unconfigured", "disabled"} for status in statuses):
            return next(status for status in statuses if status in {"blocked", "unconfigured", "disabled"})
        if any(status == "review" for status in statuses):
            return "review"
        if all(status == "ready" for status in statuses):
            return "ready"
        if any(status == "gated" for status in statuses):
            return "gated"
        return min(statuses, key=lambda item: STATUS_ORDER.get(item, 99))

    @staticmethod
    def _default_boundaries() -> dict[str, str]:
        return {
            "default_chat_grounding": "not_changed",
            "source_binding_automation": "not_changed",
            "graphrag_execution": "not_changed",
            "final_answer_policy": "not_changed",
            "provider_runtime_promotion": "not_changed",
        }

    @staticmethod
    def _readiness_boundaries(readiness: dict[str, Any]) -> dict[str, str]:
        raw = readiness.get("boundaries") if isinstance(readiness.get("boundaries"), dict) else {}
        mapped = {}
        for key, value in raw.items():
            normalized_key = {
                "default_chat_retrieval_injection": "default_chat_grounding",
                "answer_policy_change": "final_answer_policy",
            }.get(str(key), str(key))
            mapped[normalized_key] = str(value)
        return mapped

    @staticmethod
    def _capability_gates(
        capability: CapabilityDefinition,
        status: str,
        readiness: dict[str, Any],
    ) -> list[dict[str, Any]]:
        gates: list[dict[str, Any]] = []
        if status in {"unreachable", "blocked", "gated"}:
            gates.append(
                {
                    "capability_id": capability.capability_id,
                    "status": status,
                    "reason": str(readiness.get("reason") or "Capability is not ready for explicit invocation."),
                }
            )
        graph_gate = readiness.get("graph_query") if isinstance(readiness.get("graph_query"), dict) else None
        if graph_gate:
            gates.append(
                {
                    "capability_id": str(graph_gate.get("capability_id") or "knowledge.graph.query"),
                    "status": str(graph_gate.get("status") or "gated"),
                    "reason": str(graph_gate.get("reason") or "Graph execution remains gated."),
                }
            )
        chat_gate = readiness.get("default_chat_grounding") if isinstance(readiness.get("default_chat_grounding"), dict) else None
        if chat_gate:
            gates.append(
                {
                    "capability_id": "default_chat_grounding",
                    "status": str(chat_gate.get("status") or "gated"),
                    "reason": str(chat_gate.get("reason") or "Default chat grounding remains gated."),
                }
            )
        return gates

    @staticmethod
    def _capability_warnings(
        capability: CapabilityDefinition,
        status: str,
        readiness: dict[str, Any],
        provider_health: dict[str, Any],
    ) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        if status == "review":
            warnings.append(
                {
                    "capability_id": capability.capability_id,
                    "reason": str(readiness.get("reason") or provider_health.get("reason") or "Provider requires review."),
                }
            )
        source_catalog = readiness.get("source_catalog") if isinstance(readiness.get("source_catalog"), dict) else {}
        degraded_sources = source_catalog.get("degraded_sources") if isinstance(source_catalog, dict) else None
        if degraded_sources:
            warnings.append(
                {
                    "capability_id": capability.capability_id,
                    "reason": "Provider source catalog reports degraded sources.",
                    "degraded_sources": list(degraded_sources),
                }
            )
        return warnings

    @staticmethod
    def _compact_health(health: dict[str, Any]) -> dict[str, Any]:
        provider_health = health.get("provider_health") if isinstance(health.get("provider_health"), dict) else {}
        compact = {
            "status": health.get("status") or "unknown",
            "reason": health.get("reason") or "",
        }
        if health.get("error"):
            compact["error"] = health["error"]
        readiness = provider_health.get("governance_readiness") if isinstance(provider_health.get("governance_readiness"), dict) else None
        if readiness:
            compact["governance_readiness"] = readiness
        catalog_summary = provider_health.get("catalog_summary") if isinstance(provider_health.get("catalog_summary"), dict) else None
        if catalog_summary:
            compact["catalog_summary"] = catalog_summary
        return compact

    @staticmethod
    def _recommended_action(
        status: str,
        blockers: list[dict[str, Any]],
        warnings: list[dict[str, Any]],
    ) -> str:
        if status in {"unreachable", "blocked", "unconfigured", "disabled"} or blockers:
            return "fix_provider_configuration_or_availability_before_explicit_use"
        if status == "review" or warnings:
            return "review_provider_readiness_warnings_before_broader_use"
        if status == "ready":
            return "continue_caller_side_governed_explicit_use"
        return "inspect_provider_readiness_before_use"


def get_provider_consumption_service() -> ProviderConsumptionService:
    return ProviderConsumptionService()
