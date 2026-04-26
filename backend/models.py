from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum as SQLEnum, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

try:
    from database import Base
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.database import Base


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


class PermissionRequestRecord(Base):
    """工具权限请求持久化记录。"""

    __tablename__ = "permission_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(String(50), unique=True, index=True, nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_args = Column(JSON)
    permission_level = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    result = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)

    def __repr__(self):
        return f"<PermissionRequestRecord {self.request_id}: {self.tool_name} ({self.status})>"


class ArtifactRecord(Base):
    """运行时 artifact 持久化记录。"""

    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    artifact_id = Column(String(64), unique=True, index=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    kind = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    render_mode = Column(String(50))
    card_schema = Column(String(100))
    card = Column(JSON)
    artifact_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<ArtifactRecord {self.artifact_id}: {self.kind}>"


class MessageFeedbackRecord(Base):
    """用户对助手输出的反馈记录。"""

    __tablename__ = "message_feedback"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "message_id",
            "user_id",
            name="uq_message_feedback_conv_msg_user",
        ),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    feedback_type = Column(String(20), nullable=False)
    score = Column(Integer, nullable=True)
    comment = Column(Text)
    runtime_artifact_id = Column(String(64), nullable=True)
    runtime_scope = Column(String(50), nullable=True)
    selected_items = Column(JSON)
    stop_reason = Column(String(50), nullable=True)
    created_learning_id = Column(String(50), nullable=True)
    feedback_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<MessageFeedbackRecord {self.id}: {self.feedback_type}>"


class PlanStatus(str, enum.Enum):
    """计划项状态。"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class PlanHandoffStatus(str, enum.Enum):
    """计划项分派/交接状态。"""

    UNASSIGNED = "unassigned"
    READY = "ready"
    HANDED_OFF = "handed_off"
    EXECUTING = "executing"
    MERGED = "merged"


class PlanRunRecord(Base):
    """Planner 计划运行记录。"""

    __tablename__ = "plan_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True, index=True)
    objective = Column(Text, nullable=False)
    source = Column(String(50), default="manual", nullable=False)
    status = Column(SQLEnum(PlanStatus), default=PlanStatus.PENDING, nullable=False)
    active_item_id = Column(Integer, nullable=True)
    summary = Column(Text)
    plan_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    items = relationship(
        "PlanItemRecord",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanItemRecord.step_order.asc()",
    )

    def __repr__(self):
        return f"<PlanRunRecord {self.id}: {self.objective[:40]}>"


class PlanItemRecord(Base):
    """Planner 计划步骤记录。"""

    __tablename__ = "plan_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("plan_runs.id"), nullable=False, index=True)
    step_order = Column(Integer, default=1, nullable=False)
    title = Column(String(255), nullable=False)
    details = Column(Text)
    status = Column(SQLEnum(PlanStatus), default=PlanStatus.PENDING, nullable=False)
    owner = Column(String(100))
    agent_role = Column(String(100))
    agent_id = Column(String(100))
    handoff_status = Column(SQLEnum(PlanHandoffStatus), default=PlanHandoffStatus.UNASSIGNED, nullable=False)
    item_metadata = Column("metadata", JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    plan = relationship("PlanRunRecord", back_populates="items")

    def __repr__(self):
        return f"<PlanItemRecord {self.id}: {self.title}>"
