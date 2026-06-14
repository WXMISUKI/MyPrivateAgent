"""Read-only onboarding catalog for external capability providers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CONTRACT_VERSION = "provider-onboarding-catalog-v1"


@dataclass(frozen=True)
class ProviderOnboardingEnv:
    enable_var: str
    base_url_var: str
    timeout_var: str | None = None
    extra_vars: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderOnboardingEntry:
    onboarding_id: str
    provider_id: str
    kind: str
    purpose: str
    default_base_url: str
    env: ProviderOnboardingEnv
    capability_ids: tuple[str, ...]
    docs: tuple[str, ...]
    smoke_commands: tuple[str, ...]
    boundaries: dict[str, str]


class ProviderOnboardingCatalogService:
    """Build deterministic onboarding guidance for known external providers."""

    def list_entries(self) -> dict[str, Any]:
        entries = [self._entry_payload(entry, compact=True) for entry in self._entries()]
        return {
            "contract_version": CONTRACT_VERSION,
            "entries": entries,
        }

    def get_entry(self, onboarding_id: str) -> dict[str, Any]:
        entry = self._find_entry(onboarding_id)
        if entry is None:
            raise LookupError(f"Provider onboarding entry not found: {onboarding_id}")
        return {
            "contract_version": CONTRACT_VERSION,
            "entry": self._entry_payload(entry, compact=False),
        }

    def get_readiness(self, onboarding_id: str) -> dict[str, Any]:
        entry = self._find_entry(onboarding_id)
        if entry is None:
            raise LookupError(f"Provider onboarding entry not found: {onboarding_id}")
        checks = self._checks(entry)
        blocked = [check for check in checks if check["status"] == "missing"]
        configured = not blocked
        return {
            "contract_version": CONTRACT_VERSION,
            "onboarding_id": entry.onboarding_id,
            "provider_id": entry.provider_id,
            "kind": entry.kind,
            "configuration_status": "configured" if configured else "unconfigured",
            "checks": checks,
            "live_probe_hints": {
                "service_provider_detail": f"/api/service-providers/{entry.provider_id}",
                "service_provider_evidence_preview": f"/api/service-providers/{entry.provider_id}/evidence-preview",
                "capability_heartbeat": "/api/capabilities/heartbeat",
            },
            "boundaries": dict(entry.boundaries),
            "recommended_action": (
                "run_live_service_provider_probe"
                if configured
                else "configure_required_provider_environment"
            ),
        }

    def onboarding_id_for_provider(self, provider_id: str) -> str | None:
        normalized = str(provider_id or "").strip()
        for entry in self._entries():
            if entry.provider_id == normalized:
                return entry.onboarding_id
        return None

    def _entry_payload(self, entry: ProviderOnboardingEntry, *, compact: bool) -> dict[str, Any]:
        payload = {
            "onboarding_id": entry.onboarding_id,
            "provider_id": entry.provider_id,
            "kind": entry.kind,
            "purpose": entry.purpose,
            "default_base_url": entry.default_base_url,
            "capability_ids": list(entry.capability_ids),
            "env": {
                "enable_var": entry.env.enable_var,
                "base_url_var": entry.env.base_url_var,
                "timeout_var": entry.env.timeout_var,
                "extra_vars": list(entry.env.extra_vars),
            },
            "docs": list(entry.docs),
            "management": {
                "service_provider_detail": f"/api/service-providers/{entry.provider_id}",
                "service_provider_evidence_preview": f"/api/service-providers/{entry.provider_id}/evidence-preview",
            },
            "checks": self._checks(entry),
            "boundaries": dict(entry.boundaries),
        }
        if not compact:
            payload["smoke_commands"] = list(entry.smoke_commands)
            payload["non_goals"] = [
                "does_not_start_external_services",
                "does_not_write_env_or_secrets",
                "does_not_submit_provider_jobs",
                "does_not_change_default_chat_behavior",
                "does_not_promote_runtime_defaults",
            ]
        return payload

    def _checks(self, entry: ProviderOnboardingEntry) -> list[dict[str, Any]]:
        config = self._config_values(entry)
        checks = [
            {
                "id": "enable_flag",
                "env_var": entry.env.enable_var,
                "status": "present" if config["enabled"] else "missing",
                "expected": "true",
                "value_present": config["enabled"],
            },
            {
                "id": "base_url",
                "env_var": entry.env.base_url_var,
                "status": "present" if config["base_url_configured"] else "missing",
                "expected": entry.default_base_url,
                "value_present": config["base_url_configured"],
            },
            {
                "id": "runtime_probe",
                "status": "probe_required",
                "path": f"/api/service-providers/{entry.provider_id}",
                "reason": "Onboarding catalog does not perform live provider probes.",
            },
        ]
        if entry.env.timeout_var:
            checks.insert(
                2,
                {
                    "id": "timeout",
                    "env_var": entry.env.timeout_var,
                    "status": "present" if config["timeout_configured"] else "optional",
                    "value_present": config["timeout_configured"],
                },
            )
        for extra_var in entry.env.extra_vars:
            checks.append(
                {
                    "id": f"extra:{extra_var}",
                    "env_var": extra_var,
                    "status": "present" if config["extra"].get(extra_var) else "optional",
                    "value_present": bool(config["extra"].get(extra_var)),
                }
            )
        return checks

    @staticmethod
    def _config_values(entry: ProviderOnboardingEntry) -> dict[str, Any]:
        try:
            from backend import config as app_config
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            import config as app_config

        enable_value = getattr(app_config, entry.env.enable_var, False)
        base_url_value = str(getattr(app_config, entry.env.base_url_var, "") or "").strip()
        timeout_value = (
            getattr(app_config, entry.env.timeout_var, None)
            if entry.env.timeout_var
            else None
        )
        extra = {
            name: bool(str(getattr(app_config, name, "") or "").strip())
            for name in entry.env.extra_vars
        }
        return {
            "enabled": bool(enable_value),
            "base_url_configured": bool(base_url_value),
            "timeout_configured": timeout_value is not None,
            "extra": extra,
        }

    def _find_entry(self, onboarding_id: str) -> ProviderOnboardingEntry | None:
        normalized = str(onboarding_id or "").strip()
        for entry in self._entries():
            if entry.onboarding_id == normalized:
                return entry
        return None

    @staticmethod
    def _entries() -> tuple[ProviderOnboardingEntry, ...]:
        common_boundaries = {
            "default_chat_behavior": "not_changed",
            "runtime_default_promotion": "not_changed",
            "audit_or_memory_mutation": "not_performed",
            "provider_service_startup": "not_performed",
        }
        return (
            ProviderOnboardingEntry(
                onboarding_id="knowledge-rag-provider",
                provider_id="unifiedKnowledgeProvider",
                kind="knowledge",
                purpose="External lightweight RAG/knowledge provider for explicit retrieval and governed evidence use.",
                default_base_url="http://127.0.0.1:8020",
                env=ProviderOnboardingEnv(
                    enable_var="ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER",
                    base_url_var="KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL",
                    timeout_var="KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS",
                ),
                capability_ids=("knowledge.rag.retrieve", "knowledge.graph.query"),
                docs=(
                    "docs/guides/external_rag_provider_development.md",
                    "docs/integration/knowledge-provider-caller-loop/knowledge-provider-caller-loop.md",
                ),
                smoke_commands=(
                    "python backend/scripts/company_profile_explicit_api_local_smoke.py --provider-base-url http://127.0.0.1:8020",
                ),
                boundaries={
                    **common_boundaries,
                    "default_chat_grounding": "disabled",
                    "graphrag_execution": "gated",
                    "source_binding_automation": "disabled",
                },
            ),
            ProviderOnboardingEntry(
                onboarding_id="voice-asr-tts-provider",
                provider_id="unifiedTTSandASR",
                kind="voice",
                purpose="External ASR/TTS provider for speech synthesis and realtime speech recognition.",
                default_base_url="http://127.0.0.1:8010",
                env=ProviderOnboardingEnv(
                    enable_var="ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER",
                    base_url_var="VOICE_CAPABILITY_PROVIDER_BASE_URL",
                    timeout_var="VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS",
                ),
                capability_ids=("voice.tts.edge", "voice.asr.vosk"),
                docs=("docs/guides/voice_runtime_module.md",),
                smoke_commands=("GET /api/capabilities/heartbeat",),
                boundaries={**common_boundaries, "legacy_local_voice_runtime": "fallback_only"},
            ),
            ProviderOnboardingEntry(
                onboarding_id="document-ocr-provider",
                provider_id="paddleOCRProvider",
                kind="ocr",
                purpose="External OCR provider for document/image text extraction through PaddleOCR/PaddleX serving.",
                default_base_url="http://127.0.0.1:8080",
                env=ProviderOnboardingEnv(
                    enable_var="ENABLE_OCR_CAPABILITY_PROVIDER",
                    base_url_var="OCR_CAPABILITY_PROVIDER_BASE_URL",
                    timeout_var="OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS",
                ),
                capability_ids=("document.ocr.extract",),
                docs=("docs/guides/external_ocr_provider_development.md",),
                smoke_commands=("GET /api/capabilities/document.ocr.extract/health",),
                boundaries={**common_boundaries, "document_artifact_persistence": "explicit_only"},
            ),
            ProviderOnboardingEntry(
                onboarding_id="document-layout-provider",
                provider_id="paddleLayoutProvider",
                kind="layout",
                purpose="External layout provider for document structure, markdown, table, and page extraction.",
                default_base_url="http://127.0.0.1:8081",
                env=ProviderOnboardingEnv(
                    enable_var="ENABLE_LAYOUT_CAPABILITY_PROVIDER",
                    base_url_var="LAYOUT_CAPABILITY_PROVIDER_BASE_URL",
                    timeout_var="LAYOUT_CAPABILITY_PROVIDER_TIMEOUT_SECONDS",
                    extra_vars=("LAYOUT_CAPABILITY_PROVIDER_INVOKE_PATH",),
                ),
                capability_ids=("document.layout.parse",),
                docs=("docs/guides/layout_capability_debug_guide.md",),
                smoke_commands=("GET /api/capabilities/document.layout.parse/health",),
                boundaries={**common_boundaries, "document_artifact_persistence": "explicit_only"},
            ),
            ProviderOnboardingEntry(
                onboarding_id="document-vlm-provider",
                provider_id="documentVlmProvider",
                kind="vlm",
                purpose="External document VLM provider for semantic document understanding and optional async jobs.",
                default_base_url="http://127.0.0.1:8082",
                env=ProviderOnboardingEnv(
                    enable_var="ENABLE_VLM_CAPABILITY_PROVIDER",
                    base_url_var="VLM_CAPABILITY_PROVIDER_BASE_URL",
                    timeout_var="VLM_CAPABILITY_PROVIDER_TIMEOUT_SECONDS",
                    extra_vars=(
                        "VLM_CAPABILITY_PROVIDER_INVOKE_PATH",
                        "VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH",
                        "VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE",
                    ),
                ),
                capability_ids=("document.vlm.parse", "document.vlm.parse.async"),
                docs=(
                    "docs/guides/document_vlm_contract_freeze_3a.md",
                    "docs/guides/vlm_async_acceptance_report_2026-06-02.md",
                ),
                smoke_commands=("GET /api/capabilities/document.vlm.parse/health",),
                boundaries={**common_boundaries, "async_job_submission": "explicit_only"},
            ),
        )


def get_provider_onboarding_catalog_service() -> ProviderOnboardingCatalogService:
    return ProviderOnboardingCatalogService()
