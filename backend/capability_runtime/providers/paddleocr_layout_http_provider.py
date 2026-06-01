"""HTTP provider definitions for PaddleOCR PP-Structure layout parsing."""

from __future__ import annotations

from typing import Any

from ..clients.http_client import CapabilityProviderError, HttpCapabilityClient
from ..contracts import CapabilityDefinition


EXTERNAL_PROVIDER_ID = "paddleocr"


def build_http_layout_capabilities(
    *,
    base_url: str,
    timeout_seconds: float = 60.0,
    invoke_path: str = "/layout-parsing",
    client: HttpCapabilityClient | None = None,
) -> list[CapabilityDefinition]:
    http_client = client or HttpCapabilityClient(base_url=base_url, timeout_seconds=timeout_seconds)
    normalized_invoke_path = _normalize_invoke_path(invoke_path)
    return [
        CapabilityDefinition(
            capability_id="document.layout.parse",
            kind="layout",
            transport="http",
            provider=EXTERNAL_PROVIDER_ID,
            title="PaddleOCR Layout Parse",
            description="Parse document layout/tables and return markdown-ready evidence.",
            endpoint="/api/capabilities/document.layout.parse/invoke",
            input_schema={
                "type": "object",
                "required": ["file_base64", "media_type"],
                "properties": {
                    "file_base64": {"type": "string"},
                    "media_type": {"type": "string"},
                    "filename": {"type": "string"},
                    "output_format": {"type": "string"},
                    "include_tables": {"type": "boolean"},
                    "include_layout": {"type": "boolean"},
                    "max_pages": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["markdown", "elements", "tables", "pages", "artifacts", "warnings", "raw"],
                "properties": {
                    "markdown": {"type": "string"},
                    "elements": {"type": "array"},
                    "tables": {"type": "array"},
                    "pages": {"type": "array"},
                    "artifacts": {"type": "array"},
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
                "serving": "pp_structure_v3",
            },
            invoker=_invoke(http_client, normalized_invoke_path),
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


def _invoke(client: HttpCapabilityClient, invoke_path: str):
    def invoke(payload: dict[str, Any]) -> dict[str, Any]:
        file_base64 = str(payload.get("file_base64") or "").strip()
        if not file_base64:
            return {"ok": False, "error": {"code": "LAYOUT_INVALID_INPUT", "message": "Layout parse requires file_base64."}}
        media_type = str(payload.get("media_type") or "").strip().lower()
        if not _is_supported_layout_media_type(media_type):
            return {
                "ok": False,
                "error": {
                    "code": "LAYOUT_UNSUPPORTED_MEDIA_TYPE",
                    "message": "Layout parse supports application/pdf, image/png, image/jpeg.",
                    "media_type": media_type,
                },
            }
        output_format = str(payload.get("output_format") or "markdown").strip().lower()
        if output_format not in {"markdown", "json"}:
            return {
                "ok": False,
                "error": {
                    "code": "LAYOUT_INVALID_OUTPUT_FORMAT",
                    "message": "output_format must be markdown or json.",
                    "output_format": output_format,
                },
            }
        try:
            data = client.post_json(invoke_path, _to_layout_payload(payload, file_base64))
        except ValueError:
            return {
                "ok": False,
                "error": {
                    "code": "LAYOUT_INVALID_INPUT",
                    "message": "max_pages must be a positive integer.",
                },
            }
        except CapabilityProviderError as exc:
            return {"ok": False, "error": exc.to_payload()}
        error_code = data.get("errorCode")
        if error_code not in (0, "0", None):
            return {
                "ok": False,
                "error": {
                    "code": "PADDLE_LAYOUT_PROVIDER_ERROR",
                    "message": str(data.get("errorMsg") or "Layout parse failed."),
                    "provider_error_code": str(error_code),
                },
            }
        return {
            "ok": True,
            "capability_id": "document.layout.parse",
            "provider": EXTERNAL_PROVIDER_ID,
            "result": _normalize_layout_result(data.get("result") or {}),
        }

    return invoke


def _to_layout_payload(payload: dict[str, Any], file_base64: str) -> dict[str, Any]:
    mapped = {
        "file": file_base64,
        "fileType": _file_type(payload.get("media_type")),
        "outputFormat": str(payload.get("output_format") or "markdown"),
        "includeTables": bool(payload.get("include_tables", True)),
        "includeLayout": bool(payload.get("include_layout", True)),
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


def _is_supported_layout_media_type(media_type: str) -> bool:
    return media_type in {"application/pdf", "image/png", "image/jpeg"}


def _normalize_layout_result(result: dict[str, Any]) -> dict[str, Any]:
    layout_results = result.get("layoutParsingResults")
    if isinstance(layout_results, list) and layout_results:
        pages = [item for item in layout_results if isinstance(item, dict)]
    else:
        pages = result.get("pages") or result.get("pageResults")
    markdown = _extract_markdown(result, pages)
    elements = _extract_elements(result, pages)
    tables = _extract_tables(result, pages)
    warnings: list[str] = []
    if not markdown:
        warnings.append("Layout provider returned empty markdown.")
    if not isinstance(elements, list):
        elements = []
    if not isinstance(tables, list):
        tables = []
    if not isinstance(pages, list):
        pages = []
    return {
        "markdown": markdown,
        "elements": elements,
        "tables": tables,
        "pages": pages,
        "artifacts": [],
        "warnings": warnings,
        "raw": result,
    }


def _extract_markdown(result: dict[str, Any], pages: list[dict[str, Any]] | Any) -> str:
    if isinstance(result.get("markdown"), str):
        return str(result.get("markdown") or "")
    if isinstance(pages, list):
        segments: list[str] = []
        for page in pages:
            markdown_obj = page.get("markdown")
            if isinstance(markdown_obj, dict):
                text = markdown_obj.get("text")
                if isinstance(text, str) and text.strip():
                    segments.append(text)
                    continue
            pruned = page.get("prunedResult")
            if isinstance(pruned, dict):
                text = pruned.get("markdown")
                if isinstance(text, str) and text.strip():
                    segments.append(text)
        if segments:
            return "\n\n".join(segments)
    return str(result.get("md") or result.get("text") or "")


def _extract_elements(result: dict[str, Any], pages: list[dict[str, Any]] | Any) -> list[Any] | Any:
    elements = result.get("elements") or result.get("layout") or result.get("blocks")
    if elements:
        return elements
    if isinstance(pages, list):
        flattened: list[Any] = []
        for page in pages:
            pruned = page.get("prunedResult")
            if isinstance(pruned, dict):
                layouts = pruned.get("layouts")
                if isinstance(layouts, list):
                    flattened.extend(layouts)
        if flattened:
            return flattened
    return []


def _extract_tables(result: dict[str, Any], pages: list[dict[str, Any]] | Any) -> list[Any] | Any:
    tables = result.get("tables") or result.get("tableResults")
    if tables:
        return tables
    if isinstance(pages, list):
        flattened: list[Any] = []
        for page in pages:
            pruned = page.get("prunedResult")
            if isinstance(pruned, dict):
                candidates = pruned.get("table_res_list") or pruned.get("tables")
                if isinstance(candidates, list):
                    flattened.extend(candidates)
        if flattened:
            return flattened
    return []


def _normalize_invoke_path(path: str) -> str:
    normalized = (path or "").strip()
    if not normalized:
        return "/layout-parsing"
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized
