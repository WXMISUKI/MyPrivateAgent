"""Explicit opt-in trial reports for domain-agent grounded answer readiness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from backend.services.agent_grounding_policy_service import (
    AgentGroundingPolicyService,
    DEFAULT_CHAT_RETRIEVAL_INJECTION,
)
from backend.services.domain_agent_grounded_answer_promotion_service import (
    DomainAgentGroundedAnswerPromotionService,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


TRIAL_SURFACE_CONTRACT_VERSION = "domain-agent-grounded-answer-trial-surface-v1"


@dataclass(frozen=True)
class DomainAgentGroundedAnswerTrialReport:
    contract_version: str
    agent_id: str | None
    trial_status: str
    reason_code: str
    recommended_next_action: str
    grounding_decision: dict[str, Any] = field(default_factory=dict)
    promotion_decision: dict[str, Any] = field(default_factory=dict)
    citation_allowlist: list[str] = field(default_factory=list)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    evidence_summary: dict[str, Any] = field(default_factory=dict)
    provider_readiness: dict[str, Any] = field(default_factory=dict)
    boundary: dict[str, Any] = field(default_factory=dict)
    request_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DomainAgentGroundedAnswerTrialService:
    """Build trial reports without invoking chat, providers, or persistence."""

    def __init__(
        self,
        *,
        grounding_service: AgentGroundingPolicyService | None = None,
        promotion_service: DomainAgentGroundedAnswerPromotionService | None = None,
        registry_service: DomainAgentRegistryService | None = None,
    ):
        self.registry_service = registry_service
        self.grounding_service = grounding_service or AgentGroundingPolicyService(registry_service)
        self.promotion_service = promotion_service or DomainAgentGroundedAnswerPromotionService(
            registry_service=registry_service,
            grounding_service=self.grounding_service,
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
    ) -> DomainAgentGroundedAnswerTrialReport:
        grounding = self.grounding_service.decide(
            agent_id=_clean(agent_id) or None,
            domain=domain,
            evidence_pack=evidence_pack,
            graph_requested=graph_requested,
        ).to_dict()
        promotion = self.promotion_service.evaluate(
            agent_id=_clean(agent_id) or None,
            domain=domain,
            provider_evidence=provider_evidence,
            grounding_decision=grounding,
            evidence_pack=evidence_pack,
            promptops_evidence=promptops_evidence,
            memoryops_evidence=memoryops_evidence,
            eval_evidence=eval_evidence,
            graph_requested=graph_requested,
        ).to_dict()

        trial_status = self._trial_status(grounding, promotion)
        blockers = list(promotion.get("blockers") or [])
        warnings = list(promotion.get("warnings") or [])
        if grounding.get("decision") == "review" and not any(item.get("component") == "grounding" for item in warnings):
            warnings.append(_issue("grounding", grounding.get("reason_code"), status="review"))
        if grounding.get("decision") == "blocked" and not any(item.get("component") == "grounding" for item in blockers):
            blockers.append(_issue("grounding", grounding.get("reason_code"), status="blocked"))
        evidence_summary = promotion.get("evidence_summary") or {}
        provider_readiness = _provider_readiness_summary(evidence_summary, blockers=blockers, warnings=warnings)

        return DomainAgentGroundedAnswerTrialReport(
            contract_version=TRIAL_SURFACE_CONTRACT_VERSION,
            agent_id=_clean(agent_id) or None,
            trial_status=trial_status,
            reason_code=self._reason_code(trial_status, grounding, promotion),
            recommended_next_action=self._next_action(trial_status),
            grounding_decision=grounding,
            promotion_decision=promotion,
            citation_allowlist=list(grounding.get("citation_allowlist") or []),
            blockers=blockers,
            warnings=warnings,
            evidence_summary=evidence_summary,
            provider_readiness=provider_readiness,
            boundary={
                "default_chat_retrieval_injection": DEFAULT_CHAT_RETRIEVAL_INJECTION,
                "provider_invocation": "not_performed",
                "answer_generation": "not_performed",
                "source_binding_creation": "not_performed",
                "memory_write": "not_performed",
                "audit_write": "not_performed",
                "trace_write": "not_performed",
                "chat_invocation": "not_performed",
                "graphrag_execution": "not_promoted",
                "runtime_behavior_changed": False,
            },
            request_summary={
                "domain": _clean(domain) or None,
                "query": _clean(query) or None,
                "query_provided": bool(_clean(query)),
                "evidence_pack_status": _clean((evidence_pack or {}).get("status")) or None,
                "graph_requested": bool(graph_requested),
            },
        )

    @staticmethod
    def _trial_status(grounding: Mapping[str, Any], promotion: Mapping[str, Any]) -> str:
        if grounding.get("decision") == "blocked" or promotion.get("decision") == "blocked":
            return "blocked"
        if grounding.get("decision") == "review" or promotion.get("decision") == "review":
            return "review"
        if grounding.get("decision") == "allowed" and promotion.get("decision") == "go":
            return "go"
        return "blocked"

    @staticmethod
    def _reason_code(
        trial_status: str,
        grounding: Mapping[str, Any],
        promotion: Mapping[str, Any],
    ) -> str:
        if trial_status == "go":
            return "grounded_answer_trial_ready"
        if trial_status == "review":
            return "grounded_answer_trial_requires_review"
        return _clean(promotion.get("reason_code")) or _clean(grounding.get("reason_code")) or "grounded_answer_trial_blocked"

    @staticmethod
    def _next_action(trial_status: str) -> str:
        if trial_status == "go":
            return "start_repo_side_grounded_answer_trial"
        if trial_status == "review":
            return "review_trial_warnings_before_answer_trial"
        return "resolve_trial_blockers_before_answer_trial"


def build_domain_agent_grounded_answer_trial_report(
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
    registry_service: DomainAgentRegistryService | None = None,
) -> dict[str, Any]:
    return DomainAgentGroundedAnswerTrialService(registry_service=registry_service).run_trial(
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


_domain_agent_grounded_answer_trial_service: DomainAgentGroundedAnswerTrialService | None = None


def get_domain_agent_grounded_answer_trial_service() -> DomainAgentGroundedAnswerTrialService:
    global _domain_agent_grounded_answer_trial_service
    if _domain_agent_grounded_answer_trial_service is None:
        _domain_agent_grounded_answer_trial_service = DomainAgentGroundedAnswerTrialService()
    return _domain_agent_grounded_answer_trial_service


def _issue(component: str, reason_code: Any, *, status: str) -> dict[str, Any]:
    return {
        "component": component,
        "status": status,
        "reason_code": _clean(reason_code) or "unknown",
    }


def _provider_readiness_summary(
    evidence_summary: Mapping[str, Any],
    *,
    blockers: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    provider = evidence_summary.get("provider") if isinstance(evidence_summary.get("provider"), Mapping) else {}
    if not provider:
        return {}
    provider_blockers = [dict(item) for item in blockers if item.get("component") == "provider"]
    provider_warnings = [dict(item) for item in warnings if item.get("component") == "provider"]
    graph_blockers = [
        dict(item)
        for item in blockers
        if item.get("component") == "graph"
        and _clean(provider.get("graph_query_status")) == "gated"
    ]
    return {
        "status": _clean(provider.get("status")) or "unknown",
        "ready": bool(provider.get("ready")),
        "reason_code": _clean(provider.get("reason_code")) or "provider_readiness_unknown",
        "readiness_source": _clean(provider.get("readiness_source")) or "unknown",
        "rag_retrieve_status": _clean(provider.get("rag_retrieve_status")) or "unknown",
        "source_catalog_status": _clean(provider.get("source_catalog_status")) or "unknown",
        "graph_query_status": _clean(provider.get("graph_query_status")) or "unknown",
        "default_chat_grounding_status": _clean(provider.get("default_chat_grounding_status")) or "unknown",
        "blockers": provider_blockers + graph_blockers,
        "warnings": provider_warnings,
        "promotion_boundary": {
            "default_chat_grounding": "not_promoted",
            "graphrag_execution": "not_promoted",
            "provider_invocation": "not_performed",
        },
    }


def _clean(value: Any) -> str:
    return str(value or "").strip()
