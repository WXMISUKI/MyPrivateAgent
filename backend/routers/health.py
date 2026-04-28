from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from services.startup_diagnostics_service import get_startup_diagnostics_service
    from services.runtime_surface_service import get_runtime_surface_service
    from services.capability_gap_service import get_capability_gap_service
    from database import get_db
    from schemas_runtime_surface import RuntimeSurfaceUpdateRequest
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service
    from backend.services.runtime_surface_service import get_runtime_surface_service
    from backend.services.capability_gap_service import get_capability_gap_service
    from backend.database import get_db
    from backend.schemas_runtime_surface import RuntimeSurfaceUpdateRequest


router = APIRouter(prefix="/api", tags=["系统"])


@router.get("/health")
def health_check():
    """轻量健康检查与启动诊断摘要。"""
    return get_startup_diagnostics_service().collect_report()


@router.get("/runtime-profile")
def get_runtime_profile():
    """返回当前 demo/runtime 的可配置表面。"""
    return get_runtime_surface_service().get_runtime_profile()


@router.patch("/runtime-profile")
def update_runtime_profile(request: RuntimeSurfaceUpdateRequest):
    """更新当前 demo/runtime 的最小可配置表面。"""
    try:
        return get_runtime_surface_service().update_runtime_profile(request.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/capability-gaps")
def get_capability_gaps(
    limit: int = 100,
    missing_part: str | None = None,
    keyword: str | None = None,
    profile: str | None = None,
    completion_stage: str | None = None,
    error_category: str | None = None,
    db: Session = Depends(get_db),
):
    """返回近期能力缺口汇总，用于框架能力盘点。"""
    return get_capability_gap_service(db).get_summary(
        limit=limit,
        missing_part=missing_part,
        keyword=keyword,
        profile=profile,
        completion_stage=completion_stage,
        error_category=error_category,
    )
