"""Domain-agent integration trial APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

try:
    from services.domain_agent_grounded_answer_trial_service import get_domain_agent_grounded_answer_trial_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.domain_agent_grounded_answer_trial_service import get_domain_agent_grounded_answer_trial_service


router = APIRouter(prefix="/api", tags=["domain-agents"])


@router.post("/domain-agents/{agent_id}/grounded-answer-trial")
def run_grounded_answer_trial(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    trial = get_domain_agent_grounded_answer_trial_service().run_trial(
        agent_id=agent_id,
        domain=payload.get("domain"),
        query=payload.get("query"),
        evidence_pack=_mapping(payload.get("evidence_pack")),
        provider_evidence=_mapping(payload.get("provider_evidence")),
        promptops_evidence=_mapping(payload.get("promptops_evidence")),
        memoryops_evidence=_mapping(payload.get("memoryops_evidence")),
        eval_evidence=_mapping(payload.get("eval_evidence")),
        graph_requested=bool(payload.get("graph_requested")),
    ).to_dict()
    return {
        "ok": trial["trial_status"] == "go",
        "trial": trial,
    }


def _mapping(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None
