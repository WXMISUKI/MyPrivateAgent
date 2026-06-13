"""Deterministic grounded-answer package dry-run service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from backend.services.domain_agent_grounded_answer_trial_service import (
    DomainAgentGroundedAnswerTrialService,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


PACKAGE_DRY_RUN_CONTRACT_VERSION = "domain-agent-grounded-answer-package-dry-run-v1"


@dataclass(frozen=True)
class GroundedAnswerPackageDryRun:
    contract_version: str
    agent_id: str | None
    package_status: str
    reason_code: str
    query: str | None
    domain: str | None
    allowed_citations: list[str] = field(default_factory=list)
    evidence_items: list[dict[str, Any]] = field(default_factory=list)
    prompt_binding: dict[str, Any] = field(default_factory=dict)
    memory_boundary: dict[str, Any] = field(default_factory=dict)
    fallback_policy: str | None = None
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    provider_readiness: dict[str, Any] = field(default_factory=dict)
    boundary: dict[str, Any] = field(default_factory=dict)
    trial_report: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DomainAgentGroundedAnswerPackageService:
    """Prepare a future grounded-answer input package without invoking models."""

    def __init__(
        self,
        *,
        trial_service: DomainAgentGroundedAnswerTrialService | None = None,
        registry_service: DomainAgentRegistryService | None = None,
    ):
        self.trial_service = trial_service or DomainAgentGroundedAnswerTrialService(registry_service=registry_service)

    def build_package(
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
    ) -> GroundedAnswerPackageDryRun:
        trial = dict(trial_report or {})
        if not trial:
            trial = self.trial_service.run_trial(
                agent_id=agent_id,
                domain=domain,
                query=query,
                evidence_pack=evidence_pack,
                provider_evidence=provider_evidence,
                promptops_evidence=promptops_evidence,
                memoryops_evidence=memoryops_evidence,
                eval_evidence=eval_evidence,
                graph_requested=graph_requested,
            ).to_dict()

        package_status = self._package_status(trial.get("trial_status"))
        grounding = trial.get("grounding_decision") if isinstance(trial.get("grounding_decision"), dict) else {}
        evidence_summary = trial.get("evidence_summary") if isinstance(trial.get("evidence_summary"), dict) else {}
        prompt_summary = evidence_summary.get("promptops") if isinstance(evidence_summary.get("promptops"), dict) else {}
        memory_summary = evidence_summary.get("memoryops") if isinstance(evidence_summary.get("memoryops"), dict) else {}
        provider_readiness = trial.get("provider_readiness") if isinstance(trial.get("provider_readiness"), dict) else {}
        citations = [str(item).strip() for item in (trial.get("citation_allowlist") or []) if str(item).strip()]

        return GroundedAnswerPackageDryRun(
            contract_version=PACKAGE_DRY_RUN_CONTRACT_VERSION,
            agent_id=_clean(agent_id) or _clean(trial.get("agent_id")) or None,
            package_status=package_status,
            reason_code=self._reason_code(package_status, trial),
            query=_clean(query) or self._extract_query(trial) or None,
            domain=_clean(domain) or self._extract_domain(trial) or None,
            allowed_citations=citations,
            evidence_items=[{"source_type": "citation", "citation": citation} for citation in citations],
            prompt_binding={
                "prompt_key": prompt_summary.get("prompt_key"),
                "version": prompt_summary.get("version"),
                "status": prompt_summary.get("status"),
            },
            memory_boundary={
                "retrieved_knowledge_promotion_mode": memory_summary.get("retrieved_knowledge_promotion_mode"),
                "stored_as_memory_by_default": False,
            },
            fallback_policy=grounding.get("fallback_policy"),
            blockers=list(trial.get("blockers") or []),
            warnings=list(trial.get("warnings") or []),
            provider_readiness=dict(provider_readiness),
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
            trial_report=trial,
        )

    @staticmethod
    def _package_status(trial_status: Any) -> str:
        normalized = _clean(trial_status).lower()
        if normalized == "go":
            return "ready"
        if normalized == "review":
            return "review"
        return "blocked"

    @staticmethod
    def _reason_code(package_status: str, trial: Mapping[str, Any]) -> str:
        if package_status == "ready":
            return "grounded_answer_package_ready"
        if package_status == "review":
            return "grounded_answer_package_review_required"
        return _clean(trial.get("reason_code")) or "grounded_answer_package_blocked"

    @staticmethod
    def _extract_query(trial: Mapping[str, Any]) -> str:
        request_summary = trial.get("request_summary") if isinstance(trial.get("request_summary"), dict) else {}
        query = request_summary.get("query")
        return _clean(query)

    @staticmethod
    def _extract_domain(trial: Mapping[str, Any]) -> str:
        request_summary = trial.get("request_summary") if isinstance(trial.get("request_summary"), dict) else {}
        return _clean(request_summary.get("domain"))


def build_grounded_answer_package_dry_run(
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
    registry_service: DomainAgentRegistryService | None = None,
) -> dict[str, Any]:
    return DomainAgentGroundedAnswerPackageService(registry_service=registry_service).build_package(
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


_grounded_answer_package_service: DomainAgentGroundedAnswerPackageService | None = None


def get_domain_agent_grounded_answer_package_service() -> DomainAgentGroundedAnswerPackageService:
    global _grounded_answer_package_service
    if _grounded_answer_package_service is None:
        _grounded_answer_package_service = DomainAgentGroundedAnswerPackageService()
    return _grounded_answer_package_service


def _clean(value: Any) -> str:
    return str(value or "").strip()
