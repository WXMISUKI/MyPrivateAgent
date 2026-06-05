"""Side-effect-free grounding policy decisions for domain agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from backend.services.domain_agent_registry_service import (
    DomainAgentRegistryService,
    get_domain_agent_registry_service,
)


GROUNDING_DECISION_CONTRACT_VERSION = "agent-grounding-policy-decision-v1"
DEFAULT_CHAT_RETRIEVAL_INJECTION = "disabled"


@dataclass(frozen=True)
class GroundingPolicyDecision:
    contract_version: str
    agent_id: str | None
    decision: str
    reason_code: str
    recommended_action: str
    citation_allowlist: list[str] = field(default_factory=list)
    fallback_policy: str | None = None
    boundary: dict[str, Any] = field(default_factory=dict)
    policy_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentGroundingPolicyService:
    """Evaluate whether already-returned evidence may be used by an answer path."""

    def __init__(self, registry_service: DomainAgentRegistryService | None = None):
        self.registry_service = registry_service or get_domain_agent_registry_service()

    def decide(
        self,
        *,
        agent_id: str | None,
        domain: str | None = None,
        evidence_pack: Mapping[str, Any] | None = None,
        graph_requested: bool = False,
    ) -> GroundingPolicyDecision:
        clean_agent_id = _clean(agent_id)
        if graph_requested:
            return _decision(
                agent_id=clean_agent_id,
                decision="blocked",
                reason_code="graphrag_not_promoted",
                recommended_action="use_document_rag_or_wait_for_graphrag_promotion_gate",
            )
        if not clean_agent_id:
            return _decision(
                agent_id=None,
                decision="blocked",
                reason_code="agent_id_required",
                recommended_action="select_domain_agent_before_grounding",
            )

        agent = self._agent_by_id(clean_agent_id)
        if agent is None:
            return _decision(
                agent_id=clean_agent_id,
                decision="blocked",
                reason_code="agent_not_found",
                recommended_action="declare_domain_agent_manifest",
            )

        policy = agent.get("grounding_policy") if isinstance(agent.get("grounding_policy"), dict) else {}
        policy_source = _clean(policy.get("policy_source"))
        if policy_source in {"", "none"}:
            return _decision(
                agent_id=clean_agent_id,
                decision="review",
                reason_code="grounding_policy_not_declared",
                recommended_action="declare_grounding_policy_before_using_rag_evidence",
                policy=policy,
            )

        fallback_policy = _clean(policy.get("fallback_policy")) or "refuse_or_clarify_when_no_evidence"
        require_citations = bool(policy.get("require_citations"))
        must_use_domains = [
            _clean(item)
            for item in (policy.get("must_use_knowledge_for_domains") or [])
            if _clean(item)
        ]
        domain_requires_knowledge = _clean(domain) in must_use_domains
        allow_ungrounded = bool(policy.get("allow_ungrounded"))
        pack = dict(evidence_pack or {})
        pack_status = _clean(pack.get("status"))
        allowed_citations = [
            _clean(citation)
            for citation in (pack.get("allowed_citations") or [])
            if _clean(citation)
        ]

        if pack_status == "answerable" and (allowed_citations or not require_citations):
            return _decision(
                agent_id=clean_agent_id,
                decision="allowed",
                reason_code="answerable_evidence_pack",
                recommended_action="use_allowed_citations_only",
                citation_allowlist=allowed_citations,
                fallback_policy=fallback_policy,
                policy=policy,
            )
        if pack_status == "insufficient_evidence" and (require_citations or domain_requires_knowledge):
            return _decision(
                agent_id=clean_agent_id,
                decision="blocked",
                reason_code="insufficient_evidence",
                recommended_action=fallback_policy,
                fallback_policy=fallback_policy,
                policy=policy,
            )
        if require_citations and not allowed_citations:
            return _decision(
                agent_id=clean_agent_id,
                decision="blocked",
                reason_code="citations_required",
                recommended_action=fallback_policy,
                fallback_policy=fallback_policy,
                policy=policy,
            )
        if allow_ungrounded and not domain_requires_knowledge:
            return _decision(
                agent_id=clean_agent_id,
                decision="review",
                reason_code="ungrounded_allowed_by_policy",
                recommended_action="answer_without_claiming_sources",
                fallback_policy=fallback_policy,
                policy=policy,
            )
        return _decision(
            agent_id=clean_agent_id,
            decision="blocked",
            reason_code="grounding_evidence_required",
            recommended_action=fallback_policy,
            fallback_policy=fallback_policy,
            policy=policy,
        )

    def _agent_by_id(self, agent_id: str) -> dict[str, Any] | None:
        contract = self.registry_service.build_runtime_contract()
        agents = contract.get("agents") if isinstance(contract, dict) else []
        if not isinstance(agents, list):
            return None
        for agent in agents:
            if isinstance(agent, dict) and _clean(agent.get("id")) == agent_id:
                return agent
        return None


def build_grounding_policy_decision(
    *,
    agent_id: str | None,
    domain: str | None = None,
    evidence_pack: Mapping[str, Any] | None = None,
    graph_requested: bool = False,
    registry_service: DomainAgentRegistryService | None = None,
) -> dict[str, Any]:
    return AgentGroundingPolicyService(registry_service).decide(
        agent_id=agent_id,
        domain=domain,
        evidence_pack=evidence_pack,
        graph_requested=graph_requested,
    ).to_dict()


def _decision(
    *,
    agent_id: str | None,
    decision: str,
    reason_code: str,
    recommended_action: str,
    citation_allowlist: list[str] | None = None,
    fallback_policy: str | None = None,
    policy: Mapping[str, Any] | None = None,
) -> GroundingPolicyDecision:
    current_policy = dict(policy or {})
    return GroundingPolicyDecision(
        contract_version=GROUNDING_DECISION_CONTRACT_VERSION,
        agent_id=agent_id,
        decision=decision,
        reason_code=reason_code,
        recommended_action=recommended_action,
        citation_allowlist=list(citation_allowlist or []),
        fallback_policy=fallback_policy,
        boundary={
            "default_chat_retrieval_injection": DEFAULT_CHAT_RETRIEVAL_INJECTION,
            "provider_invocation": "not_performed",
            "source_binding_creation": "not_performed",
            "graphrag_execution": "not_promoted",
            "runtime_behavior_changed": False,
        },
        policy_summary={
            "policy_source": _clean(current_policy.get("policy_source")) or "none",
            "require_citations": current_policy.get("require_citations"),
            "allow_ungrounded": current_policy.get("allow_ungrounded"),
            "fallback_policy": current_policy.get("fallback_policy"),
            "source_acl_mode": current_policy.get("source_acl_mode"),
        },
    )


def _clean(value: Any) -> str:
    return str(value or "").strip()
