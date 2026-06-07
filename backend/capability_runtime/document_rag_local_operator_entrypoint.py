"""Local operator entrypoint for document RAG trials."""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable

try:
    from backend.capability_runtime.document_rag_local_readiness import (
        DEFAULT_OUTPUT_DIR as DEFAULT_READINESS_OUTPUT_DIR,
        DEFAULT_OCR_PROFILE,
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_PROVIDER_PYTHON,
        DEFAULT_PROVIDER_REPO,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
        OCR_CAPABILITY_PROVIDER_BASE_URL,
        OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        DocumentRagLocalReadinessReport,
        document_rag_local_readiness_to_dict,
        export_document_rag_local_readiness,
    )
    from backend.capability_runtime.document_rag_upload_to_use_loop import (
        DEFAULT_OUTPUT_DIR as DEFAULT_UPLOAD_OUTPUT_DIR,
        DEFAULT_PARSE_MODE,
        DEFAULT_QUERY,
        DEFAULT_TITLE,
        DEFAULT_TOP_K,
        DocumentRagUploadToUseReport,
        document_rag_upload_to_use_loop_to_dict,
        export_document_rag_upload_to_use_loop,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from capability_runtime.document_rag_local_readiness import (
        DEFAULT_OUTPUT_DIR as DEFAULT_READINESS_OUTPUT_DIR,
        DEFAULT_OCR_PROFILE,
        DEFAULT_PROVIDER_BASE_URL,
        DEFAULT_PROVIDER_PYTHON,
        DEFAULT_PROVIDER_REPO,
        DEFAULT_SOURCE_ID,
        DEFAULT_TIMEOUT_SECONDS,
        OCR_CAPABILITY_PROVIDER_BASE_URL,
        OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
        DocumentRagLocalReadinessReport,
        document_rag_local_readiness_to_dict,
        export_document_rag_local_readiness,
    )
    from capability_runtime.document_rag_upload_to_use_loop import (
        DEFAULT_OUTPUT_DIR as DEFAULT_UPLOAD_OUTPUT_DIR,
        DEFAULT_PARSE_MODE,
        DEFAULT_QUERY,
        DEFAULT_TITLE,
        DEFAULT_TOP_K,
        DocumentRagUploadToUseReport,
        document_rag_upload_to_use_loop_to_dict,
        export_document_rag_upload_to_use_loop,
    )


DOCUMENT_RAG_LOCAL_OPERATOR_ENTRYPOINT_ID = "document-rag-local-operator-entrypoint-v1"
DEFAULT_OPERATOR_OUTPUT_DIR = Path("docs/integration/document-rag-local-operator-entrypoint")
DEFAULT_OPERATOR_UPLOAD_DIR = Path(".myagent/document-rag-operator-uploads")


@dataclass(frozen=True)
class DocumentRagLocalOperatorResult:
    id: str
    generated_at: str
    decision: str
    reason_code: str
    readiness: dict[str, Any]
    upload_to_use: dict[str, Any]
    summary: dict[str, Any]
    recommended_actions: list[str]
    non_goals: list[str]


@dataclass(frozen=True)
class DocumentRagOperatorUploadMaterialization:
    filename: str
    media_type: str
    document_path: Path
    sha256: str
    byte_size: int


ReadinessExporter = Callable[..., DocumentRagLocalReadinessReport]
UploadToUseExporter = Callable[..., DocumentRagUploadToUseReport]


def materialize_document_rag_operator_upload(
    *,
    file_base64: str,
    filename: str,
    media_type: str,
    upload_dir: Path = DEFAULT_OPERATOR_UPLOAD_DIR,
) -> DocumentRagOperatorUploadMaterialization:
    encoded = str(file_base64 or "").strip()
    if not encoded:
        raise ValueError("file_base64 is required.")
    if "," in encoded and encoded.lower().startswith("data:"):
        encoded = encoded.split(",", 1)[1]
    try:
        content = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("file_base64 must be valid base64.") from exc
    if not content:
        raise ValueError("uploaded file is empty.")

    safe_name = _safe_upload_filename(filename)
    digest = sha256(content).hexdigest()
    upload_dir.mkdir(parents=True, exist_ok=True)
    document_path = upload_dir / f"{digest[:12]}-{safe_name}"
    document_path.write_bytes(content)
    return DocumentRagOperatorUploadMaterialization(
        filename=safe_name,
        media_type=str(media_type or "application/octet-stream"),
        document_path=document_path,
        sha256=digest,
        byte_size=len(content),
    )


def run_document_rag_local_readiness_entrypoint(
    *,
    ocr_base_url: str = OCR_CAPABILITY_PROVIDER_BASE_URL,
    ocr_profile: str = DEFAULT_OCR_PROFILE,
    ocr_timeout_seconds: float = OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    source_id: str | None = DEFAULT_SOURCE_ID,
    provider_repo_path: Path | None = DEFAULT_PROVIDER_REPO,
    provider_python: str = DEFAULT_PROVIDER_PYTHON,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    output_dir: Path = DEFAULT_READINESS_OUTPUT_DIR,
    readiness_exporter: ReadinessExporter = export_document_rag_local_readiness,
) -> DocumentRagLocalOperatorResult:
    readiness = readiness_exporter(
        output_dir=output_dir,
        ocr_base_url=ocr_base_url,
        ocr_profile=ocr_profile,
        ocr_timeout_seconds=ocr_timeout_seconds,
        provider_base_url=provider_base_url,
        source_id=source_id,
        provider_repo_path=provider_repo_path,
        provider_python=provider_python,
        timeout_seconds=timeout_seconds,
    )
    readiness_payload = document_rag_local_readiness_to_dict(readiness)
    return _operator_result(
        decision=readiness.decision,
        reason_code=readiness.reason_code,
        readiness=readiness_payload,
        upload_to_use=_upload_not_run("readiness_only"),
        summary={
            "entrypoint": "readiness",
            "source_id": source_id,
            "readiness_decision": readiness.decision,
            "upload_to_use_status": "not_run",
        },
        recommended_actions=list(readiness.recommended_actions),
    )


def run_document_rag_local_trial_entrypoint(
    *,
    document_path: Path,
    parse_mode: str = DEFAULT_PARSE_MODE,
    source_id: str = DEFAULT_SOURCE_ID,
    title: str = DEFAULT_TITLE,
    query: str = DEFAULT_QUERY,
    ocr_base_url: str = OCR_CAPABILITY_PROVIDER_BASE_URL,
    ocr_profile: str = DEFAULT_OCR_PROFILE,
    ocr_timeout_seconds: float = OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
    provider_base_url: str = DEFAULT_PROVIDER_BASE_URL,
    provider_api_key: str | None = None,
    provider_repo_path: Path | None = DEFAULT_PROVIDER_REPO,
    provider_python: str = DEFAULT_PROVIDER_PYTHON,
    top_k: int = DEFAULT_TOP_K,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_pages: int | None = 5,
    handoff_only: bool = False,
    allow_review_readiness: bool = True,
    output_dir: Path = DEFAULT_OPERATOR_OUTPUT_DIR,
    upload_materialization: DocumentRagOperatorUploadMaterialization | dict[str, Any] | None = None,
    readiness_exporter: ReadinessExporter = export_document_rag_local_readiness,
    upload_to_use_exporter: UploadToUseExporter = export_document_rag_upload_to_use_loop,
) -> DocumentRagLocalOperatorResult:
    readiness_output_dir = output_dir / "readiness"
    upload_output_dir = output_dir / "upload-to-use"
    readiness = readiness_exporter(
        output_dir=readiness_output_dir,
        ocr_base_url=ocr_base_url,
        ocr_profile=ocr_profile,
        ocr_timeout_seconds=ocr_timeout_seconds,
        provider_base_url=provider_base_url,
        source_id=source_id,
        provider_repo_path=provider_repo_path,
        provider_python=provider_python,
        timeout_seconds=timeout_seconds,
    )
    readiness_payload = document_rag_local_readiness_to_dict(readiness)
    if readiness.decision == "blocked":
        return _operator_result(
            decision="blocked",
            reason_code=f"readiness_{readiness.reason_code}",
            readiness=readiness_payload,
            upload_to_use=_upload_not_run("readiness_blocked"),
            summary=_trial_summary(document_path, source_id, readiness.decision, "not_run", upload_materialization),
            recommended_actions=["fix_readiness_before_running_local_document_rag_trial", *readiness.recommended_actions],
        )
    if readiness.decision == "review" and not allow_review_readiness:
        return _operator_result(
            decision="review",
            reason_code=f"readiness_{readiness.reason_code}",
            readiness=readiness_payload,
            upload_to_use=_upload_not_run("readiness_review_not_allowed"),
            summary=_trial_summary(document_path, source_id, readiness.decision, "not_run", upload_materialization),
            recommended_actions=["review_readiness_or_set_allow_review_readiness", *readiness.recommended_actions],
        )

    upload = upload_to_use_exporter(
        document_path=document_path,
        output_dir=upload_output_dir,
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
    )
    upload_payload = document_rag_upload_to_use_loop_to_dict(upload)
    return _operator_result(
        decision=upload.decision,
        reason_code=upload.reason_code,
        readiness=readiness_payload,
        upload_to_use=upload_payload,
        summary={
            **_trial_summary(document_path, source_id, readiness.decision, upload.decision, upload_materialization),
            "upload_report_json_path": _path_string(upload.json_path),
            "upload_report_markdown_path": _path_string(upload.markdown_path),
            "parser_artifact_path": _path_string(upload.parser_artifact_path),
        },
        recommended_actions=list(dict.fromkeys([*upload.recommended_actions, *readiness.recommended_actions])),
    )


def document_rag_local_operator_result_to_dict(result: DocumentRagLocalOperatorResult) -> dict[str, Any]:
    return asdict(result)


def _operator_result(
    *,
    decision: str,
    reason_code: str,
    readiness: dict[str, Any],
    upload_to_use: dict[str, Any],
    summary: dict[str, Any],
    recommended_actions: list[str],
) -> DocumentRagLocalOperatorResult:
    return DocumentRagLocalOperatorResult(
        id=DOCUMENT_RAG_LOCAL_OPERATOR_ENTRYPOINT_ID,
        generated_at=datetime.now(UTC).isoformat(),
        decision=decision,
        reason_code=reason_code,
        readiness=readiness,
        upload_to_use=upload_to_use,
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
        recommended_actions=list(dict.fromkeys(recommended_actions)),
        non_goals=_non_goals(),
    )


def _upload_not_run(reason_code: str) -> dict[str, Any]:
    return {
        "status": "not_run",
        "reason_code": reason_code,
        "decision": "not_run",
        "json_path": None,
        "markdown_path": None,
    }


def _trial_summary(
    document_path: Path,
    source_id: str,
    readiness_decision: str,
    upload_decision: str,
    upload_materialization: DocumentRagOperatorUploadMaterialization | dict[str, Any] | None = None,
) -> dict[str, Any]:
    materialized = _upload_materialization_to_dict(upload_materialization)
    return {
        "entrypoint": "local_trial",
        "input_mode": "uploaded_file" if materialized else "document_path",
        "document_path": str(document_path),
        "source_id": source_id,
        "readiness_decision": readiness_decision,
        "upload_to_use_status": upload_decision,
        **({"upload_materialization": materialized} if materialized else {}),
    }


def _non_goals() -> list[str]:
    return [
        "does_not_enable_default_chat_retrieval_injection",
        "does_not_create_source_to_agent_binding",
        "does_not_mutate_domain_agent_manifests",
        "does_not_write_memory_audit_approval_or_governance_records",
        "does_not_start_external_services",
        "does_not_execute_graphrag",
        "does_not_build_full_knowledge_base_management_ui",
    ]


def _path_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _safe_upload_filename(filename: str) -> str:
    name = Path(str(filename or "document.bin")).name.strip() or "document.bin"
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return safe[:120] or "document.bin"


def _upload_materialization_to_dict(
    upload_materialization: DocumentRagOperatorUploadMaterialization | dict[str, Any] | None,
) -> dict[str, Any] | None:
    if upload_materialization is None:
        return None
    if isinstance(upload_materialization, DocumentRagOperatorUploadMaterialization):
        return {
            "filename": upload_materialization.filename,
            "media_type": upload_materialization.media_type,
            "document_path": str(upload_materialization.document_path),
            "sha256": upload_materialization.sha256,
            "byte_size": upload_materialization.byte_size,
        }
    payload = dict(upload_materialization)
    if "document_path" in payload:
        payload["document_path"] = str(payload["document_path"])
    return payload
