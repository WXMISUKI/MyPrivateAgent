"""Deterministic grounded-answer composition trial service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from backend.services.domain_agent_grounded_answer_package_service import (
    DomainAgentGroundedAnswerPackageService,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


COMPOSITION_TRIAL_CONTRACT_VERSION = "domain-agent-grounded-answer-composition-trial-v1"


@dataclass(frozen=True)
class GroundedAnswerCompositionTrial:
    contract_version: str
    agent_id: str | None
    composition_status: str
    reason_code: str
    answer_preview: str | None
    used_citations: list[str] = field(default_factory=list)
    composition_policy: dict[str, Any] = field(default_factory=dict)
    fallback_behavior: dict[str, Any] = field(default_factory=dict)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    boundary: dict[str, Any] = field(default_factory=dict)
    package: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DomainAgentGroundedAnswerCompositionTrialService:
    """Build a deterministic answer preview from a ready grounded-answer package."""

    def __init__(
        self,
        *,
        package_service: DomainAgentGroundedAnswerPackageService | None = None,
        registry_service: DomainAgentRegistryService | None = None,
    ):
        self.package_service = package_service or DomainAgentGroundedAnswerPackageService(
            registry_service=registry_service,
        )

    def run_trial(
        self,
        *,
        agent_id: str | None,
        domain: str | None = None,
        query: str | None = None,
        evidence_pack: Mapping[str, Any] | None = None,
        provider_evidence: Mapping[str, Any] | None = None,
        promptops_evidence: Mapping[str, Any] | None = None,
        memoryops_evidence: Mapping[str, Any] | None = None,
        eval_evidence: Mapping[str, Any] | None = None,
        graph_requested: bool = False,
        trial_report: Mapping[str, Any] | None = None,
        package: Mapping[str, Any] | None = None,
    ) -> GroundedAnswerCompositionTrial:
        current_package = dict(package or {})
        if not current_package:
            current_package = self.package_service.build_package(
                agent_id=agent_id,
                domain=domain,
                query=query,
                evidence_pack=evidence_pack,
                provider_evidence=provider_evidence,
                promptops_evidence=promptops_evidence,
                memoryops_evidence=memoryops_evidence,
                eval_evidence=eval_evidence,
                graph_requested=graph_requested,
                trial_report=trial_report,
            ).to_dict()

        composition_status = self._composition_status(current_package.get("package_status"))
        answer_preview = self._build_preview(current_package) if composition_status == "ready" else None
        citations = [str(item).strip() for item in (current_package.get("allowed_citations") or []) if str(item).strip()]

        return GroundedAnswerCompositionTrial(
            contract_version=COMPOSITION_TRIAL_CONTRACT_VERSION,
            agent_id=_clean(agent_id) or _clean(current_package.get("agent_id")) or None,
            composition_status=composition_status,
            reason_code=self._reason_code(composition_status, current_package),
            answer_preview=answer_preview,
            used_citations=citations if composition_status == "ready" else [],
            composition_policy={
                "mode": "deterministic_preview",
                "citation_mode": "allowlist_only",
                "fallback_policy": current_package.get("fallback_policy"),
            },
            fallback_behavior={
                "when_blocked": current_package.get("fallback_policy"),
            },
            blockers=list(current_package.get("blockers") or []),
            warnings=list(current_package.get("warnings") or []),
            boundary={
                "provider_invocation": "not_performed",
                "model_invocation": "not_performed",
                "answer_generation": "not_performed",
                "chat_invocation": "not_performed",
                "source_binding_creation": "not_performed",
                "memory_write": "not_performed",
                "audit_write": "not_performed",
                "trace_write": "not_performed",
                "runtime_behavior_changed": False,
            },
            package=current_package,
        )

    @staticmethod
    def _composition_status(package_status: Any) -> str:
        normalized = _clean(package_status).lower()
        if normalized == "ready":
            return "ready"
        if normalized == "review":
            return "review"
        return "blocked"

    @staticmethod
    def _reason_code(composition_status: str, current_package: Mapping[str, Any]) -> str:
        if composition_status == "ready":
            return "grounded_answer_composition_ready"
        if composition_status == "review":
            return "grounded_answer_composition_review_required"
        return _clean(current_package.get("reason_code")) or "grounded_answer_composition_blocked"

    @staticmethod
    def _build_preview(current_package: Mapping[str, Any]) -> str:
        citations = [str(item).strip() for item in (current_package.get("allowed_citations") or []) if str(item).strip()]
        query = _clean(current_package.get("query"))
        domain = _clean(current_package.get("domain"))
        citation_text = ", ".join(citations) if citations else "无可用引用"
        if query and domain:
            return f"基于 {citation_text}，已为 `{domain}` 生成受控回答预览：{query}"
        if query:
            return f"基于 {citation_text}，已生成受控回答预览：{query}"
        return f"基于 {citation_text}，已生成受控 grounded answer preview。"


def build_grounded_answer_composition_trial(
    *,
    agent_id: str | None,
    domain: str | None = None,
    query: str | None = None,
    evidence_pack: Mapping[str, Any] | None = None,
    provider_evidence: Mapping[str, Any] | None = None,
    promptops_evidence: Mapping[str, Any] | None = None,
    memoryops_evidence: Mapping[str, Any] | None = None,
    eval_evidence: Mapping[str, Any] | None = None,
    graph_requested: bool = False,
    trial_report: Mapping[str, Any] | None = None,
    package: Mapping[str, Any] | None = None,
    registry_service: DomainAgentRegistryService | None = None,
) -> dict[str, Any]:
    return DomainAgentGroundedAnswerCompositionTrialService(
        registry_service=registry_service,
    ).run_trial(
        agent_id=agent_id,
        domain=domain,
        query=query,
        evidence_pack=evidence_pack,
        provider_evidence=provider_evidence,
        promptops_evidence=promptops_evidence,
        memoryops_evidence=memoryops_evidence,
        eval_evidence=eval_evidence,
        graph_requested=graph_requested,
        trial_report=trial_report,
        package=package,
    ).to_dict()


_composition_trial_service: DomainAgentGroundedAnswerCompositionTrialService | None = None


def get_domain_agent_grounded_answer_composition_trial_service() -> DomainAgentGroundedAnswerCompositionTrialService:
    global _composition_trial_service
    if _composition_trial_service is None:
        _composition_trial_service = DomainAgentGroundedAnswerCompositionTrialService()
    return _composition_trial_service


def _clean(value: Any) -> str:
    return str(value or "").strip()
