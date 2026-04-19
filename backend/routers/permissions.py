"""
权限管理 API
处理 Tool 调用权限的确认和拒绝
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from harness import get_permission_service

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
    status: str
    created_at: str


@router.get("/pending")
async def list_pending_permissions():
    """获取所有待处理的权限请求"""
    service = get_permission_service()
    pending = service.list_pending_requests()

    return {
        "requests": [
            {
                "id": p.id,
                "tool_name": p.tool_name,
                "tool_args": p.tool_args,
                "status": p.status.value,
                "created_at": p.created_at.isoformat()
            }
            for p in pending
        ]
    }


@router.get("/{request_id}")
async def get_permission(request_id: str):
    """获取特定权限请求的状态"""
    service = get_permission_service()
    request = service.get_request(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="请求不存在")

    return {
        "id": request.id,
        "tool_name": request.tool_name,
        "tool_args": request.tool_args,
        "status": request.status.value,
        "created_at": request.created_at.isoformat(),
        "result": request.result
    }


@router.post("/approve")
async def approve_permission(req: PermissionApproveRequest):
    """批准权限请求"""
    service = get_permission_service()

    success = service.approve(req.request_id, req.result)

    if not success:
        raise HTTPException(status_code=404, detail="请求不存在")

    return {"success": True, "message": "权限已批准"}


@router.post("/deny")
async def deny_permission(req: PermissionDenyRequest):
    """拒绝权限请求"""
    service = get_permission_service()

    success = service.deny(req.request_id)

    if not success:
        raise HTTPException(status_code=404, detail="请求不存在")

    return {"success": True, "message": "权限已拒绝"}


@router.get("/result/{request_id}")
async def get_result(request_id: str):
    """获取权限请求的执行结果（轮询）"""
    service = get_permission_service()
    result = service.get_result(request_id)

    if result is None:
        raise HTTPException(status_code=404, detail="结果不存在")

    return {"request_id": request_id, "result": result}
