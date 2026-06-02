"""Local document artifact persistence for OCR/Layout/VLM outputs."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from config import LOCAL_DATA_DIR
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import LOCAL_DATA_DIR


class DocumentArtifactNotFound(LookupError):
    def __init__(self, artifact_id: str):
        super().__init__(f"Document artifact not found: {artifact_id}")
        self.artifact_id = artifact_id


@dataclass(frozen=True)
class PersistedDocumentArtifact:
    metadata: dict[str, Any]
    payload: dict[str, Any]


class DocumentArtifactService:
    def __init__(self, root_dir: Path | None = None):
        self.root_dir = Path(root_dir or (LOCAL_DATA_DIR / "document_artifacts")).resolve()
        self.index_path = self.root_dir / "index.json"

    def persist(self, request: dict[str, Any]) -> PersistedDocumentArtifact:
        capability_id = _required_text(request, "capability_id")
        provider = _required_text(request, "provider")
        result = request.get("result")
        if not isinstance(result, dict):
            raise ValueError("result must be an object.")

        include_raw = bool(request.get("include_raw", False))
        payload = _compact_payload(capability_id, result, include_raw=include_raw)
        content_hash = _content_hash(payload)
        artifact_id = f"doc-artifact-{uuid.uuid4().hex}"
        now = datetime.now(timezone.utc).isoformat()
        warnings = _extract_warnings(payload)
        metadata = {
            "artifact_id": artifact_id,
            "artifact_type": _artifact_type(capability_id),
            "source_filename": str(request.get("source_filename") or ""),
            "media_type": str(request.get("media_type") or ""),
            "capability_id": capability_id,
            "provider": provider,
            "created_at": now,
            "content_hash": content_hash,
            "summary": _derive_summary(capability_id, payload),
            "warnings": warnings,
            "payload_path": f"{artifact_id}/payload.json",
            "raw_included": include_raw,
        }

        artifact_dir = self.root_dir / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=False)
        _write_json(artifact_dir / "metadata.json", metadata)
        _write_json(artifact_dir / "payload.json", payload)
        self._append_index(metadata)
        return PersistedDocumentArtifact(metadata=metadata, payload=payload)

    def get(self, artifact_id: str) -> PersistedDocumentArtifact:
        normalized = _normalize_artifact_id(artifact_id)
        artifact_dir = self.root_dir / normalized
        metadata_path = artifact_dir / "metadata.json"
        payload_path = artifact_dir / "payload.json"
        if not metadata_path.exists() or not payload_path.exists():
            raise DocumentArtifactNotFound(normalized)
        return PersistedDocumentArtifact(
            metadata=_read_json(metadata_path),
            payload=_read_json(payload_path),
        )

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        records = self._read_index()
        sorted_records = sorted(records, key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return sorted_records[: max(1, min(int(limit), 500))]

    def _append_index(self, metadata: dict[str, Any]) -> None:
        self.root_dir.mkdir(parents=True, exist_ok=True)
        records = self._read_index()
        records = [item for item in records if item.get("artifact_id") != metadata.get("artifact_id")]
        records.append(metadata)
        _write_json(self.index_path, records)

    def _read_index(self) -> list[dict[str, Any]]:
        if not self.index_path.exists():
            return []
        data = _read_json(self.index_path)
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required.")
    return value


def _compact_payload(capability_id: str, result: dict[str, Any], *, include_raw: bool = False) -> dict[str, Any]:
    cleaned = _clone_without_raw(result) if not include_raw else _json_safe(result)
    if capability_id == "document.ocr.extract":
        return {
            "text": str(cleaned.get("text") or ""),
            "pages": _list_or_empty(cleaned.get("pages")),
            "blocks": _list_or_empty(cleaned.get("blocks")),
            "tables": _list_or_empty(cleaned.get("tables")),
            "artifacts": _list_or_empty(cleaned.get("artifacts")),
            "warnings": _string_list(cleaned.get("warnings")),
            **({"raw": cleaned.get("raw")} if include_raw and "raw" in cleaned else {}),
        }
    if capability_id == "document.layout.parse":
        return {
            "markdown": str(cleaned.get("markdown") or ""),
            "elements": _list_or_empty(cleaned.get("elements")),
            "tables": _list_or_empty(cleaned.get("tables")),
            "pages": _list_or_empty(cleaned.get("pages")),
            "artifacts": _list_or_empty(cleaned.get("artifacts")),
            "warnings": _string_list(cleaned.get("warnings")),
            **({"raw": cleaned.get("raw")} if include_raw and "raw" in cleaned else {}),
        }
    if capability_id in {"document.vlm.parse", "document.vlm.parse.async"}:
        return {
            "summary": str(cleaned.get("summary") or ""),
            "sections": _list_or_empty(cleaned.get("sections")),
            "entities": _list_or_empty(cleaned.get("entities")),
            "answers": _list_or_empty(cleaned.get("answers")),
            "evidence": _list_or_empty(cleaned.get("evidence")),
            "warnings": _string_list(cleaned.get("warnings")),
            **({"raw": cleaned.get("raw")} if include_raw and "raw" in cleaned else {}),
        }
    return cleaned


def _clone_without_raw(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _clone_without_raw(v) for k, v in value.items() if str(k) != "raw"}
    if isinstance(value, list):
        return [_clone_without_raw(item) for item in value]
    return _json_safe(value)


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        return str(value)


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _extract_warnings(payload: dict[str, Any]) -> list[str]:
    return _string_list(payload.get("warnings"))


def _derive_summary(capability_id: str, payload: dict[str, Any]) -> str:
    if capability_id == "document.ocr.extract":
        return _truncate(str(payload.get("text") or ""))
    if capability_id == "document.layout.parse":
        return _truncate(str(payload.get("markdown") or ""))
    return _truncate(str(payload.get("summary") or ""))


def _truncate(value: str, limit: int = 240) -> str:
    compact = " ".join(str(value or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _artifact_type(capability_id: str) -> str:
    if capability_id == "document.ocr.extract":
        return "document.ocr"
    if capability_id == "document.layout.parse":
        return "document.layout"
    if capability_id in {"document.vlm.parse", "document.vlm.parse.async"}:
        return "document.vlm"
    return "document.capability"


def _content_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_artifact_id(artifact_id: str) -> str:
    normalized = str(artifact_id or "").strip()
    if not normalized or "/" in normalized or "\\" in normalized or ".." in normalized:
        raise DocumentArtifactNotFound(normalized)
    return normalized


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


_document_artifact_service: DocumentArtifactService | None = None


def get_document_artifact_service() -> DocumentArtifactService:
    global _document_artifact_service
    if _document_artifact_service is None:
        _document_artifact_service = DocumentArtifactService()
    return _document_artifact_service
