from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联关系
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """对话会话模型"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="新对话")
    model_name = Column(String(50), default="llama3.1")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关联关系
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """消息模型"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # 关联关系
    conversation = relationship("Conversation", back_populates="messages")


class Skill(Base):
    """Skill模型 - 存储用户导入的Skills"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)  # 描述
    source_path = Column(String(500))  # 原始文件路径
    storage_path = Column(String(500), nullable=False)  # 存储路径
    is_enabled = Column(Integer, default=0)  # 是否启用 (0=禁用, 1=启用)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ============ 自我改进相关模型 ============

class LearningCategory(str, enum.Enum):
    """学习记录分类"""
    CORRECTION = "correction"
    INSIGHT = "insight"
    KNOWLEDGE_GAP = "knowledge_gap"
    BEST_PRACTICE = "best_practice"


class Priority(str, enum.Enum):
    """优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LearningStatus(str, enum.Enum):
    """学习记录状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    PROMOTED = "promoted"
    PROMOTED_TO_SKILL = "promoted_to_skill"


class Area(str, enum.Enum):
    """区域标签"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    INFRA = "infra"
    TESTS = "tests"
    DOCS = "docs"
    CONFIG = "config"


class Learning(Base):
    """学习记录模型"""
    __tablename__ = "learnings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    learning_id = Column(String(50), unique=True, index=True, nullable=False)  # 格式: LRN-YYYYMMDD-XXX
    category = Column(SQLEnum(LearningCategory), nullable=False)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    status = Column(SQLEnum(LearningStatus), default=LearningStatus.PENDING)
    area = Column(SQLEnum(Area))
    summary = Column(Text, nullable=False)
    details = Column(Text)
    suggested_action = Column(Text)
    source = Column(String(50))  # conversation, error, user_feedback
    related_files = Column(JSON)  # 存储相关文件列表
    tags = Column(JSON)  # 存储标签
    pattern_key = Column(String(100), index=True)  # 用于检测重复模式
    recurrence_count = Column(Integer, default=1)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime)
    promoted_to = Column(String(200))  # 提升到的文件: CLAUDE.md, AGENTS.md, etc.
    see_also = Column(JSON)  # 关联的其他学习记录

    def __repr__(self):
        return f"<Learning {self.learning_id}: {self.summary}>"


class Error(Base):
    """错误记录模型"""
    __tablename__ = "errors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    error_id = Column(String(50), unique=True, index=True, nullable=False)  # 格式: ERR-YYYYMMDD-XXX
    priority = Column(SQLEnum(Priority), default=Priority.HIGH)
    status = Column(String(20), default="pending")  # pending, in_progress, resolved, wont_fix
    area = Column(SQLEnum(Area))
    summary = Column(Text, nullable=False)
    error_message = Column(Text)
    context = Column(Text)
    suggested_fix = Column(Text)
    reproducible = Column(Boolean, default=False)
    related_files = Column(JSON)
    see_also = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime)

    def __repr__(self):
        return f"<Error {self.error_id}: {self.summary}>"


class FeatureRequest(Base):
    """功能请求模型"""
    __tablename__ = "feature_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_id = Column(String(50), unique=True, index=True, nullable=False)  # 格式: FEAT-YYYYMMDD-XXX
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    status = Column(String(20), default="pending")  # pending, in_progress, resolved, wont_fix
    area = Column(SQLEnum(Area))
    requested_capability = Column(Text, nullable=False)
    user_context = Column(Text)
    complexity_estimate = Column(String(20))  # simple, medium, complex
    suggested_implementation = Column(Text)
    frequency = Column(String(20), default="first_time")  # first_time, recurring
    related_features = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime)

    def __repr__(self):
        return f"<FeatureRequest {self.feature_id}: {self.requested_capability}>"


class SystemPrompt(Base):
    """系统提示模型"""
    __tablename__ = "system_prompts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prompt_key = Column(String(100), unique=True, index=True, nullable=False)
    prompt_type = Column(String(50), nullable=False)  # behavior, workflow, tool_usage, etc.
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    area = Column(SQLEnum(Area))
    tags = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SystemPrompt {self.prompt_key}: {self.prompt_type}>"


class BestPractice(Base):
    """最佳实践模型"""
    __tablename__ = "best_practices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    practice_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(50))
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    code_example = Column(Text)
    trade_offs = Column(JSON)
    source_learning_id = Column(String(50))  # 来源学习记录ID
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<BestPractice {self.practice_id}: {self.title}>"
