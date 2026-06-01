"""HTTP provider definitions for PaddleOCR PaddleX serving."""

from __future__ import annotations

from statistics import mean
from typing import Any

from ..clients.http_client import CapabilityProviderError, HttpCapabilityClient
from ..contracts import CapabilityDefinition


EXTERNAL_PROVIDER_ID = "paddleocr"


def build_http_paddleocr_capabilities(
    *,
    base_url: str,
    timeout_seconds: float = 30.0,
    client: HttpCapabilityClient | None = None,
) -> list[CapabilityDefinition]:
    http_client = client or HttpCapabilityClient(base_url=base_url, timeout_seconds=timeout_seconds)
    return [
        CapabilityDefinition(
            capability_id="document.ocr.extract",
            kind="ocr",
            transport="http",
            provider=EXTERNAL_PROVIDER_ID,
            title="PaddleOCR Extract",
            description="Extract OCR text and compact layout evidence through PaddleOCR PaddleX serving.",
            endpoint="/api/capabilities/document.ocr.extract/invoke",
            input_schema={
                "type": "object",
                "required": ["file_base64", "media_type"],
                "properties": {
                    "file_base64": {"type": "string"},
                    "media_type": {"type": "string"},
                    "filename": {"type": "string"},
                    "visualize": {"type": "boolean"},
                },
            },
            output_schema={
                "type": "object",
                "required": ["text", "pages", "blocks", "tables", "artifacts", "warnings", "raw"],
                "properties": {
                    "text": {"type": "string"},
                    "pages": {"type": "array"},
                    "blocks": {"type": "array"},
                    "tables": {"type": "array"},
                    "artifacts": {"type": "array"},
                    "warnings": {"type": "array"},
                    "raw": {"type": "object"},
                },
            },
            metadata={
                "provider_base_url": base_url.rstrip("/"),
                "provider_health_path": "/health",
                "provider_invoke_path": "/ocr",
                "provider_heartbeat_path": "/health",
                "external_provider": EXTERNAL_PROVIDER_ID,
                "serving": "paddlex",
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
            return {
                "status": "unreachable",
                "reason": exc.message,
                "error": exc.to_payload(),
            }
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
        file_base64 = str(payload.get("file_base64") or payload.get("file") or "").strip()
        if not file_base64:
            return {
                "ok": False,
                "error": {
                    "code": "OCR_INVALID_INPUT",
                    "message": "OCR invocation requires file_base64.",
                },
            }
        try:
            data = client.post_json("/ocr", _to_paddlex_payload(payload, file_base64))
        except CapabilityProviderError as exc:
            return {
                "ok": False,
                "error": exc.to_payload(),
            }
        error_code = data.get("errorCode")
        if error_code not in (0, "0", None):
            return {
                "ok": False,
                "error": {
                    "code": "PADDLEOCR_PROVIDER_ERROR",
                    "message": str(data.get("errorMsg") or "PaddleOCR invocation failed."),
                    "provider_error_code": str(error_code),
                },
            }
        return {
            "ok": True,
            "capability_id": "document.ocr.extract",
            "provider": EXTERNAL_PROVIDER_ID,
            "result": _normalize_ocr_result(data.get("result") or {}),
        }

    return invoke


def _to_paddlex_payload(payload: dict[str, Any], file_base64: str) -> dict[str, Any]:
    mapped = {
        "file": file_base64,
        "fileType": _file_type(payload.get("media_type")),
        "visualize": bool(payload.get("visualize", False)),
    }
    for source, target in (
        ("use_doc_orientation_classify", "useDocOrientationClassify"),
        ("use_doc_unwarping", "useDocUnwarping"),
        ("use_textline_orientation", "useTextlineOrientation"),
    ):
        if source in payload:
            mapped[target] = payload[source]
    return mapped


def _file_type(media_type: Any) -> int:
    value = str(media_type or "").lower().strip()
    if value == "application/pdf" or value.endswith("/pdf"):
        return 0
    return 1


def _normalize_ocr_result(result: dict[str, Any]) -> dict[str, Any]:
    ocr_results = result.get("ocrResults")
    warnings: list[str] = []
    if not isinstance(ocr_results, list):
        ocr_results = []
        warnings.append("PaddleX response missing ocrResults array.")
    if not ocr_results:
        warnings.append("No OCR text detected from provider response.")
    pages: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    all_texts: list[str] = []
    for page_index, page_result in enumerate(ocr_results, start=1):
        pruned = page_result.get("prunedResult") if isinstance(page_result, dict) else {}
        if not isinstance(pruned, dict):
            pruned = {}
        texts = _extract_texts(pruned)
        scores = _extract_scores(pruned)
        boxes = _extract_boxes(pruned)
        page_text = "\n".join(texts)
        if page_text:
            all_texts.append(page_text)
        pages.append(
            {
                "page_number": page_index,
                "text": page_text,
                "confidence": round(mean(scores), 4) if scores else None,
            }
        )
        for offset, text in enumerate(texts):
            blocks.append(
                {
                    "page_number": page_index,
                    "block_id": f"p{page_index}-b{offset + 1}",
                    "type": "text",
                    "text": text,
                    "confidence": scores[offset] if offset < len(scores) else None,
                    "bbox": boxes[offset] if offset < len(boxes) else None,
                }
            )
    return {
        "text": "\n".join(all_texts),
        "pages": pages,
        "blocks": blocks,
        "tables": [],
        "artifacts": [],
        "warnings": warnings,
        "raw": result,
    }


def _extract_texts(pruned: dict[str, Any]) -> list[str]:
    values = pruned.get("rec_texts") or pruned.get("texts") or pruned.get("text")
    if isinstance(values, str):
        return [values] if values else []
    if isinstance(values, list):
        return [str(item) for item in values if str(item)]
    return []


def _extract_scores(pruned: dict[str, Any]) -> list[float]:
    values = pruned.get("rec_scores") or pruned.get("scores") or []
    if not isinstance(values, list):
        return []
    scores: list[float] = []
    for value in values:
        try:
            scores.append(float(value))
        except (TypeError, ValueError):
            continue
    return scores


def _extract_boxes(pruned: dict[str, Any]) -> list[Any]:
    values = pruned.get("rec_boxes") or pruned.get("dt_polys") or pruned.get("boxes") or []
    return values if isinstance(values, list) else []
