"""Metadata-backed repository for scheduler runtime state."""

from __future__ import annotations

from typing import Optional

try:
    from models import PlanItemRecord
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.models import PlanItemRecord

class SchedulerRuntimeMetadataRepository:
    """Encapsulate scheduler runtime reads/writes stored in plan item metadata."""

    CHILD_GROUP_KEY = "child_execution_group"
    CHILD_ROLES_KEY = "child_roles"
    AUDIT_TRAIL_KEY = "audit_trail"
    RUN_TRACE_KEY = "run_trace"
    REQUIRED_CAPABILITIES_KEY = "required_capabilities"

    def get_persistence_descriptor(self) -> dict:
        return {
            "backend": "metadata_adapter",
            "scope": "plan_item_metadata",
            "durable": True,
            "migration_ready": False,
        }

    def get_metadata(self, item: Optional[PlanItemRecord]) -> dict:
        if item is None:
            return {}
        metadata = getattr(item, "item_metadata", None) or {}
        return dict(metadata) if isinstance(metadata, dict) else {}

    def save_metadata(self, item: Optional[PlanItemRecord], metadata: Optional[dict]) -> dict:
        normalized = dict(metadata or {})
        if item is not None:
            item.item_metadata = normalized
        return normalized

    def touch_metadata(self, item: Optional[PlanItemRecord]) -> dict:
        return self.save_metadata(item, self.get_metadata(item))

    def get_required_capabilities(self, item: Optional[PlanItemRecord]) -> list[str]:
        metadata = self.get_metadata(item)
        capabilities = metadata.get(self.REQUIRED_CAPABILITIES_KEY) or []
        return [str(capability) for capability in capabilities if str(capability or "").strip()]

    def get_child_roles(self, item: Optional[PlanItemRecord]) -> list[str]:
        metadata = self.get_metadata(item)
        roles = metadata.get(self.CHILD_ROLES_KEY) or []
        return [str(role) for role in roles if str(role or "").strip()]

    def save_child_roles(self, item: Optional[PlanItemRecord], roles: list[str]) -> list[str]:
        metadata = self.get_metadata(item)
        metadata[self.CHILD_ROLES_KEY] = list(roles or [])
        self.save_metadata(item, metadata)
        return list(metadata[self.CHILD_ROLES_KEY])

    def get_child_group(self, item: Optional[PlanItemRecord]) -> Optional[dict]:
        metadata = self.get_metadata(item)
        group = metadata.get(self.CHILD_GROUP_KEY)
        return dict(group) if isinstance(group, dict) else None

    def save_child_group(self, item: Optional[PlanItemRecord], group: Optional[dict]) -> Optional[dict]:
        metadata = self.get_metadata(item)
        if group is None:
            metadata.pop(self.CHILD_GROUP_KEY, None)
            self.save_metadata(item, metadata)
            return None
        normalized = dict(group)
        metadata[self.CHILD_GROUP_KEY] = normalized
        self.save_metadata(item, metadata)
        return normalized

    def list_children(self, item: Optional[PlanItemRecord]) -> list[dict]:
        group = self.get_child_group(item) or {}
        children = group.get("children") or []
        return [dict(child) for child in children if isinstance(child, dict)]

    def find_child_group_entry(
        self,
        item: Optional[PlanItemRecord],
        child_execution_id: str,
    ) -> tuple[Optional[dict], Optional[dict]]:
        normalized_child_execution_id = str(child_execution_id or "").strip()
        if not normalized_child_execution_id:
            return None, None
        group = self.get_child_group(item)
        if group is None:
            return None, None
        children = []
        target_index = None
        for index, child in enumerate(group.get("children") or []):
            if not isinstance(child, dict):
                continue
            child_copy = dict(child)
            children.append(child_copy)
            if str(child_copy.get("child_execution_id") or "").strip() == normalized_child_execution_id:
                target_index = len(children) - 1
        group["children"] = children
        if target_index is None:
            return group, None
        return group, children[target_index]

    def get_audit_trail(self, item: Optional[PlanItemRecord]) -> list[dict]:
        metadata = self.get_metadata(item)
        trail = metadata.get(self.AUDIT_TRAIL_KEY) or []
        return [dict(entry) for entry in trail if isinstance(entry, dict)]

    def append_audit_trail(self, item: Optional[PlanItemRecord], entry: dict, *, limit: int = 50) -> list[dict]:
        metadata = self.get_metadata(item)
        trail = self.get_audit_trail(item)
        trail.append(dict(entry or {}))
        metadata[self.AUDIT_TRAIL_KEY] = trail[-max(1, int(limit)) :]
        self.save_metadata(item, metadata)
        return metadata[self.AUDIT_TRAIL_KEY]

    def get_run_trace(self, item: Optional[PlanItemRecord]) -> list[dict]:
        metadata = self.get_metadata(item)
        trace = metadata.get(self.RUN_TRACE_KEY) or []
        return [dict(entry) for entry in trace if isinstance(entry, dict)]

    def append_run_trace(self, item: Optional[PlanItemRecord], entry: dict, *, limit: int = 100) -> list[dict]:
        metadata = self.get_metadata(item)
        trace = self.get_run_trace(item)
        trace.append(dict(entry or {}))
        metadata[self.RUN_TRACE_KEY] = trace[-max(1, int(limit)) :]
        self.save_metadata(item, metadata)
        return metadata[self.RUN_TRACE_KEY]


def get_scheduler_runtime_repository() -> SchedulerRuntimeMetadataRepository:
    return SchedulerRuntimeMetadataRepository()
