"""Helpers for appending planner-scoped unified run trace entries from non-chat services."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Optional


logger = logging.getLogger(__name__)


class RunTraceService:
    """Append unified run-trace records to the latest active planner item for one conversation."""

    def __init__(self, db):
        self.db = db

    def append_latest_active_item_trace(
        self,
        *,
        user_id: Optional[int],
        conversation_id: Optional[int],
        source: str,
        event_type: str,
        summary: str,
        detail: str = "",
        severity: str = "info",
        payload: Optional[dict[str, Any]] = None,
    ) -> bool:
        if self.db is None or user_id is None or conversation_id is None:
            user_id = self._resolve_user_id(user_id=user_id, conversation_id=conversation_id)
        if self.db is None or user_id is None or conversation_id is None:
            return False

        try:
            planner_service = self._get_planner_service()(self.db)
            plan = planner_service.get_latest_plan_for_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
            )
            if plan is None:
                return False

            item = planner_service.get_active_item(plan=plan)
            if item is None:
                return False

            self._get_scheduler_service()(self.db).append_run_trace_event(
                plan=plan,
                item_id=item.id,
                source=source,
                event_type=event_type,
                summary=summary,
                detail=detail,
                severity=severity,
                payload=payload,
            )
            return True
        except Exception as exc:  # pragma: no cover - defensive runtime logging
            logger.warning(f"[RunTraceService] 追加 Trace 失败: {exc}")
            return False

    def append_latest_active_item_audit(
        self,
        *,
        user_id: Optional[int],
        conversation_id: Optional[int],
        event_type: str,
        content: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> bool:
        if self.db is None or user_id is None or conversation_id is None:
            user_id = self._resolve_user_id(user_id=user_id, conversation_id=conversation_id)
        if self.db is None or user_id is None or conversation_id is None:
            return False

        try:
            planner_service = self._get_planner_service()(self.db)
            plan = planner_service.get_latest_plan_for_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
            )
            if plan is None:
                return False

            item = planner_service.get_active_item(plan=plan)
            if item is None:
                return False

            self._get_scheduler_service()(self.db).append_audit_event(
                plan=plan,
                item_id=item.id,
                event_type=event_type,
                content=content,
                payload=payload,
            )
            return True
        except Exception as exc:  # pragma: no cover - defensive runtime logging
            logger.warning(f"[RunTraceService] 追加 Audit 失败: {exc}")
            return False

    def build_snapshot_ref(
        self,
        *,
        source: str,
        event_type: str,
        conversation_id: Optional[int],
        generated_at: Optional[str] = None,
    ) -> dict[str, Any]:
        timestamp = str(generated_at or datetime.now(timezone.utc).isoformat())
        source_key = str(source or "governance").strip().upper()[:4] or "GOV"
        event_key = str(event_type or "event").strip().replace(" ", "_").upper()[:12] or "EVENT"
        conversation_key = str(conversation_id if conversation_id is not None else "NA")
        compact_time = (
            timestamp.replace("-", "")
            .replace(":", "")
            .replace("T", "")
            .replace("Z", "")
            .replace("+00:00", "")
            .replace(".", "")
        )[:14]
        snapshot_id = f"{source_key}-{event_key}-{conversation_key}-{compact_time or 'NA'}"
        return {
            "snapshot_id": snapshot_id,
            "generated_at": timestamp,
            "conversation_id": conversation_id,
            "source": source,
            "event_type": event_type,
        }

    def _resolve_user_id(self, *, user_id: Optional[int], conversation_id: Optional[int]) -> Optional[int]:
        if user_id is not None:
            return user_id
        if self.db is None or conversation_id is None:
            return None
        try:
            conversation = (
                self.db.query(self._get_conversation_model())
                .filter(self._get_conversation_model().id == conversation_id)
                .first()
            )
        except Exception as exc:  # pragma: no cover - defensive runtime logging
            logger.warning(f"[RunTraceService] 解析会话 owner 失败: {exc}")
            return None
        return getattr(conversation, "user_id", None) if conversation is not None else None

    def _get_planner_service(self):
        try:
            from services.planner_service import PlannerService
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.services.planner_service import PlannerService
        return PlannerService

    def _get_scheduler_service(self):
        try:
            from services.scheduler_service import SchedulerService
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.services.scheduler_service import SchedulerService
        return SchedulerService

    def _get_conversation_model(self):
        try:
            from models import Conversation
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import Conversation
        return Conversation


def get_run_trace_service(db) -> RunTraceService:
    return RunTraceService(db)
