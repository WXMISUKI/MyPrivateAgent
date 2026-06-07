"""Caller-facing API adapter for explicit domain-agent live grounded answers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from backend.services.domain_agent_live_grounded_answer_trial_service import (
    DEFAULT_MULTITURN_EVAL_DIR,
    DEFAULT_PROVIDER_BASE_URL,
    DomainAgentLiveGroundedAnswerTrialReport,
    DomainAgentLiveGroundedAnswerTrialService,
)


class DomainAgentLiveGroundedAnswerApiService:
    """Adapt verbose live trial reports into a compact caller contract."""

    def __init__(self, *, trial_service: DomainAgentLiveGroundedAnswerTrialService | None = None):
        self.trial_service = trial_service or DomainAgentLiveGroundedAnswerTrialService()

    def run(
        self,
        *,
        agent_id: str,
        query: str,
        domain: str | None = None,
        provider_base_url: str | None = DEFAULT_PROVIDER_BASE_URL,
        provider_api_key: str | None = None,
        top_k: int = 3,
        timeout_seconds: float | None = None,
        eval_dir: Path = DEFAULT_MULTITURN_EVAL_DIR,
        transport: httpx.BaseTransport | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "agent_id": agent_id,
            "query": query,
            "domain": domain,
            "provider_base_url": _clean(provider_base_url) or DEFAULT_PROVIDER_BASE_URL,
            "provider_api_key": provider_api_key,
            "top_k": top_k,
            "eval_dir": eval_dir,
            "transport": transport,
        }
        if timeout_seconds is not None:
            kwargs["timeout_seconds"] = timeout_seconds
        report = self.trial_service.run_trial(**kwargs)
        return render_live_grounded_answer_api_response(report)


def render_live_grounded_answer_api_response(report: DomainAgentLiveGroundedAnswerTrialReport) -> dict[str, Any]:
    payload = report.to_dict()
    composition = report.composition if isinstance(report.composition, dict) else {}
    provider_retrieve = report.provider_retrieve if isinstance(report.provider_retrieve, dict) else {}
    documents = provider_retrieve.get("documents") if isinstance(provider_retrieve.get("documents"), list) else []
    citations = _string_list(
        composition.get("used_citations")
        or provider_retrieve.get("allowed_citations")
        or []
    )
    return {
        "ok": report.live_trial_status == "go",
        "status": report.live_trial_status,
        "reason_code": report.reason_code,
        "recommended_next_action": report.recommended_next_action,
        "agent_id": report.agent_id,
        "domain": report.domain,
        "query": report.query,
        "provider_base_url": report.provider_base_url,
        "answer_preview": _clean(composition.get("answer_preview")),
        "citations": citations,
        "documents": [_document_summary(document) for document in documents if isinstance(document, dict)],
        "blockers": list(report.blockers or []),
        "warnings": list(report.warnings or []),
        "boundary": dict(report.boundary or {}),
        "trial": payload,
    }


def get_domain_agent_live_grounded_answer_api_service() -> DomainAgentLiveGroundedAnswerApiService:
    return DomainAgentLiveGroundedAnswerApiService()


def _document_summary(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": _clean(document.get("source_id")),
        "document_id": _clean(document.get("document_id")),
        "title": _clean(document.get("title")),
        "snippet": _clean(document.get("snippet")),
        "score": document.get("score"),
        "citation": _clean(document.get("citation")),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _clean(value: Any) -> str:
    return str(value or "").strip()
