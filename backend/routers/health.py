from fastapi import APIRouter

try:
    from services.startup_diagnostics_service import get_startup_diagnostics_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.startup_diagnostics_service import get_startup_diagnostics_service


router = APIRouter(prefix="/api", tags=["系统"])


@router.get("/health")
def health_check():
    """轻量健康检查与启动诊断摘要。"""
    return get_startup_diagnostics_service().collect_report()
