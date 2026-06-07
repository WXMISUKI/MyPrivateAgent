"""Local document-to-RAG upload-to-use trial loop."""

from __future__ import annotations

import base64
import json
import mimetypes
import shlex
import subprocess
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

try:
    from backend.capability_runtime.local_knowledge_provider_corpus_trial import (
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
        DEFAULT_TOP_K,
        export_local_knowledge_provider_corpus_trial,
    )
    from backend.services.document_ingestion_service import (
        DocumentIngestionService,
        get_document_ingestion_service,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from capability_runtime.local_knowledge_provider_corpus_trial import (
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
        DEFAULT_TOP_K,
        export_local_knowledge_provider_corpus_trial,
    )
    from services.document_ingestion_service import (
        DocumentIngestionService,
        get_document_ingestion_service,
    )


DOCUMENT_RAG_UPLOAD_TO_USE_LOOP_ID = "document-rag-upload-to-use-loop-v1"
DEFAULT_OUTPUT_DIR = Path("docs/integration/document-rag-upload-to-use-loop")
OUTPUT_JSON_FILENAME = "document-rag-upload-to-use-loop.json"
OUTPUT_MARKDOWN_FILENAME = "document-rag-upload-to-use-loop.md"
PARSER_ARTIFACT_FILENAME = "document-rag-parser-artifact.json"
DEFAULT_PROVIDER_REPO = Path(r"D:\AI\AIcode\unifiedKnowledgeRAG")
DEFAULT_PROVIDER_PYTHON = "conda run -n GRAPHRAG python"
DEFAULT_PARSE_MODE = "ocr"
DEFAULT_TITLE = "公司简介 2025 trial"
DEFAULT_QUERY = "公司主营业务和服务范围是什么？"


@dataclass(frozen=True)
class ProviderIngestionCommandResult:
    ok: bool
    status: str
    reason_code: str
    command: list[str]
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class DocumentRagUploadToUseStep:
    id: str
    status: str
    reason_code: str
    artifacts: dict[str, str | None]
    summary: dict[str, Any]


@dataclass(frozen=True)
class DocumentRagUploadToUseReport:
    id: str
    generated_at: str
    decision: str
    reason_code: str
    document_path: Path
    parse_mode: str
    source_id: str
    title: str
    query: str
    provider_base_url: str
    provider_repo_path: Path | None
    handoff_only: bool
    ingestion: dict[str, Any]
    parser_artifact_path: Path | None
    provider_ingestion: dict[str, Any]
    corpus_trial: dict[str, Any]
    steps: list[DocumentRagUploadToUseStep]
    summary: dict[str, Any]
    recommended_actions: list[str]
    non_goals: list[str]
    json_path: Path | None = None
    markdown_path: Path | None = None


def export_document_rag_upload_to_use_loop(
    *,
    document_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    parse_mode: str = DEFAULT_PARSE_MODE,
    source_id: str = DEFAULT_SOURCE_ID,
    title: str = DEFAULT_TITLE,
    query: str = DEFAULT_QUERY,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    provider_repo_path: Path | None = DEFAULT_PROVIDER_REPO,
    provider_python: str = DEFAULT_PROVIDER_PYTHON,
    top_k: int = DEFAULT_TOP_K,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_pages: int | None = 5,
    handoff_only: bool = False,
    document_ingestion_service: DocumentIngestionService | Any | None = None,
    provider_ingestion_runner: Callable[..., ProviderIngestionCommandResult] | None = None,
    corpus_trial_exporter: Callable[..., Any] = export_local_knowledge_provider_corpus_trial,
) -> DocumentRagUploadToUseReport:
    report = build_document_rag_upload_to_use_loop(
        document_path=document_path,
        output_dir=output_dir,
        parse_mode=parse_mode,
        source_id=source_id,
        title=title,
        query=query,
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        provider_repo_path=provider_repo_path,
        provider_python=provider_python,
        top_k=top_k,
        timeout_seconds=timeout_seconds,
        max_pages=max_pages,
        handoff_only=handoff_only,
        document_ingestion_service=document_ingestion_service,
        provider_ingestion_runner=provider_ingestion_runner,
        corpus_trial_exporter=corpus_trial_exporter,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / OUTPUT_JSON_FILENAME
    markdown_path = output_dir / OUTPUT_MARKDOWN_FILENAME
    exported = DocumentRagUploadToUseReport(
        id=report.id,
        generated_at=report.generated_at,
        decision=report.decision,
        reason_code=report.reason_code,
        document_path=report.document_path,
        parse_mode=report.parse_mode,
        source_id=report.source_id,
        title=report.title,
        query=report.query,
        provider_base_url=report.provider_base_url,
        provider_repo_path=report.provider_repo_path,
        handoff_only=report.handoff_only,
        ingestion=report.ingestion,
        parser_artifact_path=report.parser_artifact_path,
        provider_ingestion=report.provider_ingestion,
        corpus_trial=report.corpus_trial,
        steps=report.steps,
        summary=report.summary,
        recommended_actions=report.recommended_actions,
        non_goals=report.non_goals,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    json_path.write_text(
        json.dumps(document_rag_upload_to_use_loop_to_dict(exported), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_document_rag_upload_to_use_loop_markdown(exported), encoding="utf-8")
    return exported


def build_document_rag_upload_to_use_loop(
    *,
    document_path: Path,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    parse_mode: str = DEFAULT_PARSE_MODE,
    source_id: str = DEFAULT_SOURCE_ID,
    title: str = DEFAULT_TITLE,
    query: str = DEFAULT_QUERY,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    provider_repo_path: Path | None = DEFAULT_PROVIDER_REPO,
    provider_python: str = DEFAULT_PROVIDER_PYTHON,
    top_k: int = DEFAULT_TOP_K,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_pages: int | None = 5,
    handoff_only: bool = False,
    document_ingestion_service: DocumentIngestionService | Any | None = None,
    provider_ingestion_runner: Callable[..., ProviderIngestionCommandResult] | None = None,
    corpus_trial_exporter: Callable[..., Any] = export_local_knowledge_provider_corpus_trial,
) -> DocumentRagUploadToUseReport:
    output_dir.mkdir(parents=True, exist_ok=True)
    steps: list[DocumentRagUploadToUseStep] = []
    normalized_document_path = document_path.expanduser()
    if not normalized_document_path.exists():
        return _report(
            decision="blocked",
            reason_code="document_file_missing",
            document_path=normalized_document_path,
            parse_mode=parse_mode,
            source_id=source_id,
            title=title,
            query=query,
            provider_base_url=provider_base_url,
            provider_repo_path=provider_repo_path,
            handoff_only=handoff_only,
            ingestion={},
            parser_artifact_path=None,
            provider_ingestion={},
            corpus_trial={},
            steps=steps,
            summary={"input_status": "missing"},
        )

    service = document_ingestion_service or get_document_ingestion_service()
    ingestion_record = service.submit(
        _document_ingestion_request(
            document_path=normalized_document_path,
            parse_mode=parse_mode,
            max_pages=max_pages,
        )
    ).metadata
    ingestion_summary = _ingestion_summary(ingestion_record)
    steps.append(
        DocumentRagUploadToUseStep(
            id="document_ingestion",
            status=str(ingestion_record.get("status") or "unknown"),
            reason_code="document_ingestion_succeeded"
            if ingestion_record.get("status") == "succeeded"
            else "document_ingestion_not_succeeded",
            artifacts={"artifact_id": str(ingestion_record.get("artifact_id") or "") or None},
            summary=ingestion_summary,
        )
    )
    if ingestion_record.get("status") != "succeeded":
        return _report(
            decision="blocked",
            reason_code="document_ingestion_not_succeeded",
            document_path=normalized_document_path,
            parse_mode=parse_mode,
            source_id=source_id,
            title=title,
            query=query,
            provider_base_url=provider_base_url,
            provider_repo_path=provider_repo_path,
            handoff_only=handoff_only,
            ingestion=ingestion_summary,
            parser_artifact_path=None,
            provider_ingestion={},
            corpus_trial={},
            steps=steps,
            summary={"document_ingestion_status": ingestion_record.get("status")},
        )

    result = service.get_result(str(ingestion_record["ingest_id"]))
    payload = result.get("payload") if isinstance(result.get("payload"), dict) else {}
    text_blocks = _text_blocks_from_payload(payload, source_id=source_id)
    if not text_blocks:
        return _report(
            decision="blocked",
            reason_code="document_artifact_has_no_rag_text",
            document_path=normalized_document_path,
            parse_mode=parse_mode,
            source_id=source_id,
            title=title,
            query=query,
            provider_base_url=provider_base_url,
            provider_repo_path=provider_repo_path,
            handoff_only=handoff_only,
            ingestion=ingestion_summary,
            parser_artifact_path=None,
            provider_ingestion={},
            corpus_trial={},
            steps=steps,
            summary={"text_block_count": 0},
        )

    parser_artifact_path = output_dir / "parser-artifacts" / PARSER_ARTIFACT_FILENAME
    parser_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    parser_artifact = _parser_artifact_payload(
        document_path=normalized_document_path,
        source_id=source_id,
        title=title,
        parse_mode=parse_mode,
        ingestion=ingestion_record,
        text_blocks=text_blocks,
    )
    parser_artifact_path.write_text(json.dumps(parser_artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    steps.append(
        DocumentRagUploadToUseStep(
            id="rag_handoff_artifact",
            status="ready",
            reason_code="normalized_parser_artifact_written",
            artifacts={"parser_artifact": str(parser_artifact_path)},
            summary={
                "artifact_id": parser_artifact["artifact_id"],
                "text_block_count": len(text_blocks),
            },
        )
    )
    if handoff_only:
        return _report(
            decision="review",
            reason_code="provider_ingestion_not_run_handoff_only",
            document_path=normalized_document_path,
            parse_mode=parse_mode,
            source_id=source_id,
            title=title,
            query=query,
            provider_base_url=provider_base_url,
            provider_repo_path=provider_repo_path,
            handoff_only=True,
            ingestion=ingestion_summary,
            parser_artifact_path=parser_artifact_path,
            provider_ingestion={"status": "skipped", "reason_code": "handoff_only"},
            corpus_trial={},
            steps=steps,
            summary={"text_block_count": len(text_blocks), "provider_ingestion_status": "skipped"},
        )

    runner = provider_ingestion_runner or run_provider_parser_artifact_ingestion_command
    command_result = runner(
        artifact_path=parser_artifact_path,
        provider_repo_path=provider_repo_path,
        provider_python=provider_python,
        output_dir=output_dir / "provider-parser-artifact-ingestion-loop",
        query=query,
        top_k=top_k,
        timeout_seconds=timeout_seconds,
    )
    provider_ingestion = provider_ingestion_command_result_to_dict(command_result)
    steps.append(
        DocumentRagUploadToUseStep(
            id="provider_parser_artifact_ingestion",
            status=command_result.status,
            reason_code=command_result.reason_code,
            artifacts={},
            summary={
                "return_code": command_result.return_code,
                "stdout_preview": _truncate(command_result.stdout),
                "stderr_preview": _truncate(command_result.stderr),
            },
        )
    )
    if not command_result.ok:
        return _report(
            decision="blocked",
            reason_code="provider_ingestion_command_failed",
            document_path=normalized_document_path,
            parse_mode=parse_mode,
            source_id=source_id,
            title=title,
            query=query,
            provider_base_url=provider_base_url,
            provider_repo_path=provider_repo_path,
            handoff_only=False,
            ingestion=ingestion_summary,
            parser_artifact_path=parser_artifact_path,
            provider_ingestion=provider_ingestion,
            corpus_trial={},
            steps=steps,
            summary={"provider_ingestion_status": command_result.status},
        )

    trial = corpus_trial_exporter(
        output_dir=output_dir / "local-knowledge-provider-corpus-trial",
        provider_base_url=provider_base_url,
        provider_api_key=provider_api_key,
        source_id=source_id,
        top_k=top_k,
        timeout_seconds=timeout_seconds,
    )
    corpus_trial = _corpus_trial_summary(trial)
    trial_decision = str(getattr(trial, "decision", "") or "blocked")
    trial_reason = str(getattr(trial, "reason_code", "") or "corpus_trial_unknown")
    steps.append(
        DocumentRagUploadToUseStep(
            id="local_knowledge_provider_corpus_trial",
            status=trial_decision,
            reason_code=trial_reason,
            artifacts={
                "json": _path_string(getattr(trial, "json_path", None)),
                "markdown": _path_string(getattr(trial, "markdown_path", None)),
            },
            summary=dict(getattr(trial, "summary", {}) or {}),
        )
    )
    if trial_decision == "go":
        decision = "go"
        reason_code = "document_rag_upload_to_use_ready"
    elif trial_decision == "review":
        decision = "review"
        reason_code = f"corpus_trial_{trial_reason}"
    else:
        decision = "blocked"
        reason_code = f"corpus_trial_{trial_reason}"
    return _report(
        decision=decision,
        reason_code=reason_code,
        document_path=normalized_document_path,
        parse_mode=parse_mode,
        source_id=source_id,
        title=title,
        query=query,
        provider_base_url=provider_base_url,
        provider_repo_path=provider_repo_path,
        handoff_only=False,
        ingestion=ingestion_summary,
        parser_artifact_path=parser_artifact_path,
        provider_ingestion=provider_ingestion,
        corpus_trial=corpus_trial,
        steps=steps,
        summary={
            "text_block_count": len(text_blocks),
            "provider_ingestion_status": command_result.status,
            "corpus_trial_decision": trial_decision,
            "corpus_trial_reason_code": trial_reason,
        },
    )


def run_provider_parser_artifact_ingestion_command(
    *,
    artifact_path: Path,
    provider_repo_path: Path | None,
    provider_python: str,
    output_dir: Path,
    query: str,
    top_k: int,
    timeout_seconds: float,
) -> ProviderIngestionCommandResult:
    if provider_repo_path is None or not provider_repo_path.exists():
        return ProviderIngestionCommandResult(
            ok=False,
            status="blocked",
            reason_code="provider_repo_missing",
            command=[],
            stderr=f"Provider repo not found: {provider_repo_path}",
        )
    script_path = provider_repo_path / "scripts" / "export_parser_artifact_local_ingestion_loop.py"
    if not script_path.exists():
        return ProviderIngestionCommandResult(
            ok=False,
            status="blocked",
            reason_code="provider_ingestion_script_missing",
            command=[],
            stderr=f"Provider ingestion script not found: {script_path}",
        )
    command = [
        *shlex.split(provider_python),
        str(script_path),
        "--artifact-path",
        str(artifact_path.resolve()),
        "--output-dir",
        str(output_dir),
        "--query",
        query,
        "--top-k",
        str(top_k),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=provider_repo_path,
            text=True,
            capture_output=True,
            timeout=max(1.0, float(timeout_seconds)),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ProviderIngestionCommandResult(
            ok=False,
            status="blocked",
            reason_code="provider_ingestion_command_failed",
            command=command,
            stderr=str(exc),
        )
    return ProviderIngestionCommandResult(
        ok=completed.returncode == 0,
        status="ready" if completed.returncode == 0 else "blocked",
        reason_code="provider_ingestion_command_ready"
        if completed.returncode == 0
        else "provider_ingestion_command_failed",
        command=command,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def document_rag_upload_to_use_loop_to_dict(report: DocumentRagUploadToUseReport) -> dict[str, Any]:
    payload = asdict(report)
    for key in ["document_path", "provider_repo_path", "parser_artifact_path", "json_path", "markdown_path"]:
        if payload[key] is not None:
            payload[key] = str(payload[key])
    return payload


def provider_ingestion_command_result_to_dict(result: ProviderIngestionCommandResult) -> dict[str, Any]:
    return asdict(result)


def render_document_rag_upload_to_use_loop_markdown(report: DocumentRagUploadToUseReport) -> str:
    lines = [
        "# Document RAG Upload-To-Use Loop",
        "",
        f"- Report: `{report.id}`",
        f"- Decision: `{report.decision}`",
        f"- Reason: `{report.reason_code}`",
        f"- Generated At: `{report.generated_at}`",
        f"- Document Path: `{report.document_path}`",
        f"- Parse Mode: `{report.parse_mode}`",
        f"- Source ID: `{report.source_id}`",
        f"- Provider Base URL: `{report.provider_base_url}`",
        f"- Parser Artifact: `{report.parser_artifact_path}`",
        "",
        "## Steps",
        "",
        "| Step | Status | Reason | Artifacts |",
        "|---|---|---|---|",
    ]
    for step in report.steps:
        artifacts = ", ".join(f"{key}={value}" for key, value in step.artifacts.items() if value) or "n/a"
        lines.append(f"| `{step.id}` | `{step.status}` | `{step.reason_code}` | `{artifacts}` |")
    lines.extend(["", "## Summary", "", "| Metric | Value |", "|---|---|"])
    for key, value in report.summary.items():
        lines.append(f"| `{key}` | `{_format_value(value)}` |")
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in report.recommended_actions)
    lines.extend(["", "## Non-Goals", ""])
    lines.extend(f"- {item}" for item in report.non_goals)
    lines.append("")
    return "\n".join(lines)


def _document_ingestion_request(*, document_path: Path, parse_mode: str, max_pages: int | None) -> dict[str, Any]:
    payload = {
        "parse_mode": parse_mode,
        "file_base64": base64.b64encode(document_path.read_bytes()).decode("ascii"),
        "media_type": _media_type(document_path),
        "filename": document_path.name,
    }
    if parse_mode == "layout":
        payload.update({"output_format": "markdown", "include_tables": True, "include_layout": True})
    if max_pages is not None and parse_mode in {"layout", "vlm_async"}:
        payload["max_pages"] = max_pages
    return payload


def _media_type(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return "application/pdf"
    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"


def _ingestion_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "ingest_id": record.get("ingest_id"),
        "status": record.get("status"),
        "parse_mode": record.get("parse_mode"),
        "capability_id": record.get("capability_id"),
        "provider": record.get("provider"),
        "artifact_id": record.get("artifact_id"),
        "warnings": record.get("warnings") if isinstance(record.get("warnings"), list) else [],
        "error": record.get("error") if isinstance(record.get("error"), dict) else {},
    }


def _parser_artifact_payload(
    *,
    document_path: Path,
    source_id: str,
    title: str,
    parse_mode: str,
    ingestion: dict[str, Any],
    text_blocks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "artifact_id": f"{_safe_id(source_id)}_{parse_mode}_document_upload",
        "source_id": source_id,
        "title": title,
        "owner": "myprivateagent_document_rag_upload_to_use_loop",
        "domain": "local_business_corpus",
        "language": "zh-CN",
        "sensitivity": "local_private_trial",
        "original_file": {
            "path": str(document_path),
            "name": document_path.name,
            "sha256": sha256(document_path.read_bytes()).hexdigest(),
            "page_range": "unknown",
        },
        "parser": {
            "parser_id": f"myprivateagent-{parse_mode}-artifact-handoff-v1",
            "parser_version": "local-trial",
            "parsed_at": datetime.now(UTC).isoformat(),
            "document_ingest_id": ingestion.get("ingest_id"),
            "document_artifact_id": ingestion.get("artifact_id"),
            "capability_id": ingestion.get("capability_id"),
            "provider": ingestion.get("provider"),
        },
        "text_blocks": text_blocks,
    }


def _text_blocks_from_payload(payload: dict[str, Any], *, source_id: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    raw_blocks = payload.get("blocks")
    if isinstance(raw_blocks, list):
        for offset, block in enumerate(raw_blocks, start=1):
            if not isinstance(block, dict):
                continue
            text = str(block.get("text") or "").strip()
            if not text:
                continue
            page = _positive_int(block.get("page_number") or block.get("page") or block.get("provenance", {}).get("page")) or 1
            blocks.append(_text_block(source_id, page, offset, text))
    if blocks:
        return blocks

    pages = payload.get("pages")
    if isinstance(pages, list):
        for offset, page_payload in enumerate(pages, start=1):
            if not isinstance(page_payload, dict):
                continue
            text = str(page_payload.get("text") or page_payload.get("markdown") or "").strip()
            if not text:
                continue
            page = _positive_int(page_payload.get("page_number") or page_payload.get("page")) or offset
            blocks.append(_text_block(source_id, page, 1, text))
    markdown = str(payload.get("markdown") or "").strip()
    if markdown:
        blocks.append(_text_block(source_id, 1, len(blocks) + 1, markdown))
    text = str(payload.get("text") or "").strip()
    if text:
        blocks.append(_text_block(source_id, 1, len(blocks) + 1, text))
    return blocks


def _text_block(source_id: str, page: int, offset: int, text: str) -> dict[str, Any]:
    return {
        "block_id": f"page-{page}-block-{offset}",
        "text": text,
        "citation": f"{source_id}#page-{page}",
        "provenance": {"page": page},
    }


def _corpus_trial_summary(trial: Any) -> dict[str, Any]:
    return {
        "decision": getattr(trial, "decision", None),
        "reason_code": getattr(trial, "reason_code", None),
        "source_id": getattr(trial, "source_id", None),
        "provider_base_url": getattr(trial, "provider_base_url", None),
        "json_path": _path_string(getattr(trial, "json_path", None)),
        "markdown_path": _path_string(getattr(trial, "markdown_path", None)),
        "summary": dict(getattr(trial, "summary", {}) or {}),
    }


def _report(
    *,
    decision: str,
    reason_code: str,
    document_path: Path,
    parse_mode: str,
    source_id: str,
    title: str,
    query: str,
    provider_base_url: str,
    provider_repo_path: Path | None,
    handoff_only: bool,
    ingestion: dict[str, Any],
    parser_artifact_path: Path | None,
    provider_ingestion: dict[str, Any],
    corpus_trial: dict[str, Any],
    steps: list[DocumentRagUploadToUseStep],
    summary: dict[str, Any],
) -> DocumentRagUploadToUseReport:
    return DocumentRagUploadToUseReport(
        id=DOCUMENT_RAG_UPLOAD_TO_USE_LOOP_ID,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        document_path=document_path,
        parse_mode=parse_mode,
        source_id=source_id,
        title=title,
        query=query,
        provider_base_url=provider_base_url.rstrip("/"),
        provider_repo_path=provider_repo_path,
        handoff_only=handoff_only,
        ingestion=ingestion,
        parser_artifact_path=parser_artifact_path,
        provider_ingestion=provider_ingestion,
        corpus_trial=corpus_trial,
        steps=steps,
        summary={
            "final_decision": decision,
            "default_chat_retrieval_injection": "not_enabled",
            "source_binding_status": "not_created",
            "memory_write_status": "not_written",
            "audit_write_status": "not_written",
            "service_start_status": "not_started",
            "graph_execution_status": "not_executed",
            **summary,
        },
        recommended_actions=_recommended_actions(decision, reason_code),
        non_goals=_non_goals(),
    )


def _recommended_actions(decision: str, reason_code: str) -> list[str]:
    if decision == "go":
        return [
            "use_generated_source_id_for_explicit_local_rag_questions",
            "productize_http_knowledge_document_ingest_only_after_repeated_go_trials",
        ]
    if reason_code == "provider_ingestion_not_run_handoff_only":
        return ["run_provider_parser_artifact_ingestion_command", "rerun_without_handoff_only"]
    if reason_code == "document_artifact_has_no_rag_text":
        return ["review_document_parser_output", "try_layout_parse_or_smaller_document_slice"]
    if reason_code == "provider_ingestion_command_failed":
        return ["check_unifiedKnowledgeRAG_repo_path_and_GRAPHRAG_env", "rerun_provider_ingestion_command"]
    if decision == "review":
        return ["review_corpus_trial_warnings", "adjust_document_parse_or_trial_questions"]
    return ["inspect_blocking_reason", "rerun_document_rag_upload_to_use_loop_after_fix"]


def _non_goals() -> list[str]:
    return [
        "does_not_enable_default_chat_retrieval_injection",
        "does_not_create_source_to_agent_binding",
        "does_not_mutate_domain_agent_manifests",
        "does_not_write_memory_audit_approval_or_governance_records",
        "does_not_start_paddleocr_or_unifiedknowledgerag_services",
        "does_not_promote_retrieval_backends",
        "does_not_execute_graphrag",
        "does_not_add_frontend_upload_ui",
    ]


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.strip()) or "document_rag_source"


def _positive_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _path_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _truncate(value: str, limit: int = 500) -> str:
    compact = " ".join(str(value or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
