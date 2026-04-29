"""Capability remediation status service."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from models import CapabilityRemediationRecord, CapabilityRemediationStatus
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import CapabilityRemediationRecord, CapabilityRemediationStatus


class RemediationStatusService:
    VALID_STATUSES = {
        CapabilityRemediationStatus.OPEN.value,
        CapabilityRemediationStatus.IN_PROGRESS.value,
        CapabilityRemediationStatus.BLOCKED.value,
        CapabilityRemediationStatus.DONE.value,
        CapabilityRemediationStatus.VERIFIED.value,
    }

    def __init__(self, db):
        self.db = db

    def list_statuses(self) -> List[Dict[str, Any]]:
        rows = (
            self.db.query(CapabilityRemediationRecord)
            .order_by(CapabilityRemediationRecord.updated_at.desc())
            .all()
        )
        return [self._serialize(row) for row in rows]

    def upsert_status(
        self,
        *,
        action_id: str,
        status: str,
        owner: str | None = None,
        module: str | None = None,
        note: str | None = None,
        updated_by: str | None = None,
    ) -> Dict[str, Any]:
        normalized_action_id = str(action_id or "").strip()
        normalized_status = str(status or "").strip().lower()
        if not normalized_action_id:
            raise ValueError("action_id 不能为空")
        if normalized_status not in self.VALID_STATUSES:
            raise ValueError("status 非法")

        row = (
            self.db.query(CapabilityRemediationRecord)
            .filter(CapabilityRemediationRecord.action_id == normalized_action_id)
            .first()
        )
        if row is None:
            row = CapabilityRemediationRecord(
                action_id=normalized_action_id,
                status=CapabilityRemediationStatus(normalized_status),
            )
            self.db.add(row)

        row.status = CapabilityRemediationStatus(normalized_status)
        if owner is not None:
            row.owner = str(owner).strip() or None
        if module is not None:
            row.module = str(module).strip() or None
        if note is not None:
            row.note = str(note).strip() or None
        if updated_by is not None:
            row.updated_by = str(updated_by).strip() or None

        self.db.commit()
        self.db.refresh(row)
        return self._serialize(row)

    def status_map(self) -> Dict[str, Dict[str, Any]]:
        return {item["action_id"]: item for item in self.list_statuses()}

    @staticmethod
    def _serialize(row: CapabilityRemediationRecord) -> Dict[str, Any]:
        return {
            "action_id": str(row.action_id),
            "status": str(row.status.value if hasattr(row.status, "value") else row.status),
            "owner": row.owner,
            "module": row.module,
            "note": row.note,
            "updated_by": row.updated_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }


def get_remediation_status_service(db) -> RemediationStatusService:
    return RemediationStatusService(db)
