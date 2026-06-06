"""Explicit live provider trial for domain-agent grounded answers."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import httpx

from backend.config import (
    KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL,
    KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
)
from backend.services.domain_agent_grounded_answer_composition_trial_service import (
    DomainAgentGroundedAnswerCompositionTrialService,
)
from backend.services.domain_agent_registry_service import (
    DomainAgentRegistryService,
    get_domain_agent_registry_service,
)
from backend.services.multiturn_eval_gate_service import MultiTurnEvalGateService


LIVE_TRIAL_CONTRACT_VERSION = "domain-agent-live-grounded-answer-trial-v1"
DEFAULT_PROVIDER_BASE_URL = KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL or "http://127.0.0.1:8020"
DEFAULT_OUTPUT_DIR = Path("docs/integration/domain-agent-live-grounded-answer-trial")
OUTPUT_JSON_FILENAME = "domain-agent-live-grounded-answer-trial.json"
OUTPUT_MARKDOWN_FILENAME = "domain-agent-live-grounded-answer-trial.md"
DEFAULT_MULTITURN_EVAL_DIR = Path("docs/evals/multiturn")


@dataclass(frozen=True)
class DomainAgentLiveGroundedAnswerTrialReport:
    contract_version: str
    generated_at: str
    agent_id: str | None
    query: str
    domain: str | None
    provider_base_url: str
    live_trial_status: str
    reason_code: str
    recommended_next_action: str
    provider_retrieve: dict[str, Any] = field(default_factory=dict)
    trial_report: dict[str, Any] = field(default_factory=dict)
    package: dict[str, Any] = field(default_factory=dict)
    composition: dict[str, Any] = field(default_factory=dict)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    boundary: dict[str, Any] = field(default_factory=dict)
    json_path: Path | None = None
    markdown_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.json_path is not None:
            payload["json_path"] = str(self.json_path)
        if self.markdown_path is not None:
            payload["markdown_path"] = str(self.markdown_path)
        return payload


class DomainAgentLiveGroundedAnswerTrialService:
    """Run an explicit provider-backed domain-agent trial without mutating runtime state."""

    def __init__(
        self,
        *,
        registry_service: DomainAgentRegistryService | None = None,
        composition_service: DomainAgentGroundedAnswerCompositionTrialService | None = None,
        eval_service: MultiTurnEvalGateService | None = None,
    ):
        self.registry_service = registry_service or get_domain_agent_registry_service()
        self.composition_service = composition_service or DomainAgentGroundedAnswerCompositionTrialService(
            registry_service=self.registry_service,
        )
        self.eval_service = eval_service or MultiTurnEvalGateService()

    def run_trial(
        self,
        *,
        agent_id: str,
        query: str,
        domain: str | None = None,
        provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
        provider_api_key: str | None = None,
        top_k: int = 3,
        timeout_seconds: float = KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        eval_dir: Path = DEFAULT_MULTITURN_EVAL_DIR,
        transport: httpx.BaseTransport | None = None,
    ) -> DomainAgentLiveGroundedAnswerTrialReport:
        clean_agent_id = _clean(agent_id)
        clean_query = _clean(query)
        base_url = provider_base_url.rstrip("/")
        boundary = _boundary()
        if not clean_agent_id:
            return _blocked_report(
                agent_id=None,
                query=clean_query,
                domain=domain,
                provider_base_url=base_url,
                reason_code="agent_id_required",
                blocker=_issue("agent", "agent_id_required", status="blocked"),
                boundary=boundary,
            )
        if not clean_query:
            return _blocked_report(
                agent_id=clean_agent_id,
                query=clean_query,
                domain=domain,
                provider_base_url=base_url,
                reason_code="query_required",
                blocker=_issue("request", "query_required", status="blocked"),
                boundary=boundary,
            )

        agent = self._agent_by_id(clean_agent_id)
        if agent is None:
            return _blocked_report(
                agent_id=clean_agent_id,
                query=clean_query,
                domain=domain,
                provider_base_url=base_url,
                reason_code="agent_not_found",
                blocker=_issue("agent", "agent_not_found", status="blocked"),
                boundary=boundary,
            )

        rag_sources = _rag_sources(agent)
        if not rag_sources:
            return _blocked_report(
                agent_id=clean_agent_id,
                query=clean_query,
                domain=domain,
                provider_base_url=base_url,
                reason_code="rag_sources_missing",
                blocker=_issue("agent", "rag_sources_missing", status="blocked"),
                boundary=boundary,
            )

        provider_retrieve = self._retrieve_provider(
            base_url=base_url,
            provider_api_key=provider_api_key,
            query=clean_query,
            knowledge_base_ids=rag_sources,
            top_k=top_k,
            timeout_seconds=timeout_seconds,
            transport=transport,
        )
        if provider_retrieve.get("status") == "blocked":
            return _blocked_report(
                agent_id=clean_agent_id,
                query=clean_query,
                domain=domain,
                provider_base_url=base_url,
                reason_code=str(provider_retrieve.get("reason_code") or "provider_retrieve_blocked"),
                blocker=_issue("provider", str(provider_retrieve.get("reason_code") or "provider_retrieve_blocked"), status="blocked"),
                boundary=boundary,
                provider_retrieve=provider_retrieve,
            )

        evidence_pack = dict(provider_retrieve.get("evidence_pack") or {})
        provider_evidence = {
            "status": "trial_passed" if provider_retrieve.get("status") == "ready" else "review",
            "provider_base_url": base_url,
            "document_count": provider_retrieve.get("document_count"),
            "evidence_pack_status": evidence_pack.get("status"),
        }
        composition = self.composition_service.run_trial(
            agent_id=clean_agent_id,
            domain=domain,
            query=clean_query,
            evidence_pack=evidence_pack,
            provider_evidence=provider_evidence,
            promptops_evidence=_default_promptops_evidence(clean_agent_id),
            memoryops_evidence=_default_memoryops_evidence(),
            eval_evidence=self._eval_evidence(eval_dir),
        ).to_dict()

        package = composition.get("package") if isinstance(composition.get("package"), dict) else {}
        trial_report = package.get("trial_report") if isinstance(package.get("trial_report"), dict) else {}
        live_status = _status_from_composition(composition.get("composition_status"))
        blockers = [
            *list(provider_retrieve.get("blockers") or []),
            *list(composition.get("blockers") or []),
        ]
        warnings = [
            *list(provider_retrieve.get("warnings") or []),
            *list(composition.get("warnings") or []),
        ]
        return DomainAgentLiveGroundedAnswerTrialReport(
            contract_version=LIVE_TRIAL_CONTRACT_VERSION,
            generated_at=datetime.now(UTC).isoformat(),
            agent_id=clean_agent_id,
            query=clean_query,
            domain=_clean(domain) or None,
            provider_base_url=base_url,
            live_trial_status=live_status,
            reason_code=_reason_code(live_status, composition),
            recommended_next_action=_next_action(live_status),
            provider_retrieve=provider_retrieve,
            trial_report=trial_report,
            package=package,
            composition=composition,
            blockers=blockers,
            warnings=warnings,
            boundary=boundary,
        )

    def export_trial(
        self,
        *,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        **kwargs: Any,
    ) -> DomainAgentLiveGroundedAnswerTrialReport:
        output_dir.mkdir(parents=True, exist_ok=True)
        report = self.run_trial(**kwargs)
        json_path = output_dir / OUTPUT_JSON_FILENAME
        markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
        exported = DomainAgentLiveGroundedAnswerTrialReport(
            contract_version=report.contract_version,
            generated_at=report.generated_at,
            agent_id=report.agent_id,
            query=report.query,
            domain=report.domain,
            provider_base_url=report.provider_base_url,
            live_trial_status=report.live_trial_status,
            reason_code=report.reason_code,
            recommended_next_action=report.recommended_next_action,
            provider_retrieve=report.provider_retrieve,
            trial_report=report.trial_report,
            package=report.package,
            composition=report.composition,
            blockers=report.blockers,
            warnings=report.warnings,
            boundary=report.boundary,
            json_path=json_path,
            markdown_path=markdown_path,
        )
        json_path.write_text(json.dumps(exported.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text(render_domain_agent_live_grounded_answer_trial_markdown(exported), encoding="utf-8")
        return exported

    def _agent_by_id(self, agent_id: str) -> dict[str, Any] | None:
        contract = self.registry_service.build_runtime_contract()
        agents = contract.get("agents") if isinstance(contract, dict) else []
        if not isinstance(agents, list):
            return None
        for agent in agents:
            if isinstance(agent, dict) and _clean(agent.get("id")) == agent_id:
                return agent
        return None

    def _retrieve_provider(
        self,
        *,
        base_url: str,
        provider_api_key: str | None,
        query: str,
        knowledge_base_ids: list[str],
        top_k: int,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None,
    ) -> dict[str, Any]:
        endpoint = "/api/rag/retrieve"
        headers = _provider_headers(provider_api_key)
        try:
            with httpx.Client(timeout=timeout_seconds, transport=transport, trust_env=False) as client:
                response = client.post(
                    f"{base_url}{endpoint}",
                    headers=headers,
                    json={"query": query, "knowledge_base_ids": knowledge_base_ids, "top_k": top_k},
                )
                payload = response.json()
        except httpx.RequestError as exc:
            return _provider_blocked(endpoint, "provider_unreachable", str(exc))
        except ValueError as exc:
            return _provider_blocked(endpoint, "provider_invalid_json", str(exc))
        if not isinstance(payload, dict):
            return _provider_blocked(endpoint, "provider_invalid_json_shape", "Provider returned non-object JSON.")
        if response.status_code >= 400:
            error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
            return _provider_blocked(
                endpoint,
                str(error.get("code") or "provider_http_error"),
                str(error.get("message") or response.text or response.status_code),
            )
        result = payload.get("result") if isinstance(payload.get("result"), dict) else payload
        documents = result.get("documents")
        metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        evidence_pack = metadata.get("evidence_pack") if isinstance(metadata.get("evidence_pack"), dict) else None
        if not isinstance(documents, list) or evidence_pack is None:
            return _provider_blocked(endpoint, "rag_retrieve_contract_mismatch", "Missing documents or evidence_pack.")
        normalized_pack = _normalize_evidence_pack(evidence_pack, documents)
        pack_status = _clean(normalized_pack.get("status")) or "unknown"
        if pack_status not in {"answerable", "insufficient_evidence"}:
            status = "review"
            warnings = [_issue("provider", "evidence_pack_status_review_required", status="review")]
        else:
            status = "ready"
            warnings = []
        return {
            "endpoint": endpoint,
            "status": status,
            "reason_code": "provider_retrieve_ready" if status == "ready" else "provider_retrieve_review",
            "document_count": len(documents),
            "knowledge_base_ids": knowledge_base_ids,
            "evidence_pack_status": pack_status,
            "citation_policy": normalized_pack.get("citation_policy"),
            "allowed_citations": normalized_pack.get("allowed_citations") or [],
            "documents": documents,
            "evidence_pack": normalized_pack,
            "warnings": warnings,
            "blockers": [],
        }

    def _eval_evidence(self, eval_dir: Path) -> dict[str, Any]:
        if not eval_dir.exists():
            return {"overall_status": "missing", "reason_code": "multiturn_eval_dir_missing"}
        return self.eval_service.evaluate_directory(eval_dir)


def render_domain_agent_live_grounded_answer_trial_markdown(
    report: DomainAgentLiveGroundedAnswerTrialReport,
) -> str:
    lines = [
        "# Domain Agent Live Grounded Answer Trial",
        "",
        f"- Contract: `{report.contract_version}`",
        f"- Status: `{report.live_trial_status}`",
        f"- Reason: `{report.reason_code}`",
        f"- Next Action: `{report.recommended_next_action}`",
        f"- Agent: `{report.agent_id}`",
        f"- Domain: `{report.domain}`",
        f"- Provider: `{report.provider_base_url}`",
        f"- Generated At: `{report.generated_at}`",
        "",
        "## Provider Retrieve",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for key in ("status", "reason_code", "document_count", "evidence_pack_status", "citation_policy", "allowed_citations"):
        lines.append(f"| `{key}` | `{_format_value(report.provider_retrieve.get(key))}` |")
    lines.extend(["", "## Downstream Status", "", "| Stage | Status | Reason |", "|---|---|---|"])
    lines.append(
        f"| `trial` | `{report.trial_report.get('trial_status')}` | `{report.trial_report.get('reason_code')}` |"
    )
    lines.append(f"| `package` | `{report.package.get('package_status')}` | `{report.package.get('reason_code')}` |")
    lines.append(
        f"| `composition` | `{report.composition.get('composition_status')}` | `{report.composition.get('reason_code')}` |"
    )
    lines.extend(["", "## Boundary", "", "| Boundary | Value |", "|---|---|"])
    for key, value in report.boundary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.append("")
    return "\n".join(lines)


def _blocked_report(
    *,
    agent_id: str | None,
    query: str,
    domain: str | None,
    provider_base_url: str,
    reason_code: str,
    blocker: dict[str, Any],
    boundary: dict[str, Any],
    provider_retrieve: dict[str, Any] | None = None,
) -> DomainAgentLiveGroundedAnswerTrialReport:
    return DomainAgentLiveGroundedAnswerTrialReport(
        contract_version=LIVE_TRIAL_CONTRACT_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        agent_id=agent_id,
        query=query,
        domain=_clean(domain) or None,
        provider_base_url=provider_base_url,
        live_trial_status="blocked",
        reason_code=reason_code,
        recommended_next_action="resolve_live_trial_blockers_before_grounded_answer_trial",
        provider_retrieve=dict(provider_retrieve or {}),
        blockers=[blocker],
        warnings=[],
        boundary=boundary,
    )


def _provider_blocked(endpoint: str, reason_code: str, message: str) -> dict[str, Any]:
    return {
        "endpoint": endpoint,
        "status": "blocked",
        "reason_code": reason_code,
        "document_count": 0,
        "evidence_pack": {},
        "documents": [],
        "blockers": [_issue("provider", reason_code, status="blocked", message=message)],
        "warnings": [],
    }


def _normalize_evidence_pack(evidence_pack: Mapping[str, Any], documents: list[Any]) -> dict[str, Any]:
    normalized = dict(evidence_pack)
    citations = [
        _clean(document.get("citation"))
        for document in documents
        if isinstance(document, dict) and _clean(document.get("citation"))
    ]
    if not normalized.get("allowed_citations") and citations:
        normalized["allowed_citations"] = citations
    return normalized


def _rag_sources(agent: Mapping[str, Any]) -> list[str]:
    capabilities = agent.get("capabilities") if isinstance(agent.get("capabilities"), dict) else {}
    return [_clean(source_id) for source_id in (capabilities.get("rag_sources") or []) if _clean(source_id)]


def _default_promptops_evidence(agent_id: str) -> dict[str, Any]:
    return {
        "prompt_key": f"{agent_id}.grounded_answer",
        "version": "1",
        "status": "active",
    }


def _default_memoryops_evidence() -> dict[str, Any]:
    return {
        "retrieved_knowledge_promotion_mode": "explicit_only",
        "stored_as_memory_by_default": False,
    }


def _status_from_composition(status: Any) -> str:
    normalized = _clean(status).lower()
    if normalized == "ready":
        return "go"
    if normalized == "review":
        return "review"
    return "blocked"


def _reason_code(live_status: str, composition: Mapping[str, Any]) -> str:
    if live_status == "go":
        return "live_grounded_answer_trial_ready"
    if live_status == "review":
        return "live_grounded_answer_trial_review_required"
    return _clean(composition.get("reason_code")) or "live_grounded_answer_trial_blocked"


def _next_action(live_status: str) -> str:
    if live_status == "go":
        return "proceed_with_explicit_grounded_answer_trial"
    if live_status == "review":
        return "review_live_trial_warnings"
    return "resolve_live_trial_blockers_before_grounded_answer_trial"


def _provider_headers(provider_api_key: str | None) -> dict[str, str]:
    if not provider_api_key:
        return {}
    return {
        "Authorization": f"Bearer {provider_api_key}",
        "X-Provider-Api-Key": provider_api_key,
    }


def _boundary() -> dict[str, Any]:
    return {
        "default_chat_retrieval_injection": "disabled",
        "chat_invocation": "not_performed",
        "model_invocation": "not_performed",
        "tool_execution": "not_performed",
        "source_binding_creation": "not_performed",
        "memory_write": "not_performed",
        "audit_write": "not_performed",
        "trace_write": "not_performed",
        "graphrag_execution": "not_promoted",
        "runtime_behavior_changed": False,
    }


def _issue(component: str, reason_code: str, *, status: str, message: str | None = None) -> dict[str, Any]:
    issue = {
        "component": component,
        "status": status,
        "reason_code": reason_code,
    }
    if message:
        issue["message"] = message
    return issue


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _clean(value: Any) -> str:
    return str(value or "").strip()
