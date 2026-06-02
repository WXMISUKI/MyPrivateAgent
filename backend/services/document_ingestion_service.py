"""Document ingestion workflow orchestration."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from capability_runtime.service import CapabilityRuntimeService, get_capability_runtime_service
    from config import LOCAL_DATA_DIR
    from services.document_artifact_service import (
        DocumentArtifactNotFound,
        DocumentArtifactService,
        get_document_artifact_service,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.capability_runtime.service import CapabilityRuntimeService, get_capability_runtime_service
    from backend.config import LOCAL_DATA_DIR
    from backend.services.document_artifact_service import (
        DocumentArtifactNotFound,
        DocumentArtifactService,
        get_document_artifact_service,
    )


PARSE_MODE_CAPABILITY = {
    "ocr": "document.ocr.extract",
    "layout": "document.layout.parse",
    "vlm_async": "document.vlm.parse.async",
}


class DocumentIngestionError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int = 400, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            **self.details,
        }


class DocumentIngestionNotFound(DocumentIngestionError):
    def __init__(self, ingest_id: str):
        super().__init__(
            "DOCUMENT_INGEST_NOT_FOUND",
            f"Document ingestion not found: {ingest_id}",
            status_code=404,
            details={"ingest_id": ingest_id},
        )


@dataclass(frozen=True)
class DocumentIngestionRecord:
    metadata: dict[str, Any]


class DocumentIngestionService:
    def __init__(
        self,
        *,
        root_dir: Path | None = None,
        capability_runtime: CapabilityRuntimeService | Any | None = None,
        artifact_service: DocumentArtifactService | Any | None = None,
    ):
        self.root_dir = Path(root_dir or (LOCAL_DATA_DIR / "document_ingestions")).resolve()
        self.index_path = self.root_dir / "index.json"
        self.capability_runtime = capability_runtime or get_capability_runtime_service()
        self.artifact_service = artifact_service or get_document_artifact_service()

    def submit(self, request: dict[str, Any]) -> DocumentIngestionRecord:
        parse_mode = _parse_mode(request)
        capability_id = PARSE_MODE_CAPABILITY[parse_mode]
        source_filename = _required_text(request, "filename")
        media_type = _required_text(request, "media_type")
        _required_text(request, "file_base64")

        ingest_id = f"doc-ingest-{uuid.uuid4().hex}"
        now = _now()
        metadata = {
            "ingest_id": ingest_id,
            "status": "running",
            "parse_mode": parse_mode,
            "capability_id": capability_id,
            "provider": "",
            "source_filename": source_filename,
            "media_type": media_type,
            "created_at": now,
            "updated_at": now,
            "artifact_id": "",
            "artifact": {},
            "provider_job": {},
            "warnings": [],
            "error": {},
            "request": _request_summary(request),
        }
        self._write_record(metadata)

        invocation_payload = _build_invocation_payload(parse_mode, request)
        try:
            invocation = self.capability_runtime.invoke(capability_id, invocation_payload)
        except LookupError as exc:
            metadata = self._fail(
                metadata,
                {
                    "code": "DOCUMENT_INGEST_PROVIDER_UNAVAILABLE",
                    "message": str(exc) or f"Capability not found: {capability_id}",
                    "capability_id": capability_id,
                },
            )
            return DocumentIngestionRecord(metadata=metadata)

        metadata["provider"] = str(invocation.get("provider") or "")
        if not invocation.get("ok"):
            metadata = self._fail(
                metadata,
                {
                    "code": "DOCUMENT_INGEST_PROVIDER_UNAVAILABLE",
                    "message": str((invocation.get("error") or {}).get("message") or "Document provider invocation failed."),
                    "capability_id": capability_id,
                    "provider_error": invocation.get("error") or {},
                },
            )
            return DocumentIngestionRecord(metadata=metadata)

        result = invocation.get("result") if isinstance(invocation.get("result"), dict) else {}
        warnings = _string_list(result.get("warnings"))
        if parse_mode == "vlm_async":
            metadata["provider_job"] = _provider_job(result)
            if str(result.get("status") or "") != "succeeded" or not isinstance(result.get("result"), dict) or not result.get("result"):
                metadata.update(
                    {
                        "status": "running" if str(result.get("status") or "") in {"queued", "running"} else str(result.get("status") or "running"),
                        "updated_at": _now(),
                        "warnings": warnings,
                    }
                )
                self._write_record(metadata)
                return DocumentIngestionRecord(metadata=metadata)
            result = result["result"]
            warnings = _string_list(result.get("warnings")) or warnings

        try:
            artifact = self.artifact_service.persist(
                {
                    "source_filename": source_filename,
                    "media_type": media_type,
                    "capability_id": capability_id,
                    "provider": metadata["provider"] or invocation.get("provider") or "unknown",
                    "result": result,
                    "include_raw": bool(request.get("include_raw", False)),
                }
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            metadata = self._fail(
                metadata,
                {
                    "code": "DOCUMENT_INGEST_ARTIFACT_PERSIST_FAILED",
                    "message": str(exc) or "Document artifact persistence failed.",
                },
            )
            return DocumentIngestionRecord(metadata=metadata)

        metadata.update(
            {
                "status": "succeeded",
                "updated_at": _now(),
                "artifact_id": str(artifact.metadata.get("artifact_id") or ""),
                "artifact": artifact.metadata,
                "warnings": warnings or _string_list(artifact.metadata.get("warnings")),
                "error": {},
            }
        )
        self._write_record(metadata)
        return DocumentIngestionRecord(metadata=metadata)

    def get(self, ingest_id: str) -> DocumentIngestionRecord:
        normalized = _normalize_ingest_id(ingest_id)
        metadata_path = self.root_dir / normalized / "metadata.json"
        if not metadata_path.exists():
            raise DocumentIngestionNotFound(normalized)
        metadata = _read_json(metadata_path)
        if not isinstance(metadata, dict):
            raise DocumentIngestionNotFound(normalized)
        return DocumentIngestionRecord(metadata=metadata)

    def get_result(self, ingest_id: str) -> dict[str, Any]:
        record = self.get(ingest_id).metadata
        artifact_id = str(record.get("artifact_id") or "").strip()
        if not artifact_id:
            return {
                "ingestion": record,
                "artifact": {},
                "payload": {},
            }
        try:
            artifact = self.artifact_service.get(artifact_id)
        except DocumentArtifactNotFound as exc:
            raise DocumentIngestionError(
                "DOCUMENT_INGEST_ARTIFACT_NOT_FOUND",
                f"Document ingestion artifact not found: {artifact_id}",
                status_code=404,
                details={"ingest_id": ingest_id, "artifact_id": exc.artifact_id},
            ) from exc
        return {
            "ingestion": record,
            "artifact": artifact.metadata,
            "payload": artifact.payload,
        }

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        records = self._read_index()
        sorted_records = sorted(records, key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return sorted_records[: max(1, min(int(limit), 500))]

    def _fail(self, metadata: dict[str, Any], error: dict[str, Any]) -> dict[str, Any]:
        metadata.update(
            {
                "status": "failed",
                "updated_at": _now(),
                "error": error,
            }
        )
        self._write_record(metadata)
        return metadata

    def _write_record(self, metadata: dict[str, Any]) -> None:
        ingest_id = _normalize_ingest_id(str(metadata.get("ingest_id") or ""))
        record_dir = self.root_dir / ingest_id
        record_dir.mkdir(parents=True, exist_ok=True)
        _write_json(record_dir / "metadata.json", metadata)
        records = [item for item in self._read_index() if item.get("ingest_id") != ingest_id]
        records.append(metadata)
        _write_json(self.index_path, records)

    def _read_index(self) -> list[dict[str, Any]]:
        if not self.index_path.exists():
            return []
        data = _read_json(self.index_path)
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]


def _parse_mode(request: dict[str, Any]) -> str:
    parse_mode = str(request.get("parse_mode") or "").strip().lower()
    if parse_mode not in PARSE_MODE_CAPABILITY:
        raise DocumentIngestionError(
            "DOCUMENT_INGEST_INVALID_INPUT",
            "parse_mode must be one of: ocr, layout, vlm_async.",
            details={"parse_mode": parse_mode},
        )
    return parse_mode


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise DocumentIngestionError(
            "DOCUMENT_INGEST_INVALID_INPUT",
            f"{key} is required.",
            details={"field": key},
        )
    return value


def _build_invocation_payload(parse_mode: str, request: dict[str, Any]) -> dict[str, Any]:
    base = {
        "file_base64": str(request.get("file_base64") or ""),
        "media_type": str(request.get("media_type") or ""),
        "filename": str(request.get("filename") or ""),
    }
    if parse_mode == "ocr":
        return {
            **base,
            "visualize": bool(request.get("visualize", False)),
        }
    if parse_mode == "layout":
        return {
            **base,
            "output_format": str(request.get("output_format") or "markdown"),
            "include_tables": bool(request.get("include_tables", True)),
            "include_layout": bool(request.get("include_layout", True)),
            "max_pages": request.get("max_pages"),
        }
    return {
        **base,
        "operation": "submit",
        "task": str(request.get("task") or "summarize"),
        "question": str(request.get("question") or ""),
        "max_pages": request.get("max_pages"),
    }


def _request_summary(request: dict[str, Any]) -> dict[str, Any]:
    summary = {
        key: value
        for key, value in request.items()
        if key not in {"file_base64", "file", "raw"}
    }
    file_base64 = str(request.get("file_base64") or "")
    if file_base64:
        summary["file_base64_length"] = len(file_base64)
    return summary


def _provider_job(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": str(result.get("job_id") or ""),
        "status": str(result.get("status") or "unknown"),
        "progress": result.get("progress", 0),
        "error": result.get("error") if isinstance(result.get("error"), dict) else {},
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _normalize_ingest_id(ingest_id: str) -> str:
    normalized = str(ingest_id or "").strip()
    if not normalized or "/" in normalized or "\\" in normalized or ".." in normalized:
        raise DocumentIngestionNotFound(normalized)
    return normalized


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


_document_ingestion_service: DocumentIngestionService | None = None


def get_document_ingestion_service() -> DocumentIngestionService:
    global _document_ingestion_service
    if _document_ingestion_service is None:
        _document_ingestion_service = DocumentIngestionService()
    return _document_ingestion_service
