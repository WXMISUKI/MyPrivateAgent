"""HTTP provider definitions for document VLM parsing."""

from __future__ import annotations

from typing import Any

from ..clients.http_client import CapabilityProviderError, HttpCapabilityClient
from ..contracts import CapabilityDefinition


EXTERNAL_PROVIDER_ID = "document_vlm_provider"


def build_http_document_vlm_capabilities(
    *,
    base_url: str,
    timeout_seconds: float = 90.0,
    invoke_path: str = "/vlm",
    async_submit_path: str = "/api/vlm/jobs",
    async_status_path_template: str = "/api/vlm/jobs/{job_id}",
    client: HttpCapabilityClient | None = None,
) -> list[CapabilityDefinition]:
    http_client = client or HttpCapabilityClient(base_url=base_url, timeout_seconds=timeout_seconds)
    normalized_invoke_path = _normalize_invoke_path(invoke_path)
    normalized_async_submit_path = _normalize_async_path(async_submit_path)
    normalized_async_status_path_template = _normalize_async_path_template(async_status_path_template)
    return [
        CapabilityDefinition(
            capability_id="document.vlm.parse",
            kind="vlm",
            transport="http",
            provider=EXTERNAL_PROVIDER_ID,
            title="Document VLM Parse",
            description="Semantic document understanding through external multimodal provider.",
            endpoint="/api/capabilities/document.vlm.parse/invoke",
            input_schema={
                "type": "object",
                "required": ["file_base64", "media_type", "task"],
                "properties": {
                    "file_base64": {"type": "string"},
                    "media_type": {"type": "string"},
                    "filename": {"type": "string"},
                    "task": {"type": "string"},
                    "question": {"type": "string"},
                    "max_pages": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["summary", "sections", "entities", "answers", "evidence", "warnings", "raw"],
                "properties": {
                    "summary": {"type": "string"},
                    "sections": {"type": "array"},
                    "entities": {"type": "array"},
                    "answers": {"type": "array"},
                    "evidence": {"type": "array"},
                    "warnings": {"type": "array"},
                    "raw": {"type": "object"},
                },
            },
            metadata={
                "provider_base_url": base_url.rstrip("/"),
                "provider_health_path": "/health",
                "provider_invoke_path": normalized_invoke_path,
                "provider_heartbeat_path": "/health",
                "external_provider": EXTERNAL_PROVIDER_ID,
                "mode": "placeholder_sync",
            },
            invoker=_invoke(http_client, normalized_invoke_path),
            health_checker=_provider_health(http_client),
            heartbeat_checker=_provider_health(http_client),
        ),
        CapabilityDefinition(
            capability_id="document.vlm.parse.async",
            kind="vlm",
            transport="http",
            provider=EXTERNAL_PROVIDER_ID,
            title="Document VLM Parse Async",
            description="Asynchronous semantic document parsing placeholder contract.",
            endpoint="/api/capabilities/document.vlm.parse.async/invoke",
            input_schema={
                "type": "object",
                "required": ["operation"],
                "properties": {
                    "operation": {"type": "string"},
                    "job_id": {"type": "string"},
                    "file_base64": {"type": "string"},
                    "media_type": {"type": "string"},
                    "filename": {"type": "string"},
                    "task": {"type": "string"},
                    "question": {"type": "string"},
                    "max_pages": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["job_id", "status", "progress", "warnings", "raw"],
                "properties": {
                    "job_id": {"type": "string"},
                    "status": {"type": "string"},
                    "progress": {"type": "number"},
                    "result": {"type": "object"},
                    "error": {"type": "object"},
                    "warnings": {"type": "array"},
                    "raw": {"type": "object"},
                },
            },
            metadata={
                "provider_base_url": base_url.rstrip("/"),
                "provider_health_path": "/health",
                "provider_invoke_path": normalized_async_submit_path,
                "provider_status_path_template": normalized_async_status_path_template,
                "provider_heartbeat_path": "/health",
                "external_provider": EXTERNAL_PROVIDER_ID,
                "mode": "placeholder_async",
            },
            invoker=_invoke_async(
                client=http_client,
                submit_path=normalized_async_submit_path,
                status_path_template=normalized_async_status_path_template,
            ),
            health_checker=_provider_health(http_client),
            heartbeat_checker=_provider_health(http_client),
        ),
    ]


def _provider_health(client: HttpCapabilityClient):
    def check() -> dict[str, Any]:
        try:
            data = client.get_json("/health")
        except CapabilityProviderError as exc:
            return {"status": "unreachable", "reason": exc.message, "error": exc.to_payload()}
        status = str(data.get("status") or "unknown")
        if status == "ok" or data.get("errorCode") in (0, "0"):
            status = "ready"
        return {
            "status": status,
            "reason": str(data.get("message") or data.get("reason") or data.get("errorMsg") or ""),
            "raw": data,
        }

    return check


def _invoke(client: HttpCapabilityClient, invoke_path: str):
    def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        validation_error = _validate_vlm_payload(payload)
        if validation_error is not None:
            return {"ok": False, "error": validation_error}
        try:
            data = client.post_json(
                invoke_path,
                _to_vlm_payload(payload, str(payload.get("file_base64") or ""), str(payload.get("task") or "")),
            )
        except ValueError:
            return {"ok": False, "error": {"code": "VLM_INVALID_INPUT", "message": "max_pages must be a positive integer."}}
        except CapabilityProviderError as exc:
            return {"ok": False, "error": exc.to_payload()}
        error_code = data.get("errorCode")
        if error_code not in (0, "0", None):
            return {
                "ok": False,
                "error": {
                    "code": "DOCUMENT_VLM_PROVIDER_ERROR",
                    "message": str(data.get("errorMsg") or "Document VLM invocation failed."),
                    "provider_error_code": str(error_code),
                },
            }
        return {
            "ok": True,
            "capability_id": "document.vlm.parse",
            "provider": EXTERNAL_PROVIDER_ID,
            "result": _normalize_vlm_result(data.get("result") or {}),
        }

    return invoke


def _to_vlm_payload(payload: dict[str, Any], file_base64: str, task: str) -> dict[str, Any]:
    mapped = {
        "file": file_base64,
        "fileType": _file_type(payload.get("media_type")),
        "task": task,
        "question": str(payload.get("question") or ""),
    }
    if payload.get("max_pages") is not None:
        max_pages = int(payload["max_pages"])
        if max_pages <= 0:
            raise ValueError("max_pages must be positive")
        mapped["maxPages"] = max_pages
    return mapped


def _file_type(media_type: Any) -> int:
    value = str(media_type or "").lower().strip()
    if value == "application/pdf" or value.endswith("/pdf"):
        return 0
    return 1


def _is_supported_vlm_media_type(media_type: str) -> bool:
    return media_type in {"application/pdf", "image/png", "image/jpeg"}


def _normalize_invoke_path(path: str) -> str:
    normalized = (path or "").strip()
    if not normalized:
        return "/vlm"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized


def _normalize_vlm_result(result: dict[str, Any]) -> dict[str, Any]:
    summary = str(result.get("summary") or result.get("answer") or "")
    sections = result.get("sections")
    entities = result.get("entities")
    answers = result.get("answers")
    evidence = result.get("evidence")
    pages = _extract_pages(result)
    if not summary and pages:
        summary = "\n\n".join(_page_markdown_text(page) for page in pages if _page_markdown_text(page)).strip()
    if not sections and pages:
        sections = _derive_sections_from_pages(pages)
    if not evidence and pages:
        evidence = _derive_evidence_from_pages(pages)
    warnings: list[str] = []
    if not summary:
        warnings.append("VLM provider returned empty summary.")
    if not isinstance(sections, list):
        sections = []
    if not isinstance(entities, list):
        entities = []
    if not isinstance(answers, list):
        answers = []
    if not isinstance(evidence, list):
        evidence = []
    return {
        "summary": summary,
        "sections": sections,
        "entities": entities,
        "answers": answers,
        "evidence": evidence,
        "warnings": warnings,
        "raw": result,
    }


def _invoke_async(
    *,
    client: HttpCapabilityClient,
    submit_path: str,
    status_path_template: str,
):
    def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        operation = str(payload.get("operation") or "submit").strip().lower()
        if operation not in {"submit", "status"}:
            return {
                "ok": False,
                "error": {
                    "code": "VLM_ASYNC_INVALID_OPERATION",
                    "message": "operation must be submit or status.",
                    "operation": operation,
                },
            }
        if operation == "status":
            job_id = str(payload.get("job_id") or "").strip()
            if not job_id:
                return {
                    "ok": False,
                    "error": {"code": "VLM_ASYNC_MISSING_JOB_ID", "message": "job_id is required when operation=status."},
                }
            try:
                data = client.get_json(_fill_async_status_path(status_path_template, job_id))
            except CapabilityProviderError as exc:
                return {"ok": False, "error": exc.to_payload()}
            return {
                "ok": True,
                "capability_id": "document.vlm.parse.async",
                "provider": EXTERNAL_PROVIDER_ID,
                "result": _normalize_async_job(data),
            }

        validation_error = _validate_vlm_payload(payload)
        if validation_error is not None:
            return {"ok": False, "error": validation_error}
        submit_payload = _to_vlm_payload(payload, str(payload.get("file_base64") or ""), str(payload.get("task") or "summarize"))
        try:
            data = client.post_json(submit_path, submit_payload)
        except CapabilityProviderError as exc:
            return {"ok": False, "error": exc.to_payload()}
        error_code = data.get("errorCode")
        if error_code not in (0, "0", None):
            return {
                "ok": False,
                "error": {
                    "code": "DOCUMENT_VLM_PROVIDER_ERROR",
                    "message": str(data.get("errorMsg") or "Document VLM async submit failed."),
                    "provider_error_code": str(error_code),
                },
            }
        return {
            "ok": True,
            "capability_id": "document.vlm.parse.async",
            "provider": EXTERNAL_PROVIDER_ID,
            "result": _normalize_async_job(data),
        }

    return invoke


def _validate_vlm_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    file_base64 = str(payload.get("file_base64") or "").strip()
    if not file_base64:
        return {"code": "VLM_INVALID_INPUT", "message": "VLM parse requires file_base64."}
    media_type = str(payload.get("media_type") or "").strip().lower()
    if not _is_supported_vlm_media_type(media_type):
        return {
            "code": "VLM_UNSUPPORTED_MEDIA_TYPE",
            "message": "VLM parse supports application/pdf, image/png, image/jpeg.",
            "media_type": media_type,
        }
    task = str(payload.get("task") or "").strip().lower()
    if task not in {"summarize", "extract_fields", "chart_understanding", "qa"}:
        return {"code": "VLM_UNSUPPORTED_TASK", "message": "Unsupported VLM task.", "task": task}
    if task == "qa" and not str(payload.get("question") or "").strip():
        return {
            "code": "VLM_INVALID_INPUT",
            "message": "question is required when task=qa.",
        }
    return None


def _normalize_async_job(data: dict[str, Any]) -> dict[str, Any]:
    result = data.get("result") if isinstance(data.get("result"), dict) else data
    status = _normalize_async_status(str(result.get("status") or result.get("job_status") or "queued"))
    job_id = str(result.get("job_id") or result.get("id") or "")
    progress_raw = result.get("progress", 0)
    try:
        progress = float(progress_raw)
    except (TypeError, ValueError):
        progress = 0.0
    warnings: list[str] = []
    if not job_id:
        warnings.append("Async provider response missing job_id.")
    return {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "result": result.get("result") if isinstance(result.get("result"), dict) else {},
        "error": result.get("error") if isinstance(result.get("error"), dict) else {},
        "warnings": warnings,
        "raw": data,
    }


def _normalize_async_status(raw_status: str) -> str:
    value = (raw_status or "").strip().lower()
    if value in {"queued", "running", "succeeded", "failed", "expired"}:
        return value
    if value in {"success", "done"}:
        return "succeeded"
    if value in {"error", "exception", "timeout"}:
        return "failed"
    if value in {"init", "pending"}:
        return "queued"
    if value in {"", None}:
        return "queued"
    return "failed"


def _normalize_async_path(path: str) -> str:
    normalized = (path or "").strip()
    if not normalized:
        return "/api/vlm/jobs"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized


def _normalize_async_path_template(template: str) -> str:
    normalized = _normalize_async_path(template)
    if "{job_id}" not in normalized:
        if normalized.endswith("/"):
            return normalized + "{job_id}"
        return normalized + "/{job_id}"
    return normalized


def _fill_async_status_path(template: str, job_id: str) -> str:
    return str(template or "").replace("{job_id}", job_id).replace("{JOB_ID}", job_id)


def _extract_pages(result: dict[str, Any]) -> list[dict[str, Any]]:
    layout_results = result.get("layoutParsingResults")
    if not isinstance(layout_results, list):
        return []
    return [item for item in layout_results if isinstance(item, dict)]


def _page_markdown_text(page: dict[str, Any]) -> str:
    markdown_obj = page.get("markdown")
    if isinstance(markdown_obj, dict):
        text = markdown_obj.get("text")
        if isinstance(text, str):
            return text
    if isinstance(markdown_obj, str):
        return markdown_obj
    pruned = page.get("prunedResult")
    if isinstance(pruned, dict):
        text = pruned.get("markdown")
        if isinstance(text, str):
            return text
    return ""


def _derive_sections_from_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for index, page in enumerate(pages, start=1):
        text = _page_markdown_text(page).strip()
        if not text:
            continue
        sections.append({"title": f"Page {index}", "content": text})
    return sections


def _derive_evidence_from_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for index, page in enumerate(pages, start=1):
        pruned = page.get("prunedResult")
        if isinstance(pruned, dict):
            layouts = pruned.get("layouts")
            if isinstance(layouts, list):
                evidence.append({"page": index, "layout_count": len(layouts)})
                continue
        if _page_markdown_text(page).strip():
            evidence.append({"page": index})
    return evidence
