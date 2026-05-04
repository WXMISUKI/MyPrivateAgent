"""Planner/Todo service for the reusable agent framework demo."""

from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List, Optional

try:
    from models import PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus
try:
    from services.scheduler_service import SchedulerService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.scheduler_service import SchedulerService


VALID_PLAN_STATUSES = {status.value for status in PlanStatus}
VALID_HANDOFF_STATUSES = {status.value for status in PlanHandoffStatus}


class PlannerService:
    """Application service for minimal planner/todo management."""

    def __init__(self, db):
        self.db = db

    def list_plans(self, *, user_id: int, conversation_id: Optional[int] = None, limit: int = 20) -> List[PlanRunRecord]:
        query = self.db.query(PlanRunRecord).filter(PlanRunRecord.user_id == user_id)
        if conversation_id is not None:
            query = query.filter(PlanRunRecord.conversation_id == conversation_id)
        return query.order_by(PlanRunRecord.updated_at.desc()).limit(limit).all()

    def get_latest_plan_for_conversation(self, *, user_id: int, conversation_id: Optional[int]) -> Optional[PlanRunRecord]:
        if conversation_id is None:
            return None
        return (
            self.db.query(PlanRunRecord)
            .filter(
                PlanRunRecord.user_id == user_id,
                PlanRunRecord.conversation_id == conversation_id,
            )
            .order_by(PlanRunRecord.updated_at.desc())
            .first()
        )

    def get_plan(self, *, plan_id: int, user_id: int) -> Optional[PlanRunRecord]:
        return (
            self.db.query(PlanRunRecord)
            .filter(PlanRunRecord.id == plan_id, PlanRunRecord.user_id == user_id)
            .first()
        )

    def create_plan(
        self,
        *,
        user_id: int,
        objective: str,
        conversation_id: Optional[int] = None,
        source: str = "manual",
        items: Optional[Iterable[dict]] = None,
    ) -> PlanRunRecord:
        normalized_objective = str(objective or "").strip()
        if not normalized_objective:
            raise ValueError("objective 不能为空")

        plan = PlanRunRecord(
            user_id=user_id,
            conversation_id=conversation_id,
            objective=normalized_objective,
            source=(source or "manual").strip() or "manual",
            status=PlanStatus.PENDING,
            summary="等待执行",
            plan_metadata={"version": 1, "kind": "planner_todo"},
        )
        self.db.add(plan)
        self.db.flush()

        for index, item in enumerate(items or [], start=1):
            self._create_plan_item(
                plan_id=plan.id,
                title=item.get("title", ""),
                details=item.get("details"),
                status=item.get("status", PlanStatus.PENDING.value),
                owner=item.get("owner"),
                agent_role=item.get("agent_role"),
                agent_id=item.get("agent_id"),
                handoff_status=item.get("handoff_status", PlanHandoffStatus.UNASSIGNED.value),
                step_order=item.get("step_order") or index,
            )

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def generate_plan(
        self,
        *,
        user_id: int,
        objective: str,
        conversation_id: Optional[int] = None,
        source: str = "generated",
    ) -> PlanRunRecord:
        generated_items = self._generate_plan_items(objective)
        return self.create_plan(
            user_id=user_id,
            objective=objective,
            conversation_id=conversation_id,
            source=source,
            items=generated_items,
        )

    def update_plan(
        self,
        *,
        plan: PlanRunRecord,
        objective: Optional[str] = None,
        summary: Optional[str] = None,
        status: Optional[str] = None,
    ) -> PlanRunRecord:
        if objective is not None:
            normalized = str(objective).strip()
            if not normalized:
                raise ValueError("objective 不能为空")
            plan.objective = normalized
        if summary is not None:
            plan.summary = str(summary).strip() or None
        if status is not None:
            plan.status = self._normalize_status(status)

        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def add_plan_item(
        self,
        *,
        plan: PlanRunRecord,
        title: str,
        details: Optional[str] = None,
        status: str = PlanStatus.PENDING.value,
        owner: Optional[str] = None,
        agent_role: Optional[str] = None,
        agent_id: Optional[str] = None,
        handoff_status: str = PlanHandoffStatus.UNASSIGNED.value,
        required_capabilities: Optional[Iterable[str]] = None,
        step_order: Optional[int] = None,
    ) -> PlanRunRecord:
        next_order = step_order or (len(plan.items) + 1)
        self._create_plan_item(
            plan_id=plan.id,
            title=title,
            details=details,
            status=status,
            owner=owner,
            agent_role=agent_role,
            agent_id=agent_id,
            handoff_status=handoff_status,
            required_capabilities=required_capabilities,
            step_order=next_order,
        )
        self.db.flush()
        self.db.refresh(plan)
        self._resequence_items(plan)
        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def update_plan_item(
        self,
        *,
        plan: PlanRunRecord,
        item_id: int,
        title: Optional[str] = None,
        details: Optional[str] = None,
        status: Optional[str] = None,
        owner: Optional[str] = None,
        agent_role: Optional[str] = None,
        agent_id: Optional[str] = None,
        handoff_status: Optional[str] = None,
        required_capabilities: Optional[Iterable[str]] = None,
        step_order: Optional[int] = None,
    ) -> PlanRunRecord:
        item = self._ensure_plan_item(plan, item_id)

        if title is not None:
            normalized_title = str(title).strip()
            if not normalized_title:
                raise ValueError("title 不能为空")
            item.title = normalized_title
        if details is not None:
            item.details = str(details).strip() or None
        if owner is not None:
            item.owner = str(owner).strip() or None
        if agent_role is not None:
            item.agent_role = str(agent_role).strip() or None
        if agent_id is not None:
            item.agent_id = str(agent_id).strip() or None
        if handoff_status is not None:
            item.handoff_status = self._normalize_handoff_status(handoff_status)
        if required_capabilities is not None:
            item.item_metadata = dict(item.item_metadata or {})
            item.item_metadata["required_capabilities"] = self._normalize_capability_list(required_capabilities)
        if status is not None:
            normalized_status = self._normalize_status(status)
            item.status = normalized_status
            if normalized_status == PlanStatus.IN_PROGRESS:
                for other in plan.items:
                    if other.id != item.id and other.status == PlanStatus.IN_PROGRESS:
                        other.status = PlanStatus.PENDING
                plan.active_item_id = item.id
                if item.agent_role:
                    item.handoff_status = PlanHandoffStatus.EXECUTING
            elif plan.active_item_id == item.id and normalized_status != PlanStatus.IN_PROGRESS:
                plan.active_item_id = None
                if normalized_status == PlanStatus.COMPLETED and item.agent_role:
                    item.handoff_status = PlanHandoffStatus.MERGED
        if step_order is not None:
            item.step_order = max(1, int(step_order))
            self._resequence_items(plan)

        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def delete_plan_item(self, *, plan: PlanRunRecord, item_id: int) -> PlanRunRecord:
        item = self._ensure_plan_item(plan, item_id)
        if plan.active_item_id == item.id:
            plan.active_item_id = None
        self.db.delete(item)
        self.db.flush()
        self.db.refresh(plan)
        self._resequence_items(plan)
        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def serialize_plan(self, plan: PlanRunRecord) -> dict:
        progress = self._build_progress(plan.items)
        scheduler_service = SchedulerService(self.db)
        return {
            "id": plan.id,
            "user_id": plan.user_id,
            "conversation_id": plan.conversation_id,
            "objective": plan.objective,
            "source": plan.source,
            "status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
            "active_item_id": plan.active_item_id,
            "summary": plan.summary,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "items": [
                {
                    "id": item.id,
                    "plan_id": item.plan_id,
                    "step_order": item.step_order,
                    "title": item.title,
                    "details": item.details,
                    "status": item.status.value if hasattr(item.status, "value") else str(item.status),
                    "owner": item.owner,
                    "agent_role": item.agent_role,
                    "agent_id": item.agent_id,
                    "handoff_status": item.handoff_status.value if hasattr(item.handoff_status, "value") else str(item.handoff_status),
                    "required_capabilities": list((item.item_metadata or {}).get("required_capabilities", [])),
                    "scheduler_snapshot": scheduler_service.get_scheduler_snapshot(item),
                    "child_executions": scheduler_service.serialize_child_executions(item),
                    "merge_summary": scheduler_service.get_merge_summary(item),
                    "audit_trail": scheduler_service.get_audit_trail(item),
                    "run_trace": scheduler_service.get_run_trace(item),
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in sorted(plan.items, key=lambda row: row.step_order)
            ],
            "progress": progress,
        }

    def get_active_item(self, *, plan: Optional[PlanRunRecord]) -> Optional[PlanItemRecord]:
        if plan is None:
            return None

        active_item = next((item for item in plan.items if item.status == PlanStatus.IN_PROGRESS), None)
        if active_item is None and plan.active_item_id is not None:
            active_item = next((item for item in plan.items if item.id == plan.active_item_id), None)
        return active_item

    def begin_execution(self, *, plan: Optional[PlanRunRecord]) -> Optional[PlanRunRecord]:
        if plan is None:
            return None

        active_item = self.get_active_item(plan=plan)
        if active_item is None:
            active_item = next((item for item in sorted(plan.items, key=lambda row: row.step_order) if item.status == PlanStatus.PENDING), None)

        if active_item is None:
            return plan

        for item in plan.items:
            if item.id != active_item.id and item.status == PlanStatus.IN_PROGRESS:
                item.status = PlanStatus.PENDING

        active_item.status = PlanStatus.IN_PROGRESS
        if active_item.agent_role and active_item.agent_role != "general":
            if active_item.handoff_status == PlanHandoffStatus.UNASSIGNED:
                active_item.handoff_status = PlanHandoffStatus.READY
        plan.active_item_id = active_item.id
        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def prepare_handoff(self, *, plan: Optional[PlanRunRecord]) -> Optional[PlanRunRecord]:
        active_item = self.get_active_item(plan=plan)
        if active_item is None or not active_item.agent_role or active_item.agent_role == "general":
            return plan

        if not active_item.agent_id:
            active_item.agent_id = self._build_agent_id(plan=plan, item=active_item)
        active_item.handoff_status = PlanHandoffStatus.HANDED_OFF
        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def mark_handoff_executing(self, *, plan: Optional[PlanRunRecord]) -> Optional[PlanRunRecord]:
        active_item = self.get_active_item(plan=plan)
        if active_item is None or not active_item.agent_role or active_item.agent_role == "general":
            return plan

        if not active_item.agent_id:
            active_item.agent_id = self._build_agent_id(plan=plan, item=active_item)
        active_item.handoff_status = PlanHandoffStatus.EXECUTING
        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def complete_execution(
        self,
        *,
        plan: Optional[PlanRunRecord],
        note: Optional[str] = None,
    ) -> Optional[PlanRunRecord]:
        if plan is None:
            return None

        active_item = next((item for item in plan.items if item.status == PlanStatus.IN_PROGRESS), None)
        if active_item is None and plan.active_item_id is not None:
            active_item = next((item for item in plan.items if item.id == plan.active_item_id), None)

        if active_item is None:
            return plan

        active_item.status = PlanStatus.COMPLETED
        if active_item.agent_role and active_item.agent_role != "general":
            if not active_item.agent_id:
                active_item.agent_id = self._build_agent_id(plan=plan, item=active_item)
            active_item.handoff_status = PlanHandoffStatus.MERGED
        if note:
            details = (active_item.details or "").strip()
            suffix = f"\n\n执行结果：{note.strip()}"
            active_item.details = f"{details}{suffix}".strip() if details else f"执行结果：{note.strip()}"

        plan.active_item_id = None
        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def block_active_item(
        self,
        *,
        plan: Optional[PlanRunRecord],
        reason: str,
        missing_capabilities: Optional[Iterable[str]] = None,
        unavailable_capabilities: Optional[Iterable[str]] = None,
    ) -> Optional[PlanRunRecord]:
        if plan is None:
            return None

        active_item = self.get_active_item(plan=plan)
        if active_item is None:
            return plan

        active_item.status = PlanStatus.BLOCKED
        active_item.item_metadata = dict(active_item.item_metadata or {})
        active_item.item_metadata["capability_guard"] = {
            "reason": str(reason or "").strip(),
            "missing_capabilities": self._normalize_capability_list(missing_capabilities),
            "unavailable_capabilities": self._normalize_capability_list(unavailable_capabilities),
        }

        details = (active_item.details or "").strip()
        reason_text = str(reason or "").strip()
        suffix = f"\n\n阻塞原因：{reason_text}" if reason_text else ""
        if suffix:
            active_item.details = f"{details}{suffix}".strip() if details else suffix.strip()

        plan.active_item_id = None
        self._refresh_plan_progress(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def _ensure_plan_item(self, plan: PlanRunRecord, item_id: int) -> PlanItemRecord:
        for item in plan.items:
            if item.id == item_id:
                return item
        raise ValueError("计划项不存在")

    def _create_plan_item(
        self,
        *,
        plan_id: int,
        title: str,
        details: Optional[str],
        status: str,
        owner: Optional[str],
        agent_role: Optional[str],
        agent_id: Optional[str],
        handoff_status: str,
        required_capabilities: Optional[Iterable[str]],
        step_order: int,
    ) -> PlanItemRecord:
        normalized_title = str(title or "").strip()
        if not normalized_title:
            raise ValueError("title 不能为空")

        item = PlanItemRecord(
            plan_id=plan_id,
            step_order=max(1, int(step_order)),
            title=normalized_title,
            details=str(details).strip() if details else None,
            status=self._normalize_status(status),
            owner=str(owner).strip() if owner else None,
            agent_role=str(agent_role).strip() if agent_role else None,
            agent_id=str(agent_id).strip() if agent_id else None,
            handoff_status=self._normalize_handoff_status(handoff_status),
            item_metadata={
                "generated": True,
                "required_capabilities": self._normalize_capability_list(required_capabilities),
            },
        )
        self.db.add(item)
        self.db.flush()
        return item

    def _resequence_items(self, plan: PlanRunRecord) -> None:
        ordered = sorted(plan.items, key=lambda item: (item.step_order, item.id))
        for index, item in enumerate(ordered, start=1):
            item.step_order = index

    def _refresh_plan_progress(self, plan: PlanRunRecord) -> None:
        progress = self._build_progress(plan.items)
        if progress["total"] == 0:
            plan.status = PlanStatus.PENDING
            plan.summary = "尚未拆解步骤"
            plan.active_item_id = None
            return

        if progress["in_progress"] > 0:
            plan.status = PlanStatus.IN_PROGRESS
            active_item = next((item for item in plan.items if item.status == PlanStatus.IN_PROGRESS), None)
            plan.active_item_id = active_item.id if active_item else None
            plan.summary = f"执行中：{progress['completed']}/{progress['total']} 已完成"
            return

        plan.active_item_id = None
        if progress["completed"] == progress["total"]:
            plan.status = PlanStatus.COMPLETED
            plan.summary = f"已完成：{progress['completed']}/{progress['total']}"
        elif progress["blocked"] > 0:
            plan.status = PlanStatus.BLOCKED
            plan.summary = f"存在阻塞：{progress['blocked']} 项"
        elif progress["cancelled"] == progress["total"]:
            plan.status = PlanStatus.CANCELLED
            plan.summary = "计划已取消"
        else:
            plan.status = PlanStatus.PENDING
            plan.summary = f"待执行：{progress['pending']} 项"

    def _build_progress(self, items: Iterable[PlanItemRecord]) -> dict:
        counter = Counter()
        total = 0
        for item in items:
            total += 1
            key = item.status.value if hasattr(item.status, "value") else str(item.status)
            counter[key] += 1

        return {
            "total": total,
            "pending": counter.get(PlanStatus.PENDING.value, 0),
            "in_progress": counter.get(PlanStatus.IN_PROGRESS.value, 0),
            "completed": counter.get(PlanStatus.COMPLETED.value, 0),
            "blocked": counter.get(PlanStatus.BLOCKED.value, 0),
            "cancelled": counter.get(PlanStatus.CANCELLED.value, 0),
        }

    def _normalize_status(self, status: str) -> PlanStatus:
        normalized = str(status or "").strip().lower()
        if normalized not in VALID_PLAN_STATUSES:
            raise ValueError("status 无效")
        return PlanStatus(normalized)

    def _normalize_handoff_status(self, status: str) -> PlanHandoffStatus:
        normalized = str(status or "").strip().lower()
        if normalized not in VALID_HANDOFF_STATUSES:
            raise ValueError("handoff_status 无效")
        return PlanHandoffStatus(normalized)

    def _generate_plan_items(self, objective: str) -> List[dict]:
        normalized = str(objective or "").strip()
        if not normalized:
            raise ValueError("objective 不能为空")

        fragments = [
            fragment.strip(" ;；。.\t")
            for fragment in re.split(r"[\n；;。]+", normalized)
            if fragment.strip()
        ]
        candidate_steps = [fragment for fragment in fragments if len(fragment) >= 4]

        if len(candidate_steps) >= 2:
            return [
                {
                    "title": self._as_action_title(step),
                    "details": step,
                    "status": PlanStatus.PENDING.value,
                    **self._suggest_assignment(step),
                }
                for step in candidate_steps[:8]
            ]

        return [
            {
                "title": "明确目标与边界",
                "details": normalized,
                "status": PlanStatus.PENDING.value,
                **self._suggest_assignment("分析目标和范围"),
            },
            {
                "title": "盘点现有实现与约束",
                "details": "阅读相关代码、配置和依赖，识别风险点。",
                "status": PlanStatus.PENDING.value,
                **self._suggest_assignment("阅读代码和架构分析"),
            },
            {
                "title": "拆解执行步骤",
                "details": "把目标拆成可验证的前后端/服务端子任务。",
                "status": PlanStatus.PENDING.value,
                **self._suggest_assignment("制定计划和任务拆解"),
            },
            {
                "title": "实现并验证关键路径",
                "details": "优先完成主链路功能并执行最小验证。",
                "status": PlanStatus.PENDING.value,
                **self._suggest_assignment("实现代码和测试验证"),
            },
            {
                "title": "整理结果与后续项",
                "details": "记录完成情况、剩余风险和下一步。",
                "status": PlanStatus.PENDING.value,
                **self._suggest_assignment("汇总结果和文档整理"),
            },
        ]

    def _as_action_title(self, text: str) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        compact = compact.lstrip("-0123456789.、)）(")
        if len(compact) <= 24:
            return compact
        return compact[:24].rstrip() + "..."

    def _suggest_assignment(self, text: str) -> dict:
        lowered = str(text or "").lower()
        role = "general"
        owner = "主智能体"
        required_capabilities: list[str] = []

        if any(keyword in lowered for keyword in ["前端", "ui", "vue", "页面", "样式", "组件", "frontend"]):
            role = "frontend"
            owner = "前端子智能体"
        elif any(keyword in lowered for keyword in ["后端", "接口", "数据库", "service", "router", "backend", "api"]):
            role = "backend"
            owner = "后端子智能体"
        elif any(keyword in lowered for keyword in ["测试", "回归", "验证", "test", "smoke"]):
            role = "qa"
            owner = "测试子智能体"
        elif any(keyword in lowered for keyword in ["文档", "日志", "说明", "readme", "docs"]):
            role = "docs"
            owner = "文档子智能体"
        elif any(keyword in lowered for keyword in ["规划", "拆解", "分析", "plan", "todo"]):
            role = "planner"
            owner = "规划子智能体"

        if any(keyword in lowered for keyword in ["文件", "filesystem", "目录", "代码库", "readme", "仓库"]):
            required_capabilities.append("filesystem.read")
        if any(keyword in lowered for keyword in ["搜索", "检索", "query", "知识库", "文档查询"]):
            required_capabilities.append("search.query")
        if any(keyword in lowered for keyword in ["写入", "保存", "生成文件", "落盘"]):
            required_capabilities.append("filesystem.write")

        handoff_status = PlanHandoffStatus.READY.value if role != "general" else PlanHandoffStatus.UNASSIGNED.value
        return {
            "owner": owner,
            "agent_role": role,
            "agent_id": None,
            "handoff_status": handoff_status,
            "required_capabilities": sorted(dict.fromkeys(required_capabilities)),
        }

    def _build_agent_id(self, *, plan: Optional[PlanRunRecord], item: PlanItemRecord) -> str:
        role = str(item.agent_role or "general").strip().lower() or "general"
        plan_id = getattr(plan, "id", None) or item.plan_id or "x"
        item_id = getattr(item, "id", None) or item.step_order or "x"
        return f"{role}-agent-p{plan_id}-i{item_id}"

    def _normalize_capability_list(self, values: Optional[Iterable[str]]) -> List[str]:
        normalized = []
        for value in values or []:
            text = str(value or "").strip()
            if text:
                normalized.append(text)
        return sorted(dict.fromkeys(normalized))
