from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List

try:
    from agent_server.dependencies import get_current_user, get_db
    from agent_server.http import ensure_exists, success_response
    from models import User
    from schemas import (
        ConversationCreate,
        ConversationFeedbackAnalyticsResponse,
        ConversationFeedbackCreate,
        ConversationFeedbackResponse,
        ConversationResponse,
        ConversationWithMessages,
    )
    from services.conversation_service import ConversationService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_current_user, get_db
    from backend.agent_server.http import ensure_exists, success_response
    from backend.models import User
    from backend.schemas import (
        ConversationCreate,
        ConversationFeedbackAnalyticsResponse,
        ConversationFeedbackCreate,
        ConversationFeedbackResponse,
        ConversationResponse,
        ConversationWithMessages,
    )
    from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["会话"])


@router.get("", response_model=List[ConversationResponse])
def get_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取用户所有会话"""
    return ConversationService(db).list_user_conversations(current_user.id)


@router.get("/search", response_model=List[ConversationResponse])
def search_conversations(
    q: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """搜索会话（按标题和消息内容）"""
    return ConversationService(db).search_conversations(user_id=current_user.id, query=q)


@router.get("/search/messages")
def search_messages(
    q: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """搜索消息（返回匹配的消息及其所属会话）"""
    return ConversationService(db).search_messages(user_id=current_user.id, query=q)


@router.post("", response_model=ConversationResponse)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """创建新会话"""
    return ConversationService(db).create_conversation(
        user_id=current_user.id,
        title=conversation_data.title,
        model_name=conversation_data.model_name,
    )


@router.get("/analytics/feedback", response_model=ConversationFeedbackAnalyticsResponse)
def get_feedback_analytics(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    days: int = 30,
    min_samples_for_candidate: int = 2,
):
    """按 scope / prompt / practice 聚合反馈表现，支持回滚候选识别。"""
    service = ConversationService(db)
    return service.get_feedback_analytics(
        user_id=current_user.id,
        days=days,
        min_samples_for_candidate=min_samples_for_candidate,
    )


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
def get_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取会话详情（含消息）"""
    conversation = ConversationService(db).get_owned_conversation(conversation_id, current_user.id)
    return ensure_exists(conversation, "会话不存在")


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """删除会话"""
    conversation = ConversationService(db).get_owned_conversation(conversation_id, current_user.id)
    ensure_exists(conversation, "会话不存在")

    ConversationService(db).delete_conversation(conversation)

    return success_response("删除成功")


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    title: str = None,
    model_name: str = None,
):
    """更新会话"""
    conversation = ConversationService(db).get_owned_conversation(conversation_id, current_user.id)
    ensure_exists(conversation, "会话不存在")

    return ConversationService(db).update_conversation(
        conversation=conversation,
        title=title,
        model_name=model_name,
    )


@router.post("/{conversation_id}/feedback", response_model=ConversationFeedbackResponse)
def create_conversation_feedback(
    conversation_id: int,
    feedback: ConversationFeedbackCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """记录用户对助手回复的反馈，并关联本次 runtime effect。"""
    service = ConversationService(db)
    conversation = service.get_owned_conversation(conversation_id, current_user.id)
    ensure_exists(conversation, "会话不存在")

    try:
        return service.create_feedback(
            conversation=conversation,
            user_id=current_user.id,
            feedback_type=feedback.feedback_type,
            score=feedback.score,
            comment=feedback.comment,
            message_id=feedback.message_id,
            selected_reasons=feedback.selected_reasons,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{conversation_id}/feedback", response_model=List[ConversationFeedbackResponse])
def get_conversation_feedback(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """获取会话反馈列表，便于评估 runtime knowledge 效果。"""
    service = ConversationService(db)
    conversation = service.get_owned_conversation(conversation_id, current_user.id)
    ensure_exists(conversation, "会话不存在")

    return service.list_feedback(conversation_id=conversation.id)
