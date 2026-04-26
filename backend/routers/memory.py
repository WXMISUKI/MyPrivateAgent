"""
内存管理 API
提供会话状态和内存使用情况的监控接口
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

try:
    from harness import get_memory_manager, get_context_manager
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.harness import get_memory_manager, get_context_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])


class MemoryStatsResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    idle_sessions: int
    abandoned_sessions: int
    total_tokens: int
    total_messages: int
    memory_usage_mb: float
    active_conversation_id: Optional[int]


class SessionInfoResponse(BaseModel):
    conversation_id: int
    state: str
    message_count: int
    total_tokens: int
    last_active: str
    idle_seconds: float


@router.get("/memory/stats")
async def get_memory_stats():
    """获取内存使用统计"""
    memory_mgr = get_memory_manager()
    context_mgr = get_context_manager()

    stats = memory_mgr.get_stats()

    # 添加上下文统计
    stats["context_count"] = len(context_mgr.contexts)

    return stats


@router.get("/memory/sessions")
async def list_active_sessions() -> List[Dict[str, Any]]:
    """列出所有活跃会话"""
    memory_mgr = get_memory_manager()
    return memory_mgr.get_active_sessions()


@router.delete("/memory/session/{conversation_id}")
async def delete_session(conversation_id: int):
    """删除指定会话"""
    memory_mgr = get_memory_manager()
    context_mgr = get_context_manager()

    # 删除内存会话
    memory_mgr.delete_session(conversation_id)

    # 删除上下文
    context_mgr.delete_context(conversation_id)

    return {"success": True, "message": f"会话 {conversation_id} 已删除"}


@router.post("/memory/cleanup")
async def trigger_cleanup():
    """手动触发清理"""
    memory_mgr = get_memory_manager()

    # 清理空闲会话
    idle_count = memory_mgr._cleanup_idle_sessions()

    # 清理过期的上下文
    context_mgr = get_context_manager()
    # （未来可以在这里添加上下文清理逻辑）

    return {
        "success": True,
        "cleaned_sessions": idle_count,
        "message": f"已清理 {idle_count} 个空闲会话"
    }


@router.post("/memory/clear-all")
async def clear_all_sessions():
    """清空所有会话（危险操作）"""
    memory_mgr = get_memory_manager()
    context_mgr = get_context_manager()

    # 清空调话
    memory_mgr.clear_all_sessions()

    # 清空所有上下文
    for conv_id in list(context_mgr.contexts.keys()):
        context_mgr.delete_context(conv_id)

    return {"success": True, "message": "已清空所有会话和上下文"}


@router.get("/memory/session/{conversation_id}")
async def get_session_info(conversation_id: int):
    """获取指定会话的详细信息"""
    memory_mgr = get_memory_manager()
    context_mgr = get_context_manager()

    session = memory_mgr.get_session(conversation_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    context_stats = context_mgr.get_stats(conversation_id)

    return {
        "conversation_id": session.conversation_id,
        "state": session.state.value,
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat(),
        "message_count": session.message_count,
        "total_tokens": session.total_tokens,
        "user_id": session.user_id,
        "model_name": session.model_name,
        "context_stats": context_stats
    }
