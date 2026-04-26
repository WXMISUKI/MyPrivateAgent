"""Helpers for appending planner-scoped unified run trace entries from non-chat services."""

from __future__ import annotations

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


def get_run_trace_service(db) -> RunTraceService:
    return RunTraceService(db)
