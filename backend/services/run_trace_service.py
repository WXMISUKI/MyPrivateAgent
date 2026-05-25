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
            return self.append_runtime_trace(
                user_id=user_id,
                conversation_id=conversation_id,
                source=source,
                event_type=event_type,
                summary=summary,
                detail=detail,
                severity=severity,
                payload=payload,
            )
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
            return self.append_runtime_audit(
                user_id=user_id,
                conversation_id=conversation_id,
                event_type=event_type,
                content=content,
                payload=payload,
            )
        except Exception as exc:  # pragma: no cover - defensive runtime logging
            logger.warning(f"[RunTraceService] 追加 Audit 失败: {exc}")
            return False

    def append_runtime_trace(
        self,
        *,
        user_id: Optional[int],
        conversation_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        item_id: Optional[int] = None,
        run_id: Optional[str] = None,
        child_run_id: Optional[str] = None,
        source: str,
        event_type: str,
        summary: str,
        detail: str = "",
        severity: str = "info",
        payload: Optional[dict[str, Any]] = None,
    ) -> bool:
        if self.db is None or user_id is None:
            user_id = self._resolve_user_id(user_id=user_id, conversation_id=conversation_id)
        if self.db is None or user_id is None:
            return False
        target = self._resolve_plan_item_target(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
            prefer_active_when_unspecified=not self._has_explicit_runtime_scope(
                plan_id=plan_id,
                item_id=item_id,
                run_id=run_id,
                child_run_id=child_run_id,
            ),
        )
        if target is None:
            return False
        plan, item = target
        payload_data = self._build_scoped_payload(
            payload=payload,
            plan=plan,
            item=item,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
        )
        self._get_scheduler_service()(self.db).append_run_trace_event(
            plan=plan,
            item_id=item.id,
            source=source,
            event_type=event_type,
            summary=summary,
            detail=detail,
            severity=severity,
            payload=payload_data,
        )
        return True

    def has_runtime_trace_fingerprint(
        self,
        *,
        user_id: Optional[int],
        conversation_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        item_id: Optional[int] = None,
        run_id: Optional[str] = None,
        child_run_id: Optional[str] = None,
        source: str,
        event_type: str,
        fingerprint: str,
        dedupe_key: Optional[str] = None,
        limit: int = 50,
    ) -> bool:
        normalized_fingerprint = str(fingerprint or "").strip()
        normalized_dedupe_key = str(dedupe_key or "").strip()
        if not normalized_fingerprint and not normalized_dedupe_key:
            return False
        return self._has_runtime_trace_payload_match(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
            source=source,
            event_type=event_type,
            dedupe_key=normalized_dedupe_key or None,
            fingerprint=normalized_fingerprint or None,
            limit=limit,
        )

    def has_runtime_trace_dedupe_key(
        self,
        *,
        user_id: Optional[int],
        conversation_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        item_id: Optional[int] = None,
        run_id: Optional[str] = None,
        child_run_id: Optional[str] = None,
        source: str,
        event_type: str,
        dedupe_key: str,
        limit: int = 50,
    ) -> bool:
        normalized_dedupe_key = str(dedupe_key or "").strip()
        if not normalized_dedupe_key:
            return False
        return self._has_runtime_trace_payload_match(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
            source=source,
            event_type=event_type,
            dedupe_key=normalized_dedupe_key,
            fingerprint=None,
            limit=limit,
        )

    def _has_runtime_trace_payload_match(
        self,
        *,
        user_id: Optional[int],
        conversation_id: Optional[int],
        plan_id: Optional[int],
        item_id: Optional[int],
        run_id: Optional[str],
        child_run_id: Optional[str],
        source: str,
        event_type: str,
        dedupe_key: Optional[str] = None,
        fingerprint: Optional[str] = None,
        limit: int = 50,
    ) -> bool:
        normalized_dedupe_key = str(dedupe_key or "").strip()
        normalized_fingerprint = str(fingerprint or "").strip()
        if not normalized_dedupe_key and not normalized_fingerprint:
            return False
        if self.db is None or user_id is None:
            user_id = self._resolve_user_id(user_id=user_id, conversation_id=conversation_id)
        if self.db is None or user_id is None:
            return False
        target = self._resolve_plan_item_target(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
            prefer_active_when_unspecified=not self._has_explicit_runtime_scope(
                plan_id=plan_id,
                item_id=item_id,
                run_id=run_id,
                child_run_id=child_run_id,
            ),
        )
        if target is None:
            return False
        _, item = target
        events = self._get_scheduler_service()(self.db).filter_run_trace(
            item,
            run_id=run_id,
            child_run_id=child_run_id,
            source=source,
            event_type=event_type,
            limit=limit,
        )
        for event in events:
            payload = event.get("payload") if isinstance(event, dict) else {}
            if not isinstance(payload, dict):
                continue
            if normalized_dedupe_key and str(payload.get("dedupe_key") or "").strip() == normalized_dedupe_key:
                return True
            if normalized_fingerprint and str(payload.get("fingerprint") or "").strip() == normalized_fingerprint:
                return True
        return False

    def append_runtime_audit(
        self,
        *,
        user_id: Optional[int],
        conversation_id: Optional[int] = None,
        plan_id: Optional[int] = None,
        item_id: Optional[int] = None,
        run_id: Optional[str] = None,
        child_run_id: Optional[str] = None,
        event_type: str,
        content: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> bool:
        if self.db is None or user_id is None:
            user_id = self._resolve_user_id(user_id=user_id, conversation_id=conversation_id)
        if self.db is None or user_id is None:
            return False
        target = self._resolve_plan_item_target(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
            prefer_active_when_unspecified=not self._has_explicit_runtime_scope(
                plan_id=plan_id,
                item_id=item_id,
                run_id=run_id,
                child_run_id=child_run_id,
            ),
        )
        if target is None:
            return False
        plan, item = target
        payload_data = self._build_scoped_payload(
            payload=payload,
            plan=plan,
            item=item,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
        )
        self._get_scheduler_service()(self.db).append_audit_event(
            plan=plan,
            item_id=item.id,
            event_type=event_type,
            content=content,
            payload=payload_data,
        )
        return True

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

    def _resolve_plan_item_target(
        self,
        *,
        user_id: int,
        conversation_id: Optional[int],
        plan_id: Optional[int],
        item_id: Optional[int],
        run_id: Optional[str],
        child_run_id: Optional[str],
        prefer_active_when_unspecified: bool,
    ) -> Optional[tuple[Any, Any]]:
        planner_service = self._get_planner_service()(self.db)
        plan, item = planner_service.resolve_runtime_target(
            user_id=user_id,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            child_run_id=child_run_id,
        )
        if plan is not None and item is not None:
            return plan, item
        if not prefer_active_when_unspecified:
            return None
        plan = planner_service.get_latest_plan_for_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )
        if plan is None:
            return None
        item = planner_service.get_active_item(plan=plan)
        if item is None:
            return None
        return plan, item

    def _has_explicit_runtime_scope(
        self,
        *,
        plan_id: Optional[int],
        item_id: Optional[int],
        run_id: Optional[str],
        child_run_id: Optional[str],
    ) -> bool:
        if plan_id is not None:
            return True
        if item_id is not None:
            return True
        if str(run_id or "").strip():
            return True
        if str(child_run_id or "").strip():
            return True
        return False

    def _build_scoped_payload(
        self,
        *,
        payload: Optional[dict[str, Any]],
        plan: Any,
        item: Any,
        plan_id: Optional[int],
        item_id: Optional[int],
        run_id: Optional[str],
        child_run_id: Optional[str],
    ) -> dict[str, Any]:
        payload_data = dict(payload or {})
        if plan is not None and item is not None:
            payload_data["plan_id"] = getattr(plan, "id", None)
            payload_data["plan_item_id"] = getattr(item, "id", None)
        if run_id:
            payload_data["run_id"] = run_id
        if child_run_id:
            payload_data["child_run_id"] = child_run_id
        return payload_data

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
