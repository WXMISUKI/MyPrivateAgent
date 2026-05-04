"""
权限管理 API
处理 Tool 调用权限的确认和拒绝
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

try:
    from agent_server.dependencies import get_db
    from agent_server.http import ensure_exists, permission_request_to_dict, success_response
    from harness import get_permission_service
    from services.run_trace_service import get_run_trace_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_db
    from backend.agent_server.http import ensure_exists, permission_request_to_dict, success_response
    from backend.harness import get_permission_service
    from backend.services.run_trace_service import get_run_trace_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/permissions", tags=["permissions"])


class PermissionApproveRequest(BaseModel):
    request_id: str
    result: Optional[str] = None


class PermissionDenyRequest(BaseModel):
    request_id: str


class PermissionResponse(BaseModel):
    id: str
    tool_name: str
    tool_args: dict
    permission_level: str
    conversation_id: Optional[int] = None
    status: str
    created_at: str


@router.get("/pending")
async def list_pending_permissions():
    """获取所有待处理的权限请求"""
    service = get_permission_service()
    pending = service.list_pending_requests()

    return {
        "requests": [permission_request_to_dict(p) for p in pending]
    }


@router.get("/{request_id}")
async def get_permission(request_id: str):
    """获取特定权限请求的状态"""
    service = get_permission_service()
    request = service.get_request(request_id)
    return permission_request_to_dict(ensure_exists(request, "请求不存在"), include_result=True)

@router.post("/approve")
async def approve_permission(req: PermissionApproveRequest, db: Session = Depends(get_db)):
    """批准权限请求"""
    service = get_permission_service()
    request = service.get_request(req.request_id)

    success = service.approve(req.request_id, req.result)

    if not success:
        raise HTTPException(status_code=404, detail="请求不存在")

    if request is not None:
        trace_service = get_run_trace_service(db)
        snapshot_ref = trace_service.build_snapshot_ref(
            source="permission",
            event_type="permission_approved",
            conversation_id=getattr(request, "conversation_id", None),
        )
        payload = {
            "request_id": request.id,
            "tool_name": request.tool_name,
            "tool_args": dict(request.tool_args or {}),
            "result": req.result,
            "snapshot_ref": snapshot_ref,
        }
        trace_service.append_latest_active_item_trace(
            user_id=getattr(request, "user_id", None),
            conversation_id=getattr(request, "conversation_id", None),
            source="permission",
            event_type="permission_approved",
            summary=f"工具 `{request.tool_name}` 权限请求已批准",
            detail=str(req.result or "").strip(),
            severity="success",
            payload=payload,
        )
        trace_service.append_latest_active_item_audit(
            user_id=getattr(request, "user_id", None),
            conversation_id=getattr(request, "conversation_id", None),
            event_type="permission_approved",
            content=f"工具 `{request.tool_name}` 权限请求已批准",
            payload=payload,
        )

    return success_response("权限已批准")


@router.post("/deny")
async def deny_permission(req: PermissionDenyRequest, db: Session = Depends(get_db)):
    """拒绝权限请求"""
    service = get_permission_service()
    request = service.get_request(req.request_id)

    success = service.deny(req.request_id)

    if not success:
        raise HTTPException(status_code=404, detail="请求不存在")

    if request is not None:
        trace_service = get_run_trace_service(db)
        snapshot_ref = trace_service.build_snapshot_ref(
            source="permission",
            event_type="permission_denied",
            conversation_id=getattr(request, "conversation_id", None),
        )
        payload = {
            "request_id": request.id,
            "tool_name": request.tool_name,
            "tool_args": dict(request.tool_args or {}),
            "snapshot_ref": snapshot_ref,
        }
        trace_service.append_latest_active_item_trace(
            user_id=getattr(request, "user_id", None),
            conversation_id=getattr(request, "conversation_id", None),
            source="permission",
            event_type="permission_denied",
            summary=f"工具 `{request.tool_name}` 权限请求已拒绝",
            detail="用户拒绝了本次工具执行。",
            severity="warning",
            payload=payload,
        )
        trace_service.append_latest_active_item_audit(
            user_id=getattr(request, "user_id", None),
            conversation_id=getattr(request, "conversation_id", None),
            event_type="permission_denied",
            content=f"工具 `{request.tool_name}` 权限请求已拒绝",
            payload=payload,
        )

    return success_response("权限已拒绝")


@router.get("/result/{request_id}")
async def get_result(request_id: str):
    """获取权限请求的执行结果（轮询）"""
    service = get_permission_service()
    result = service.get_result(request_id)

    if result is None:
        raise HTTPException(status_code=404, detail="结果不存在")

    return {"request_id": request_id, "result": result}
