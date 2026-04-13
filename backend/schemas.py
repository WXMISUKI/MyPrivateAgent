from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============ 认证相关 ============
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ============ 对话相关 ============
class ConversationCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    title: Optional[str] = "新对话"
    model_name: Optional[str] = "llama3.1"


class ConversationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    user_id: int
    title: str
    model_name: str
    created_at: datetime
    updated_at: datetime


class ConversationWithMessages(ConversationResponse):
    messages: List["MessageResponse"] = []


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


# ============ 聊天相关 ============
class ChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    conversation_id: int
    message: str
    model_name: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: int


# ============ 模型相关 ============
class ModelInfo(BaseModel):
    name: str
    display_name: str