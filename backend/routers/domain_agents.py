"""Domain-agent integration trial APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

try:
    from services.domain_agent_catalog_service import get_domain_agent_catalog_service
    from services.domain_agent_grounded_answer_composition_trial_service import get_domain_agent_grounded_answer_composition_trial_service
    from services.domain_agent_grounded_answer_package_service import get_domain_agent_grounded_answer_package_service
    from services.domain_agent_grounded_answer_trial_service import get_domain_agent_grounded_answer_trial_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.domain_agent_catalog_service import get_domain_agent_catalog_service
    from backend.services.domain_agent_grounded_answer_composition_trial_service import get_domain_agent_grounded_answer_composition_trial_service
    from backend.services.domain_agent_grounded_answer_package_service import get_domain_agent_grounded_answer_package_service
    from backend.services.domain_agent_grounded_answer_trial_service import get_domain_agent_grounded_answer_trial_service


router = APIRouter(prefix="/api", tags=["domain-agents"])


@router.get("/agents")
def list_domain_agents() -> dict[str, Any]:
    return get_domain_agent_catalog_service().build_catalog()


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


@router.post("/domain-agents/{agent_id}/grounded-answer-package-dry-run")
def run_grounded_answer_package_dry_run(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    package = get_domain_agent_grounded_answer_package_service().build_package(
        agent_id=agent_id,
        domain=payload.get("domain"),
        query=payload.get("query"),
        evidence_pack=_mapping(payload.get("evidence_pack")),
        provider_evidence=_mapping(payload.get("provider_evidence")),
        promptops_evidence=_mapping(payload.get("promptops_evidence")),
        memoryops_evidence=_mapping(payload.get("memoryops_evidence")),
        eval_evidence=_mapping(payload.get("eval_evidence")),
        graph_requested=bool(payload.get("graph_requested")),
        trial_report=_mapping(payload.get("trial_report")),
    ).to_dict()
    return {
        "ok": package["package_status"] == "ready",
        "package": package,
    }


@router.post("/domain-agents/{agent_id}/grounded-answer-composition-trial")
def run_grounded_answer_composition_trial(agent_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    composition = get_domain_agent_grounded_answer_composition_trial_service().run_trial(
        agent_id=agent_id,
        domain=payload.get("domain"),
        query=payload.get("query"),
        evidence_pack=_mapping(payload.get("evidence_pack")),
        provider_evidence=_mapping(payload.get("provider_evidence")),
        promptops_evidence=_mapping(payload.get("promptops_evidence")),
        memoryops_evidence=_mapping(payload.get("memoryops_evidence")),
        eval_evidence=_mapping(payload.get("eval_evidence")),
        graph_requested=bool(payload.get("graph_requested")),
        trial_report=_mapping(payload.get("trial_report")),
        package=_mapping(payload.get("package")),
    ).to_dict()
    return {
        "ok": composition["composition_status"] == "ready",
        "composition": composition,
    }


def _mapping(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None
