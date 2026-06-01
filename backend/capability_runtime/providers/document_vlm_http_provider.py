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
    client: HttpCapabilityClient | None = None,
) -> list[CapabilityDefinition]:
    http_client = client or HttpCapabilityClient(base_url=base_url, timeout_seconds=timeout_seconds)
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
                "provider_invoke_path": "/vlm",
                "provider_heartbeat_path": "/health",
                "external_provider": EXTERNAL_PROVIDER_ID,
                "mode": "placeholder_sync",
            },
            invoker=_invoke(http_client),
            health_checker=_provider_health(http_client),
            heartbeat_checker=_provider_health(http_client),
        )
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


def _invoke(client: HttpCapabilityClient):
    def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        file_base64 = str(payload.get("file_base64") or "").strip()
        if not file_base64:
            return {"ok": False, "error": {"code": "VLM_INVALID_INPUT", "message": "VLM parse requires file_base64."}}
        task = str(payload.get("task") or "").strip().lower()
        if task not in {"summarize", "extract_fields", "chart_understanding", "qa"}:
            return {"ok": False, "error": {"code": "VLM_UNSUPPORTED_TASK", "message": "Unsupported VLM task.", "task": task}}
        try:
            data = client.post_json("/vlm", _to_vlm_payload(payload, file_base64, task))
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


def _normalize_vlm_result(result: dict[str, Any]) -> dict[str, Any]:
    summary = str(result.get("summary") or result.get("answer") or "")
    sections = result.get("sections")
    entities = result.get("entities")
    answers = result.get("answers")
    evidence = result.get("evidence")
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
