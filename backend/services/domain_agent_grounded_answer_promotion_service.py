"""Side-effect-free promotion gate for domain-agent grounded answer trials."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

from backend.services.agent_grounding_policy_service import (
    AgentGroundingPolicyService,
    DEFAULT_CHAT_RETRIEVAL_INJECTION,
)
from backend.services.domain_agent_registry_service import (
    DomainAgentRegistryService,
    get_domain_agent_registry_service,
)


PROMOTION_GATE_CONTRACT_VERSION = "domain-agent-grounded-answer-promotion-gate-v1"

READY_STATUSES = {"ready", "passed", "trial_passed", "go", "allowed", "active", "review"}
BLOCKED_STATUSES = {"blocked", "failed", "error", "degraded", "unreachable", "not_ready"}


@dataclass(frozen=True)
class DomainAgentGroundedAnswerPromotionDecision:
    contract_version: str
    agent_id: str | None
    decision: str
    reason_code: str
    recommended_next_action: str
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    evidence_summary: dict[str, Any] = field(default_factory=dict)
    boundary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DomainAgentGroundedAnswerPromotionService:
    """Aggregate readiness evidence before a grounded answer path is trialed."""

    def __init__(
        self,
        registry_service: DomainAgentRegistryService | None = None,
        grounding_service: AgentGroundingPolicyService | None = None,
    ):
        self.registry_service = registry_service or get_domain_agent_registry_service()
        self.grounding_service = grounding_service or AgentGroundingPolicyService(self.registry_service)

    def evaluate(
        self,
        *,
        agent_id: str | None,
        domain: str | None = None,
        provider_evidence: Mapping[str, Any] | None = None,
        grounding_decision: Mapping[str, Any] | None = None,
        evidence_pack: Mapping[str, Any] | None = None,
        promptops_evidence: Mapping[str, Any] | None = None,
        memoryops_evidence: Mapping[str, Any] | None = None,
        eval_evidence: Mapping[str, Any] | None = None,
        graph_requested: bool = False,
    ) -> DomainAgentGroundedAnswerPromotionDecision:
        clean_agent_id = _clean(agent_id)
        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []

        agent_exists = self._agent_exists(clean_agent_id)
        if not clean_agent_id:
            blockers.append(_issue("agent", "agent_id_required", status="missing"))
        elif not agent_exists:
            blockers.append(_issue("agent", "agent_not_found", status="missing"))

        if graph_requested:
            blockers.append(_issue("graph", "graphrag_not_promoted", status="blocked"))

        provider_summary = self._provider_summary(provider_evidence)
        if not provider_summary["ready"]:
            issue = _issue("provider", provider_summary["reason_code"], status=provider_summary["status"])
            if provider_summary["status"] == "review":
                warnings.append(issue)
            else:
                blockers.append(issue)
        if graph_requested and provider_summary.get("graph_query_status") == "gated":
            graph_issue = _issue("graph", "graphrag_not_promoted_by_provider_readiness", status="blocked")
            if graph_issue not in blockers:
                blockers.append(graph_issue)

        grounding_summary = self._grounding_summary(
            clean_agent_id,
            domain=domain,
            grounding_decision=grounding_decision,
            evidence_pack=evidence_pack,
            graph_requested=graph_requested,
        )
        if grounding_summary["decision"] == "blocked":
            blockers.append(_issue("grounding", grounding_summary["reason_code"], status="blocked"))
        elif grounding_summary["decision"] == "review":
            warnings.append(_issue("grounding", grounding_summary["reason_code"], status="review"))
        elif grounding_summary["decision"] != "allowed":
            blockers.append(_issue("grounding", "grounding_decision_not_allowed", status=grounding_summary["decision"]))

        promptops_summary = self._promptops_summary(promptops_evidence)
        if not promptops_summary["ready"]:
            warnings.append(_issue("promptops", promptops_summary["reason_code"], status=promptops_summary["status"]))

        memoryops_summary = self._memoryops_summary(memoryops_evidence)
        if not memoryops_summary["ready"]:
            warnings.append(_issue("memoryops", memoryops_summary["reason_code"], status=memoryops_summary["status"]))

        eval_summary = self._eval_summary(eval_evidence)
        if eval_summary["status"] in {"failed", "blocked"}:
            blockers.append(_issue("eval", eval_summary["reason_code"], status=eval_summary["status"]))
        elif not eval_summary["ready"]:
            warnings.append(_issue("eval", eval_summary["reason_code"], status=eval_summary["status"]))

        if blockers:
            decision = "blocked"
            reason_code = "promotion_prerequisites_blocked"
            recommended_next_action = "resolve_blockers_before_grounded_answer_trial"
        elif warnings:
            decision = "review"
            reason_code = "promotion_requires_review"
            recommended_next_action = "review_warnings_before_grounded_answer_trial"
        else:
            decision = "go"
            reason_code = "grounded_answer_trial_ready"
            recommended_next_action = "start_repo_side_grounded_answer_trial"

        return DomainAgentGroundedAnswerPromotionDecision(
            contract_version=PROMOTION_GATE_CONTRACT_VERSION,
            agent_id=clean_agent_id or None,
            decision=decision,
            reason_code=reason_code,
            recommended_next_action=recommended_next_action,
            blockers=blockers,
            warnings=warnings,
            evidence_summary={
                "agent": {"exists": agent_exists, "status": "ready" if agent_exists else "missing"},
                "provider": provider_summary,
                "grounding": grounding_summary,
                "promptops": promptops_summary,
                "memoryops": memoryops_summary,
                "eval": eval_summary,
            },
            boundary={
                "default_chat_retrieval_injection": DEFAULT_CHAT_RETRIEVAL_INJECTION,
                "provider_invocation": "not_performed",
                "answer_generation": "not_performed",
                "source_binding_creation": "not_performed",
                "memory_write": "not_performed",
                "graphrag_execution": "not_promoted",
                "runtime_behavior_changed": False,
            },
        )

    def _agent_exists(self, agent_id: str) -> bool:
        if not agent_id:
            return False
        contract = self.registry_service.build_runtime_contract()
        agents = contract.get("agents") if isinstance(contract, dict) else []
        if not isinstance(agents, list):
            return False
        return any(isinstance(agent, dict) and _clean(agent.get("id")) == agent_id for agent in agents)

    def _grounding_summary(
        self,
        agent_id: str,
        *,
        domain: str | None,
        grounding_decision: Mapping[str, Any] | None,
        evidence_pack: Mapping[str, Any] | None,
        graph_requested: bool,
    ) -> dict[str, Any]:
        decision = dict(grounding_decision or {})
        if not decision:
            decision = self.grounding_service.decide(
                agent_id=agent_id or None,
                domain=domain,
                evidence_pack=evidence_pack,
                graph_requested=graph_requested,
            ).to_dict()
        return {
            "decision": _clean(decision.get("decision")) or "unknown",
            "reason_code": _clean(decision.get("reason_code")) or "grounding_decision_missing",
            "citation_count": len(decision.get("citation_allowlist") or []),
            "fallback_policy": decision.get("fallback_policy"),
        }

    @staticmethod
    def _provider_summary(provider_evidence: Mapping[str, Any] | None) -> dict[str, Any]:
        evidence = dict(provider_evidence or {})
        readiness = evidence.get("governance_readiness") if isinstance(evidence.get("governance_readiness"), Mapping) else {}
        if readiness:
            rag = readiness.get("rag_retrieve") if isinstance(readiness.get("rag_retrieve"), Mapping) else {}
            graph = readiness.get("graph_query") if isinstance(readiness.get("graph_query"), Mapping) else {}
            default_chat = readiness.get("default_chat_grounding") if isinstance(readiness.get("default_chat_grounding"), Mapping) else {}
            source_catalog = readiness.get("source_catalog") if isinstance(readiness.get("source_catalog"), Mapping) else {}
            overall_status = _first_clean(readiness.get("overall_status"))
            rag_status = _first_clean(rag.get("status"))
            source_catalog_status = _first_clean(source_catalog.get("status"))
            graph_query_status = _first_clean(graph.get("status"))
            default_chat_status = _first_clean(default_chat.get("status"))
            summary = {
                "ready": False,
                "status": overall_status or rag_status or "unknown",
                "reason_code": "provider_readiness_unknown",
                "readiness_source": "governance_readiness",
                "rag_retrieve_status": rag_status or "unknown",
                "graph_query_status": graph_query_status or "unknown",
                "default_chat_grounding_status": default_chat_status or "unknown",
                "source_catalog_status": source_catalog_status or "unknown",
            }
            if overall_status == "unreachable" or rag_status == "unreachable":
                summary.update({"status": "unreachable", "reason_code": "provider_unreachable"})
                return summary
            if rag_status == "ready":
                if source_catalog_status == "degraded" or overall_status == "degraded":
                    summary.update({"status": "review", "reason_code": "provider_source_catalog_degraded"})
                    return summary
                summary.update({"ready": True, "status": "ready", "reason_code": "provider_rag_ready"})
                return summary
            if rag_status in BLOCKED_STATUSES:
                summary.update({"status": rag_status, "reason_code": "provider_rag_not_ready"})
                return summary
            return summary
        status = _first_clean(
            evidence.get("status"),
            evidence.get("decision"),
            evidence.get("overall_status"),
            evidence.get("trial_status"),
            evidence.get("closure_decision"),
        )
        if not evidence:
            return {"ready": False, "status": "missing", "reason_code": "provider_readiness_missing"}
        if status in READY_STATUSES:
            return {"ready": True, "status": status, "reason_code": "provider_ready", "readiness_source": "legacy_status"}
        if status in BLOCKED_STATUSES:
            return {"ready": False, "status": status, "reason_code": "provider_not_ready", "readiness_source": "legacy_status"}
        return {"ready": False, "status": status or "unknown", "reason_code": "provider_readiness_unknown", "readiness_source": "legacy_status"}

    @staticmethod
    def _promptops_summary(promptops_evidence: Mapping[str, Any] | None) -> dict[str, Any]:
        evidence = dict(promptops_evidence or {})
        status = _first_clean(evidence.get("status"), evidence.get("prompt_status"), evidence.get("overall_status"))
        prompt_key = _clean(evidence.get("prompt_key")) or None
        version = _clean(evidence.get("version")) or None
        if not evidence:
            return {"ready": False, "status": "missing", "reason_code": "promptops_evidence_missing"}
        if status in {"active", "review", "passed", "ready"}:
            return {"ready": True, "status": status, "reason_code": "promptops_ready", "prompt_key": prompt_key, "version": version}
        return {"ready": False, "status": status or "unknown", "reason_code": "promptops_review_required", "prompt_key": prompt_key, "version": version}

    @staticmethod
    def _memoryops_summary(memoryops_evidence: Mapping[str, Any] | None) -> dict[str, Any]:
        evidence = dict(memoryops_evidence or {})
        posture = evidence.get("posture") if isinstance(evidence.get("posture"), dict) else {}
        retrieved = posture.get("retrieved_knowledge_evidence") if isinstance(posture.get("retrieved_knowledge_evidence"), dict) else {}
        promotion_mode = _first_clean(evidence.get("retrieved_knowledge_promotion_mode"), retrieved.get("promotion_mode"))
        stored_by_default = evidence.get("stored_as_memory_by_default", retrieved.get("stored_as_memory_by_default"))
        if not evidence:
            return {"ready": False, "status": "missing", "reason_code": "memoryops_evidence_missing"}
        if promotion_mode == "explicit_only" and stored_by_default is not True:
            return {"ready": True, "status": "ready", "reason_code": "memoryops_explicit_only", "retrieved_knowledge_promotion_mode": promotion_mode}
        return {"ready": False, "status": "review", "reason_code": "memoryops_boundary_review_required", "retrieved_knowledge_promotion_mode": promotion_mode or "unknown"}

    @staticmethod
    def _eval_summary(eval_evidence: Mapping[str, Any] | None) -> dict[str, Any]:
        evidence = dict(eval_evidence or {})
        status = _first_clean(evidence.get("overall_status"), evidence.get("status"), evidence.get("decision"))
        if not evidence:
            return {"ready": False, "status": "missing", "reason_code": "eval_evidence_missing"}
        if status == "passed":
            return {"ready": True, "status": status, "reason_code": "eval_passed"}
        if status in {"failed", "blocked"}:
            return {"ready": False, "status": status, "reason_code": "eval_not_passed"}
        return {"ready": False, "status": status or "unknown", "reason_code": "eval_review_required"}


def build_domain_agent_grounded_answer_promotion_decision(
    *,
    agent_id: str | None,
    domain: str | None = None,
    provider_evidence: Mapping[str, Any] | None = None,
    grounding_decision: Mapping[str, Any] | None = None,
    evidence_pack: Mapping[str, Any] | None = None,
    promptops_evidence: Mapping[str, Any] | None = None,
    memoryops_evidence: Mapping[str, Any] | None = None,
    eval_evidence: Mapping[str, Any] | None = None,
    graph_requested: bool = False,
    registry_service: DomainAgentRegistryService | None = None,
) -> dict[str, Any]:
    return DomainAgentGroundedAnswerPromotionService(registry_service).evaluate(
        agent_id=agent_id,
        domain=domain,
        provider_evidence=provider_evidence,
        grounding_decision=grounding_decision,
        evidence_pack=evidence_pack,
        promptops_evidence=promptops_evidence,
        memoryops_evidence=memoryops_evidence,
        eval_evidence=eval_evidence,
        graph_requested=graph_requested,
    ).to_dict()


def _issue(component: str, reason_code: str, *, status: str) -> dict[str, Any]:
    return {
        "component": component,
        "status": status,
        "reason_code": reason_code,
    }


def _first_clean(*values: Any) -> str:
    for value in values:
        cleaned = _clean(value).lower()
        if cleaned:
            return cleaned
    return ""


def _clean(value: Any) -> str:
    return str(value or "").strip()
