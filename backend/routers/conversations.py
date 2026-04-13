from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List
from datetime import datetime

from database import get_db
from models import User, Conversation, Message
from schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    MessageResponse
)
from auth import get_current_user
from routers.chat import clear_graph_cache

router = APIRouter(prefix="/api/conversations", tags=["会话"])


@router.get("", response_model=List[ConversationResponse])
def get_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取用户所有会话"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    return conversations


@router.post("", response_model=ConversationResponse)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """创建新会话"""
    conversation = Conversation(
        user_id=current_user.id,
        title=conversation_data.title,
        model_name=conversation_data.model_name
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
def get_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """获取会话详情（含消息）"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    return conversation


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
):
    """删除会话"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    db.delete(conversation)
    db.commit()

    return {"message": "删除成功"}


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    title: str = None,
    model_name: str = None,
):
    """更新会话"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    # 记录旧模型名称
    old_model_name = conversation.model_name

    if title is not None:
        conversation.title = title
    if model_name is not None:
        conversation.model_name = model_name
        # 清除旧模型的缓存
        if old_model_name != model_name:
            clear_graph_cache(old_model_name)

    db.commit()
    db.refresh(conversation)

    return conversation
