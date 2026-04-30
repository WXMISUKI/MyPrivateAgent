import re
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

try:
    from services.startup_diagnostics_service import get_startup_diagnostics_service
    from services.runtime_surface_service import get_runtime_surface_service
    from services.capability_gap_service import get_capability_gap_service
    from services.remediation_status_service import get_remediation_status_service
    from database import get_db
    from schemas_runtime_surface import RuntimeSurfaceUpdateRequest
    from config import CORS_ALLOWED_ORIGINS, CORS_ALLOWED_ORIGIN_REGEX
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service
    from backend.services.runtime_surface_service import get_runtime_surface_service
    from backend.services.capability_gap_service import get_capability_gap_service
    from backend.services.remediation_status_service import get_remediation_status_service
    from backend.database import get_db
    from backend.schemas_runtime_surface import RuntimeSurfaceUpdateRequest
    from backend.config import CORS_ALLOWED_ORIGINS, CORS_ALLOWED_ORIGIN_REGEX


router = APIRouter(prefix="/api", tags=["系统"])


def _parse_iso_datetime(value: str | None) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        normalized = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


@router.get("/health/live")
def liveness():
    """Lightweight liveness probe — confirms the process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe — checks database connectivity."""
    checks = {"database": "ok"}
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        checks["database"] = f"error: {e}"
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "checks": checks}


@router.get("/health")
def health_check():
    """轻量健康检查与启动诊断摘要。"""
    return get_startup_diagnostics_service().collect_report()


@router.get("/health/cors")
def cors_diagnostics(request: Request):
    """Return effective CORS settings and match result for current request Origin."""
    origin = str(request.headers.get("origin") or "").strip()
    allowed_origins = [str(item).strip().rstrip("/") for item in CORS_ALLOWED_ORIGINS if str(item).strip()]
    origin_regex = str(CORS_ALLOWED_ORIGIN_REGEX or "").strip() or None

    exact_match = origin.rstrip("/") in allowed_origins if origin else False
    regex_match = False
    regex_error = None
    if origin and origin_regex:
        try:
            regex_match = re.fullmatch(origin_regex, origin) is not None
        except re.error as exc:
            regex_error = str(exc)

    return {
        "request_origin": origin or None,
        "allow_credentials": True,
        "configured_allow_origins": allowed_origins,
        "configured_allow_origin_regex": origin_regex,
        "matched_by_exact_origin": exact_match,
        "matched_by_regex": regex_match,
        "is_allowed": bool(exact_match or regex_match),
        "regex_error": regex_error,
        "preflight_headers": {
            "access-control-request-method": request.headers.get("access-control-request-method"),
            "access-control-request-headers": request.headers.get("access-control-request-headers"),
        },
    }


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
    hook_event_type: str | None = None,
    subagent_role: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    window_days: int | None = None,
    db: Session = Depends(get_db),
):
    """返回近期能力缺口汇总，用于框架能力盘点。"""
    summary = get_capability_gap_service(db).get_summary(
        limit=limit,
        missing_part=missing_part,
        keyword=keyword,
        profile=profile,
        completion_stage=completion_stage,
        error_category=error_category,
        hook_event_type=hook_event_type,
        subagent_role=subagent_role,
        provider=provider,
        model_name=model_name,
        window_days=window_days,
    )
    status_map = get_remediation_status_service(db).status_map()
    remediation_status_counts: dict[str, int] = {
        "open": 0,
        "in_progress": 0,
        "blocked": 0,
        "done": 0,
        "verified": 0,
    }
    for target in summary.get("remediation_targets") or []:
        action_id = str(target.get("action_id") or "").strip()
        if not action_id:
            continue
        target["status"] = (status_map.get(action_id) or {}).get("status", "open")
        target["status_detail"] = status_map.get(action_id)
        status_key = str(target.get("status") or "open").strip()
        remediation_status_counts[status_key] = int(remediation_status_counts.get(status_key, 0)) + 1
    summary["remediation_status_counts"] = remediation_status_counts
    summary["non_closed_action_count"] = (
        int(remediation_status_counts.get("open", 0))
        + int(remediation_status_counts.get("in_progress", 0))
        + int(remediation_status_counts.get("blocked", 0))
    )
    progress_window_days = 14
    if window_days in {7, 14, 30}:
        progress_window_days = int(window_days)
    now_utc = datetime.now(timezone.utc)
    recent_threshold = now_utc - timedelta(days=progress_window_days)
    stale_threshold = now_utc - timedelta(days=30)
    recent_progress: list[dict] = []
    long_blocked: list[dict] = []
    pending_start: list[dict] = []
    for target in summary.get("remediation_targets") or []:
        action_id = str(target.get("action_id") or "").strip()
        status = str(target.get("status") or "open").strip()
        status_detail = target.get("status_detail") or {}
        updated_at = _parse_iso_datetime(status_detail.get("updated_at"))
        item = {
            "action_id": action_id,
            "status": status,
            "owner": str(target.get("owner") or "").strip(),
            "module": str(target.get("module") or "").strip(),
            "playbook_title": str(target.get("playbook_title") or "").strip(),
            "updated_at": status_detail.get("updated_at"),
        }
        if updated_at and updated_at >= recent_threshold:
            recent_progress.append(item)
        if status == "blocked":
            if updated_at is None or updated_at < stale_threshold:
                long_blocked.append(item)
        if status == "open":
            pending_start.append(item)
    summary["remediation_progress"] = {
        "window_days": progress_window_days,
        "recent_progress": recent_progress,
        "long_blocked": long_blocked,
        "pending_start": pending_start,
        "recent_progress_count": len(recent_progress),
        "long_blocked_count": len(long_blocked),
        "pending_start_count": len(pending_start),
    }
    return summary


@router.get("/remediation-status")
def get_remediation_statuses(db: Session = Depends(get_db)):
    """返回整改状态清单。"""
    return {"items": get_remediation_status_service(db).list_statuses()}


@router.patch("/remediation-status/{action_id}")
def update_remediation_status(
    action_id: str,
    payload: dict,
    db: Session = Depends(get_db),
):
    """更新单个整改动作状态。"""
    try:
        updated = get_remediation_status_service(db).upsert_status(
            action_id=action_id,
            status=str(payload.get("status") or ""),
            owner=payload.get("owner"),
            module=payload.get("module"),
            note=payload.get("note"),
            updated_by=payload.get("updated_by"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return updated
