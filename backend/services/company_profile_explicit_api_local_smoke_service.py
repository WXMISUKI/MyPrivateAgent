"""Local smoke for MyPrivateAgent explicit company-profile grounded-answer API."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.domain_agents import router as domain_agents_router
from backend.services.domain_agent_live_grounded_answer_trial_service import DEFAULT_PROVIDER_BASE_URL


SMOKE_CONTRACT_VERSION = "company-profile-explicit-api-local-smoke-v1"
DEFAULT_AGENT_ID = "company_profile"
DEFAULT_DOMAIN = "company.profile"
DEFAULT_QUERY = "公司主营业务是什么？"
DEFAULT_OUTPUT_DIR = Path("docs/integration/company-profile-explicit-api-local-smoke")
OUTPUT_JSON_FILENAME = "company-profile-explicit-api-local-smoke.json"
OUTPUT_MARKDOWN_FILENAME = "company-profile-explicit-api-local-smoke.md"


@dataclass(frozen=True)
class CompanyProfileExplicitApiLocalSmokeReport:
    contract_version: str
    generated_at: str
    decision: str
    reason_code: str
    recommended_next_action: str
    endpoint: str
    agent_id: str
    domain: str | None
    query: str
    provider_base_url: str
    http_status_code: int | None
    ok: bool
    api_status: str | None
    answer_preview: str
    citations: list[str] = field(default_factory=list)
    document_count: int = 0
    blockers: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    boundary: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    json_path: Path | None = None
    markdown_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.json_path is not None:
            payload["json_path"] = str(self.json_path)
        if self.markdown_path is not None:
            payload["markdown_path"] = str(self.markdown_path)
        return payload


def run_company_profile_explicit_api_local_smoke(
    *,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    agent_id: str = DEFAULT_AGENT_ID,
    domain: str | None = DEFAULT_DOMAIN,
    query: str = DEFAULT_QUERY,
    top_k: int = 3,
    timeout_seconds: float = 5,
    client: TestClient | None = None,
) -> CompanyProfileExplicitApiLocalSmokeReport:
    endpoint = f"/api/domain-agents/{agent_id}/live-grounded-answer"
    payload = {
        "query": query,
        "domain": domain,
        "provider_base_url": provider_base_url,
        "top_k": top_k,
        "timeout_seconds": timeout_seconds,
    }
    if provider_api_key:
        payload["provider_api_key"] = provider_api_key
    active_client = client or _default_client()
    try:
        response = active_client.post(endpoint, json=payload)
        response_payload = response.json()
    except Exception as exc:  # pragma: no cover - defensive smoke boundary
        return _blocked_report(
            endpoint=endpoint,
            agent_id=agent_id,
            domain=domain,
            query=query,
            provider_base_url=provider_base_url,
            http_status_code=None,
            reason_code="explicit_api_route_failed",
            blocker=_issue("explicit_api", "explicit_api_route_failed", message=str(exc)),
        )
    if not isinstance(response_payload, dict):
        return _blocked_report(
            endpoint=endpoint,
            agent_id=agent_id,
            domain=domain,
            query=query,
            provider_base_url=provider_base_url,
            http_status_code=response.status_code,
            reason_code="explicit_api_invalid_response_shape",
            blocker=_issue("explicit_api", "explicit_api_invalid_response_shape"),
        )

    if _contains_secret(response_payload, provider_api_key):
        return _blocked_report(
            endpoint=endpoint,
            agent_id=agent_id,
            domain=domain,
            query=query,
            provider_base_url=provider_base_url,
            http_status_code=response.status_code,
            reason_code="provider_api_key_leaked",
            blocker=_issue("security", "provider_api_key_leaked"),
            response=response_payload,
        )

    decision, reason_code, blockers, warnings = _decision(response.status_code, response_payload)
    return CompanyProfileExplicitApiLocalSmokeReport(
        contract_version=SMOKE_CONTRACT_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        recommended_next_action=_next_action(decision),
        endpoint=endpoint,
        agent_id=agent_id,
        domain=domain,
        query=query,
        provider_base_url=provider_base_url,
        http_status_code=response.status_code,
        ok=bool(response_payload.get("ok")),
        api_status=_clean(response_payload.get("status")) or None,
        answer_preview=_clean(response_payload.get("answer_preview")),
        citations=_string_list(response_payload.get("citations")),
        document_count=len(response_payload.get("documents") or []),
        blockers=blockers,
        warnings=warnings,
        boundary=dict(response_payload.get("boundary") or {}),
        response=_redact_response(response_payload, provider_api_key),
    )


def export_company_profile_explicit_api_local_smoke(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    **kwargs: Any,
) -> CompanyProfileExplicitApiLocalSmokeReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    report = run_company_profile_explicit_api_local_smoke(**kwargs)
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = CompanyProfileExplicitApiLocalSmokeReport(
        contract_version=report.contract_version,
        generated_at=report.generated_at,
        decision=report.decision,
        reason_code=report.reason_code,
        recommended_next_action=report.recommended_next_action,
        endpoint=report.endpoint,
        agent_id=report.agent_id,
        domain=report.domain,
        query=report.query,
        provider_base_url=report.provider_base_url,
        http_status_code=report.http_status_code,
        ok=report.ok,
        api_status=report.api_status,
        answer_preview=report.answer_preview,
        citations=report.citations,
        document_count=report.document_count,
        blockers=report.blockers,
        warnings=report.warnings,
        boundary=report.boundary,
        response=report.response,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(json.dumps(exported.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_company_profile_explicit_api_local_smoke_markdown(exported), encoding="utf-8")
    return exported


def render_company_profile_explicit_api_local_smoke_markdown(
    report: CompanyProfileExplicitApiLocalSmokeReport,
) -> str:
    lines = [
        "# Company Profile Explicit API Local Smoke",
        "",
        f"- Contract: `{report.contract_version}`",
        f"- Decision: `{report.decision}`",
        f"- Reason: `{report.reason_code}`",
        f"- Next Action: `{report.recommended_next_action}`",
        f"- Endpoint: `{report.endpoint}`",
        f"- Agent: `{report.agent_id}`",
        f"- Domain: `{report.domain}`",
        f"- Provider: `{report.provider_base_url}`",
        f"- Generated At: `{report.generated_at}`",
        "",
        "## Result",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| `http_status_code` | `{report.http_status_code}` |",
        f"| `ok` | `{report.ok}` |",
        f"| `api_status` | `{report.api_status}` |",
        f"| `document_count` | `{report.document_count}` |",
        f"| `citations` | `{json.dumps(report.citations, ensure_ascii=False)}` |",
        "",
        "## Answer Preview",
        "",
        report.answer_preview or "No answer preview.",
        "",
        "## Boundary",
        "",
        "| Boundary | Value |",
        "|---|---|",
    ]
    for key, value in report.boundary.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Blockers", ""])
    lines.append(json.dumps(report.blockers, ensure_ascii=False) if report.blockers else "None.")
    lines.extend(["", "## Warnings", ""])
    lines.append(json.dumps(report.warnings, ensure_ascii=False) if report.warnings else "None.")
    lines.append("")
    return "\n".join(lines)


def _default_client() -> TestClient:
    app = FastAPI()
    app.include_router(domain_agents_router)
    return TestClient(app)


def _decision(status_code: int, payload: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]], list[dict[str, Any]]]:
    boundary = dict(payload.get("boundary") or {})
    blockers = list(payload.get("blockers") or [])
    warnings = list(payload.get("warnings") or [])
    if status_code != 200:
        return "blocked", "explicit_api_http_error", [_issue("explicit_api", "explicit_api_http_error")], warnings
    if boundary.get("default_chat_retrieval_injection") != "disabled":
        return "blocked", "explicit_api_boundary_missing", [_issue("boundary", "explicit_api_boundary_missing")], warnings
    if payload.get("ok") is True and payload.get("status") == "go" and payload.get("citations") and payload.get("documents"):
        return "go", "company_profile_explicit_api_ready", [], warnings
    if payload.get("status") == "blocked" or blockers:
        return "blocked", _clean(payload.get("reason_code")) or "company_profile_explicit_api_blocked", blockers or [_issue("explicit_api", "company_profile_explicit_api_blocked")], warnings
    return "review", _clean(payload.get("reason_code")) or "company_profile_explicit_api_review", blockers, warnings


def _blocked_report(
    *,
    endpoint: str,
    agent_id: str,
    domain: str | None,
    query: str,
    provider_base_url: str,
    http_status_code: int | None,
    reason_code: str,
    blocker: dict[str, Any],
    response: dict[str, Any] | None = None,
) -> CompanyProfileExplicitApiLocalSmokeReport:
    return CompanyProfileExplicitApiLocalSmokeReport(
        contract_version=SMOKE_CONTRACT_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        decision="blocked",
        reason_code=reason_code,
        recommended_next_action=_next_action("blocked"),
        endpoint=endpoint,
        agent_id=agent_id,
        domain=domain,
        query=query,
        provider_base_url=provider_base_url,
        http_status_code=http_status_code,
        ok=False,
        api_status=None,
        answer_preview="",
        blockers=[blocker],
        warnings=[],
        boundary={},
        response=response or {},
    )


def _next_action(decision: str) -> str:
    if decision == "go":
        return "use_explicit_api_for_local_business_trials"
    if decision == "review":
        return "review_explicit_api_smoke_warnings"
    return "fix_provider_or_explicit_api_before_business_use"


def _contains_secret(payload: dict[str, Any], secret: str | None) -> bool:
    if not secret:
        return False
    return secret in json.dumps(payload, ensure_ascii=False)


def _redact_response(payload: dict[str, Any], secret: str | None) -> dict[str, Any]:
    if not secret:
        return payload
    return json.loads(json.dumps(payload, ensure_ascii=False).replace(secret, "[REDACTED]"))


def _issue(component: str, reason_code: str, *, message: str | None = None) -> dict[str, Any]:
    issue = {"component": component, "status": "blocked", "reason_code": reason_code}
    if message:
        issue["message"] = message
    return issue


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clean(item) for item in value if _clean(item)]


def _clean(value: Any) -> str:
    return str(value or "").strip()
