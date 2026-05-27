"""Runtime Surface profile request context assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RuntimeSurfaceProfileContext:
    """Scoped runtime profile context used by the top-level profile assembler."""

    db: Any = None
    conversation_id: int | None = None
    plan_id: int | None = None
    item_id: int | None = None
    query_id: str | None = None
    run_id: str | None = None
    parent_run_id: str | None = None
    child_run_id: str | None = None
    scheduler_run_id: str | None = None
    runtime_scope: Dict[str, Any] | None = None
    recovery_target_run_id: str = ""


class RuntimeSurfaceProfileContextAssembler:
    """Assemble runtime profile request scope without building profile sections."""

    @classmethod
    def assemble(
        cls,
        service: Any,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
        query_id: str | None = None,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        child_run_id: str | None = None,
        scheduler_run_id: str | None = None,
    ) -> RuntimeSurfaceProfileContext:
        runtime_scope = service._build_runtime_scope_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            child_run_id=child_run_id,
            scheduler_run_id=scheduler_run_id,
        )
        recovery_target_run_id = cls.resolve_recovery_target_run_id(
            parent_run_id=parent_run_id,
            runtime_scope=runtime_scope,
        )
        return RuntimeSurfaceProfileContext(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            query_id=query_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            child_run_id=child_run_id,
            scheduler_run_id=scheduler_run_id,
            runtime_scope=runtime_scope,
            recovery_target_run_id=recovery_target_run_id,
        )

    @staticmethod
    def resolve_recovery_target_run_id(
        *,
        parent_run_id: str | None = None,
        runtime_scope: Dict[str, Any] | None = None,
    ) -> str:
        scope = runtime_scope or {}
        return (
            str(parent_run_id or "").strip()
            or str(scope.get("scheduler_run_id") or "").strip()
            or str(scope.get("run_id") or "").strip()
        )
