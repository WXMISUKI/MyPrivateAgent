"""Local document RAG operator APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

try:
    from backend.capability_runtime.document_rag_local_operator_entrypoint import (
        DEFAULT_OPERATOR_OUTPUT_DIR,
        DEFAULT_PROVIDER_REPO,
        document_rag_local_operator_result_to_dict,
        run_document_rag_local_readiness_entrypoint,
        run_document_rag_local_trial_entrypoint,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from capability_runtime.document_rag_local_operator_entrypoint import (
        DEFAULT_OPERATOR_OUTPUT_DIR,
        DEFAULT_PROVIDER_REPO,
        document_rag_local_operator_result_to_dict,
        run_document_rag_local_readiness_entrypoint,
        run_document_rag_local_trial_entrypoint,
    )


router = APIRouter(prefix="/api", tags=["document-rag-local-trials"])


@router.post("/document-rag/local-trials/readiness")
def run_document_rag_local_readiness(payload: dict[str, Any]):
    result = run_document_rag_local_readiness_entrypoint(
        ocr_base_url=str(payload.get("ocr_base_url") or "http://127.0.0.1:8080"),
        ocr_profile=str(payload.get("ocr_profile") or "unknown"),
        ocr_timeout_seconds=_float(payload.get("ocr_timeout_seconds"), 30.0),
        provider_base_url=str(payload.get("provider_base_url") or "http://127.0.0.1:8020"),
        source_id=_optional_str(payload.get("source_id")) or "company_profile_2025_trial",
        provider_repo_path=_optional_path(payload.get("knowledge_provider_repo")) or DEFAULT_PROVIDER_REPO,
        provider_python=str(payload.get("provider_python") or "conda run -n GRAPHRAG python"),
        timeout_seconds=_float(payload.get("timeout_seconds"), 5.0),
        output_dir=_optional_path(payload.get("output_dir")) or DEFAULT_OPERATOR_OUTPUT_DIR / "readiness",
    )
    return _response(result)


@router.post("/document-rag/local-trials")
def run_document_rag_local_trial(payload: dict[str, Any]):
    document_path = _optional_path(payload.get("document_path"))
    if document_path is None:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "error": {
                    "code": "DOCUMENT_RAG_LOCAL_TRIAL_INVALID_INPUT",
                    "message": "document_path is required.",
                },
            },
        )
    result = run_document_rag_local_trial_entrypoint(
        document_path=document_path,
        parse_mode=str(payload.get("parse_mode") or "ocr"),
        source_id=str(payload.get("source_id") or "company_profile_2025_trial"),
        title=str(payload.get("title") or "公司简介 2025 trial"),
        query=str(payload.get("query") or "公司主营业务和服务范围是什么？"),
        ocr_base_url=str(payload.get("ocr_base_url") or "http://127.0.0.1:8080"),
        ocr_profile=str(payload.get("ocr_profile") or "unknown"),
        ocr_timeout_seconds=_float(payload.get("ocr_timeout_seconds"), 30.0),
        provider_base_url=str(payload.get("provider_base_url") or "http://127.0.0.1:8020"),
        provider_api_key=_optional_str(payload.get("provider_api_key")),
        provider_repo_path=_optional_path(payload.get("knowledge_provider_repo")) or DEFAULT_PROVIDER_REPO,
        provider_python=str(payload.get("provider_python") or "conda run -n GRAPHRAG python"),
        top_k=_int(payload.get("top_k"), 3),
        timeout_seconds=_float(payload.get("timeout_seconds"), 5.0),
        max_pages=_optional_int(payload.get("max_pages")),
        handoff_only=bool(payload.get("handoff_only", False)),
        allow_review_readiness=bool(payload.get("allow_review_readiness", True)),
        output_dir=_optional_path(payload.get("output_dir")) or DEFAULT_OPERATOR_OUTPUT_DIR,
    )
    return _response(result)


def _response(result) -> JSONResponse:
    payload = document_rag_local_operator_result_to_dict(result)
    status_code = 200 if result.decision != "blocked" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": result.decision != "blocked",
            **payload,
        },
    )


def _optional_path(value: Any) -> Path | None:
    text = _optional_str(value)
    return Path(text) if text else None


def _optional_str(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None
