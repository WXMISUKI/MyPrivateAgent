"""Local readiness checks for document-to-RAG trials."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

import httpx

try:
    from backend.capability_runtime.document_rag_upload_to_use_loop import (
        DEFAULT_PROVIDER_PYTHON,
        DEFAULT_PROVIDER_REPO,
    )
    from backend.capability_runtime.local_knowledge_provider_corpus_trial import (
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
    )
    from backend.config import (
        OCR_CAPABILITY_PROVIDER_BASE_URL,
        OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from capability_runtime.document_rag_upload_to_use_loop import (
        DEFAULT_PROVIDER_PYTHON,
        DEFAULT_PROVIDER_REPO,
    )
    from capability_runtime.local_knowledge_provider_corpus_trial import (
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
    )
    from config import (
        OCR_CAPABILITY_PROVIDER_BASE_URL,
        OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
    )


DOCUMENT_RAG_LOCAL_READINESS_ID = "document-rag-local-readiness-v1"
DEFAULT_OUTPUT_DIR = Path("docs/integration/document-rag-local-readiness")
OUTPUT_JSON_FILENAME = "document-rag-local-readiness.json"
OUTPUT_MARKDOWN_FILENAME = "document-rag-local-readiness.md"
PARSER_INGESTION_SCRIPT = Path("scripts/export_parser_artifact_local_ingestion_loop.py")
DEFAULT_OCR_PROFILE = os.getenv("OCR_CAPABILITY_PROVIDER_PROFILE", "unknown")
RECOMMENDED_LARGE_PDF_OCR_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True)
class ReadinessCommandResult:
    ok: bool
    status: str
    reason_code: str
    command: list[str]
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class DocumentRagLocalReadinessCheck:
    id: str
    status: str
    reason_code: str
    endpoint: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DocumentRagLocalReadinessReport:
    id: str
    generated_at: str
    decision: str
    reason_code: str
    ocr_base_url: str
    ocr_profile: str
    ocr_timeout_seconds: float
    provider_base_url: str
    source_id: str | None
    provider_repo_path: Path | None
    provider_python: str
    checks: list[DocumentRagLocalReadinessCheck]
    summary: dict[str, Any]
    recommended_actions: list[str]
    non_goals: list[str]
    json_path: Path | None = None
    markdown_path: Path | None = None


CommandRunner = Callable[..., ReadinessCommandResult]


def export_document_rag_local_readiness(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    ocr_base_url: str = OCR_CAPABILITY_PROVIDER_BASE_URL,
    ocr_profile: str = DEFAULT_OCR_PROFILE,
    ocr_timeout_seconds: float = OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    source_id: str | None = DEFAULT_SOURCE_ID,
    provider_repo_path: Path | None = DEFAULT_PROVIDER_REPO,
    provider_python: str = DEFAULT_PROVIDER_PYTHON,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    transport: httpx.BaseTransport | None = None,
    command_runner: CommandRunner | None = None,
) -> DocumentRagLocalReadinessReport:
    report = build_document_rag_local_readiness(
        ocr_base_url=ocr_base_url,
        ocr_profile=ocr_profile,
        ocr_timeout_seconds=ocr_timeout_seconds,
        provider_base_url=provider_base_url,
        source_id=source_id,
        provider_repo_path=provider_repo_path,
        provider_python=provider_python,
        timeout_seconds=timeout_seconds,
        transport=transport,
        command_runner=command_runner,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = DocumentRagLocalReadinessReport(
        id=report.id,
        generated_at=report.generated_at,
        decision=report.decision,
        reason_code=report.reason_code,
        ocr_base_url=report.ocr_base_url,
        ocr_profile=report.ocr_profile,
        ocr_timeout_seconds=report.ocr_timeout_seconds,
        provider_base_url=report.provider_base_url,
        source_id=report.source_id,
        provider_repo_path=report.provider_repo_path,
        provider_python=report.provider_python,
        checks=report.checks,
        summary=report.summary,
        recommended_actions=report.recommended_actions,
        non_goals=report.non_goals,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(
        json.dumps(document_rag_local_readiness_to_dict(exported), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_document_rag_local_readiness_markdown(exported), encoding="utf-8")
    return exported


def build_document_rag_local_readiness(
    *,
    ocr_base_url: str = OCR_CAPABILITY_PROVIDER_BASE_URL,
    ocr_profile: str = DEFAULT_OCR_PROFILE,
    ocr_timeout_seconds: float = OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    source_id: str | None = DEFAULT_SOURCE_ID,
    provider_repo_path: Path | None = DEFAULT_PROVIDER_REPO,
    provider_python: str = DEFAULT_PROVIDER_PYTHON,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    transport: httpx.BaseTransport | None = None,
    command_runner: CommandRunner | None = None,
) -> DocumentRagLocalReadinessReport:
    normalized_ocr_url = _base_url(ocr_base_url)
    normalized_provider_url = _base_url(provider_base_url)
    normalized_profile = _normalize_profile(ocr_profile)
    runner = command_runner or run_provider_python_version_check
    checks: list[DocumentRagLocalReadinessCheck] = []

    with httpx.Client(timeout=timeout_seconds, transport=transport, trust_env=False) as client:
        checks.append(_ocr_provider_check(client, normalized_ocr_url, normalized_profile, ocr_timeout_seconds))
        checks.extend(_knowledge_provider_checks(client, normalized_provider_url, source_id))

    checks.append(
        _provider_command_check(
            provider_repo_path=provider_repo_path,
            provider_python=provider_python,
            timeout_seconds=timeout_seconds,
            command_runner=runner,
        )
    )
    checks.append(_runtime_boundary_check())

    decision, reason_code = _decision(checks)
    return DocumentRagLocalReadinessReport(
        id=DOCUMENT_RAG_LOCAL_READINESS_ID,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        ocr_base_url=normalized_ocr_url,
        ocr_profile=normalized_profile,
        ocr_timeout_seconds=float(ocr_timeout_seconds),
        provider_base_url=normalized_provider_url,
        source_id=source_id,
        provider_repo_path=provider_repo_path,
        provider_python=provider_python,
        checks=checks,
        summary={
            "final_decision": decision,
            "ready_check_count": sum(1 for check in checks if check.status == "ready"),
            "review_check_count": sum(1 for check in checks if check.status == "review"),
            "blocked_check_count": sum(1 for check in checks if check.status == "blocked"),
            "ocr_profile": normalized_profile,
            "ocr_timeout_seconds": float(ocr_timeout_seconds),
            "large_pdf_timeout_recommendation_seconds": RECOMMENDED_LARGE_PDF_OCR_TIMEOUT_SECONDS,
            "default_chat_retrieval_injection": "not_enabled",
            "source_binding_status": "not_created",
            "document_parse_status": "not_run",
            "provider_ingestion_status": "not_run",
            "service_start_status": "not_started",
            "graph_execution_status": "not_executed",
        },
        recommended_actions=_recommended_actions(decision, checks),
        non_goals=_non_goals(),
    )


def run_provider_python_version_check(
    *,
    provider_python: str,
    provider_repo_path: Path | None,
    timeout_seconds: float,
) -> ReadinessCommandResult:
    command = [*shlex.split(provider_python), "--version"]
    try:
        completed = subprocess.run(
            command,
            cwd=str(provider_repo_path) if provider_repo_path is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return ReadinessCommandResult(
            ok=False,
            status="blocked",
            reason_code="provider_python_command_unavailable",
            command=command,
            stderr=str(exc),
        )
    ok = completed.returncode == 0
    return ReadinessCommandResult(
        ok=ok,
        status="ready" if ok else "blocked",
        reason_code="provider_python_command_ready" if ok else "provider_python_command_failed",
        command=command,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def document_rag_local_readiness_to_dict(report: DocumentRagLocalReadinessReport) -> dict[str, Any]:
    payload = asdict(report)
    if report.provider_repo_path is not None:
        payload["provider_repo_path"] = str(report.provider_repo_path)
    if report.json_path is not None:
        payload["json_path"] = str(report.json_path)
    if report.markdown_path is not None:
        payload["markdown_path"] = str(report.markdown_path)
    return payload


def render_document_rag_local_readiness_markdown(report: DocumentRagLocalReadinessReport) -> str:
    lines = [
        "# Document RAG Local Readiness",
        "",
        f"- Report: `{report.id}`",
        f"- Decision: `{report.decision}`",
        f"- Reason: `{report.reason_code}`",
        f"- Generated At: `{report.generated_at}`",
        f"- OCR Provider: `{report.ocr_base_url}`",
        f"- OCR Profile: `{report.ocr_profile}`",
        f"- OCR Timeout Seconds: `{report.ocr_timeout_seconds}`",
        f"- Knowledge Provider: `{report.provider_base_url}`",
        f"- Source ID: `{report.source_id}`",
        f"- Provider Repo: `{report.provider_repo_path}`",
        "",
        "## Checks",
        "",
        "| Check | Status | Reason | Endpoint | Summary |",
        "|---|---|---|---|---|",
    ]
    for check in report.checks:
        lines.append(
            f"| `{check.id}` | `{check.status}` | `{check.reason_code}` | "
            f"`{check.endpoint or 'n/a'}` | `{_format_value(check.summary)}` |"
        )
    lines.extend(["", "## Summary", "", "| Metric | Value |", "|---|---|"])
    for key, value in report.summary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in report.recommended_actions)
    lines.extend(["", "## Non-Goals", ""])
    lines.extend(f"- {item}" for item in report.non_goals)
    lines.append("")
    return "\n".join(lines)


def _ocr_provider_check(
    client: httpx.Client,
    base_url: str,
    profile: str,
    ocr_timeout_seconds: float,
) -> DocumentRagLocalReadinessCheck:
    endpoint = f"{base_url}/health"
    health = _get_json(client, endpoint)
    if health["status"] != "ready":
        return DocumentRagLocalReadinessCheck(
            id="ocr_provider",
            status="blocked",
            reason_code="ocr_provider_unreachable",
            endpoint=endpoint,
            summary=health,
            recommended_actions=["start_paddleocr_serving", "verify_ocr_provider_base_url"],
        )
    posture = _ocr_posture(profile, ocr_timeout_seconds)
    return DocumentRagLocalReadinessCheck(
        id="ocr_provider",
        status=posture["status"],
        reason_code=posture["reason_code"],
        endpoint=endpoint,
        summary={
            **health,
            "ocr_profile": profile,
            "ocr_timeout_seconds": float(ocr_timeout_seconds),
            "large_pdf_timeout_recommendation_seconds": RECOMMENDED_LARGE_PDF_OCR_TIMEOUT_SECONDS,
        },
        recommended_actions=posture["recommended_actions"],
    )


def _knowledge_provider_checks(
    client: httpx.Client,
    base_url: str,
    source_id: str | None,
) -> list[DocumentRagLocalReadinessCheck]:
    health_endpoint = f"{base_url}/health"
    health = _get_json(client, health_endpoint)
    if health["status"] != "ready":
        return [
            DocumentRagLocalReadinessCheck(
                id="knowledge_provider",
                status="blocked",
                reason_code="knowledge_provider_unreachable",
                endpoint=health_endpoint,
                summary=health,
                recommended_actions=["start_unifiedKnowledgeRAG_provider", "verify_provider_base_url"],
            )
        ]

    catalog_endpoint = f"{base_url}/api/rag/sources"
    catalog = _get_json(client, catalog_endpoint)
    if catalog["status"] != "ready":
        return [
            DocumentRagLocalReadinessCheck(
                id="knowledge_provider",
                status="ready",
                reason_code="knowledge_provider_health_ready",
                endpoint=health_endpoint,
                summary=health,
            ),
            DocumentRagLocalReadinessCheck(
                id="knowledge_source_catalog",
                status="blocked",
                reason_code="knowledge_provider_unreachable",
                endpoint=catalog_endpoint,
                summary=catalog,
                recommended_actions=["verify_rag_source_catalog_endpoint"],
            ),
        ]
    source_ids = _extract_source_ids(catalog.get("raw"))
    if source_id and source_id not in source_ids:
        return [
            DocumentRagLocalReadinessCheck(
                id="knowledge_provider",
                status="ready",
                reason_code="knowledge_provider_health_ready",
                endpoint=health_endpoint,
                summary=health,
            ),
            DocumentRagLocalReadinessCheck(
                id="knowledge_source_catalog",
                status="review",
                reason_code="source_not_visible",
                endpoint=catalog_endpoint,
                summary={"source_id": source_id, "visible_source_ids": source_ids},
                recommended_actions=["run_provider_parser_artifact_ingestion_or_select_existing_source"],
            ),
        ]
    return [
        DocumentRagLocalReadinessCheck(
            id="knowledge_provider",
            status="ready",
            reason_code="knowledge_provider_health_ready",
            endpoint=health_endpoint,
            summary=health,
        ),
        DocumentRagLocalReadinessCheck(
            id="knowledge_source_catalog",
            status="ready",
            reason_code="source_visible" if source_id else "source_check_skipped",
            endpoint=catalog_endpoint,
            summary={"source_id": source_id, "visible_source_ids": source_ids},
        ),
    ]


def _provider_command_check(
    *,
    provider_repo_path: Path | None,
    provider_python: str,
    timeout_seconds: float,
    command_runner: CommandRunner,
) -> DocumentRagLocalReadinessCheck:
    if provider_repo_path is None:
        return DocumentRagLocalReadinessCheck(
            id="provider_ingestion_command",
            status="blocked",
            reason_code="provider_repo_path_missing",
            recommended_actions=["configure_knowledge_provider_repo"],
        )
    repo = provider_repo_path.expanduser()
    if not repo.exists():
        return DocumentRagLocalReadinessCheck(
            id="provider_ingestion_command",
            status="blocked",
            reason_code="provider_repo_path_missing",
            endpoint=str(repo),
            recommended_actions=["verify_knowledge_provider_repo_path"],
        )
    script = repo / PARSER_INGESTION_SCRIPT
    if not script.exists():
        return DocumentRagLocalReadinessCheck(
            id="provider_ingestion_command",
            status="blocked",
            reason_code="parser_artifact_ingestion_script_missing",
            endpoint=str(script),
            recommended_actions=["update_unifiedKnowledgeRAG_or_verify_script_path"],
        )
    result = command_runner(
        provider_python=provider_python,
        provider_repo_path=repo,
        timeout_seconds=timeout_seconds,
    )
    return DocumentRagLocalReadinessCheck(
        id="provider_ingestion_command",
        status=result.status,
        reason_code=result.reason_code,
        endpoint=str(script),
        summary={
            "provider_repo_path": str(repo),
            "provider_python": provider_python,
            "command": result.command,
            "return_code": result.return_code,
            "stdout": _truncate(result.stdout),
            "stderr": _truncate(result.stderr),
        },
        recommended_actions=[] if result.ok else ["verify_GRAPHRAG_environment_and_provider_python_command"],
    )


def _runtime_boundary_check() -> DocumentRagLocalReadinessCheck:
    return DocumentRagLocalReadinessCheck(
        id="runtime_boundaries",
        status="ready",
        reason_code="side_effect_free_readiness_only",
        summary={
            "document_parse_status": "not_run",
            "provider_ingestion_status": "not_run",
            "service_start_status": "not_started",
            "default_chat_retrieval_injection": "not_enabled",
            "source_binding_status": "not_created",
            "memory_audit_governance_write_status": "not_written",
            "graph_execution_status": "not_executed",
        },
    )


def _get_json(client: httpx.Client, endpoint: str) -> dict[str, Any]:
    try:
        response = client.get(endpoint)
        response.raise_for_status()
        raw = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"status": "blocked", "error": str(exc), "raw": {}}
    status = _ready_status(raw)
    return {"status": status, "raw": raw}


def _ready_status(raw: Any) -> str:
    if not isinstance(raw, dict):
        return "blocked"
    status = str(raw.get("status") or raw.get("readiness") or "").lower()
    if status in {"ok", "ready", "healthy"}:
        return "ready"
    if raw.get("errorCode") in (0, "0"):
        return "ready"
    if "sources" in raw or "items" in raw or "data" in raw or "knowledge_bases" in raw:
        return "ready"
    return "blocked"


def _extract_source_ids(raw: Any) -> list[str]:
    candidates: list[Any] = []
    if isinstance(raw, dict):
        for key in ("sources", "items", "data", "knowledge_bases"):
            value = raw.get(key)
            if isinstance(value, list):
                candidates.extend(value)
        if isinstance(raw.get("source_ids"), list):
            candidates.extend(str(item) for item in raw["source_ids"])
    elif isinstance(raw, list):
        candidates = raw
    ids: list[str] = []
    for item in candidates:
        if isinstance(item, str):
            ids.append(item)
        elif isinstance(item, dict):
            source_id = item.get("source_id") or item.get("id") or item.get("name")
            if source_id:
                ids.append(str(source_id))
    return sorted(set(ids))


def _ocr_posture(profile: str, timeout_seconds: float) -> dict[str, Any]:
    actions: list[str] = []
    status = "ready"
    reason_code = "ocr_profile_ready"
    if profile == "unknown":
        status = "review"
        reason_code = "ocr_profile_unknown"
        actions.append("set_ocr_profile_cpu_or_gpu_for_local_readiness")
    if profile == "cpu":
        status = "review"
        reason_code = "ocr_cpu_profile_large_pdf_review"
        actions.append("consider_gpu_ocr_for_large_pdf_trials")
    if timeout_seconds < RECOMMENDED_LARGE_PDF_OCR_TIMEOUT_SECONDS:
        status = "review"
        reason_code = "ocr_timeout_below_large_pdf_recommendation"
        actions.append("increase_OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS_for_large_pdfs")
    if profile == "gpu":
        actions.append("use_gpu_ocr_service_endpoint_for_large_pdf_trials")
    return {"status": status, "reason_code": reason_code, "recommended_actions": actions}


def _decision(checks: list[DocumentRagLocalReadinessCheck]) -> tuple[str, str]:
    blocked = next((check for check in checks if check.status == "blocked"), None)
    if blocked is not None:
        return "blocked", blocked.reason_code
    review = next((check for check in checks if check.status == "review"), None)
    if review is not None:
        return "review", review.reason_code
    return "go", "document_rag_local_readiness_ready"


def _recommended_actions(decision: str, checks: list[DocumentRagLocalReadinessCheck]) -> list[str]:
    actions: list[str] = []
    for check in checks:
        actions.extend(check.recommended_actions)
    if decision == "go":
        actions.insert(0, "run_document_rag_upload_to_use_loop_for_real_document")
    elif decision == "review":
        actions.insert(0, "review_local_readiness_warnings_before_large_pdf_trial")
    else:
        actions.insert(0, "fix_blocking_local_readiness_check_before_document_trial")
    return list(dict.fromkeys(actions))


def _non_goals() -> list[str]:
    return [
        "does_not_upload_parse_or_ingest_documents",
        "does_not_start_external_services",
        "does_not_enable_default_chat_retrieval_injection",
        "does_not_create_source_to_agent_binding",
        "does_not_write_memory_audit_approval_or_governance_records",
        "does_not_execute_graphrag",
        "does_not_add_frontend_document_management_ui",
    ]


def _base_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _normalize_profile(value: str) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in {"cpu", "gpu"} else "unknown"


def _truncate(value: str, limit: int = 500) -> str:
    compact = " ".join(str(value or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
