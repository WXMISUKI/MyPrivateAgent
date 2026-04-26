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


class ConversationFeedbackCreate(BaseModel):
    feedback_type: str = Field(..., pattern="^(positive|negative|neutral)$")
    message_id: Optional[int] = None
    score: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)
    selected_reasons: Optional[List[str]] = None


class ConversationFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    message_id: Optional[int] = None
    user_id: Optional[int] = None
    feedback_type: str
    score: Optional[int] = None
    comment: Optional[str] = None
    runtime_artifact_id: Optional[str] = None
    runtime_scope: Optional[str] = None
    selected_items: Optional[List[dict]] = None
    stop_reason: Optional[str] = None
    created_learning_id: Optional[str] = None
    feedback_metadata: Optional[dict] = None
    created_at: datetime


class FeedbackDimensionStat(BaseModel):
    key: str
    total: int
    negative: int
    negative_rate: float


class FeedbackRollbackCandidate(BaseModel):
    kind: str
    key: str
    total: int
    negative: int
    negative_rate: float


class ConversationFeedbackAnalyticsResponse(BaseModel):
    window_days: int
    generated_at: datetime
    total_feedback: int
    positive_count: int
    negative_count: int
    neutral_count: int
    negative_rate: float
    scope_stats: List[FeedbackDimensionStat]
    prompt_stats: List[FeedbackDimensionStat]
    practice_stats: List[FeedbackDimensionStat]
    rollback_candidates: List[FeedbackRollbackCandidate]


# ============ 聊天相关 ============
class ChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    conversation_id: Optional[int] = None
    message: str
    model_name: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: int


# ============ 模型相关 ============
class ModelInfo(BaseModel):
    name: str
    display_name: str


# ============ Planner / Todo 相关 ============
class PlanItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    details: Optional[str] = Field(default=None, max_length=4000)
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|blocked|cancelled)$")
    owner: Optional[str] = Field(default=None, max_length=100)
    agent_role: Optional[str] = Field(default=None, max_length=100)
    agent_id: Optional[str] = Field(default=None, max_length=100)
    handoff_status: str = Field(default="unassigned", pattern="^(unassigned|ready|handed_off|executing|merged)$")
    required_capabilities: List[str] = []
    step_order: Optional[int] = Field(default=None, ge=1)


class PlanItemCreate(PlanItemBase):
    pass


class PlanItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    details: Optional[str] = Field(default=None, max_length=4000)
    status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|completed|blocked|cancelled)$")
    owner: Optional[str] = Field(default=None, max_length=100)
    agent_role: Optional[str] = Field(default=None, max_length=100)
    agent_id: Optional[str] = Field(default=None, max_length=100)
    handoff_status: Optional[str] = Field(default=None, pattern="^(unassigned|ready|handed_off|executing|merged)$")
    required_capabilities: Optional[List[str]] = None
    step_order: Optional[int] = Field(default=None, ge=1)


class PlanItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    step_order: int
    title: str
    details: Optional[str] = None
    status: str
    owner: Optional[str] = None
    agent_role: Optional[str] = None
    agent_id: Optional[str] = None
    handoff_status: str
    required_capabilities: List[str] = []
    child_executions: List[dict] = []
    merge_summary: Optional[dict] = None
    audit_trail: List[dict] = []
    run_trace: List[dict] = []
    created_at: datetime
    updated_at: datetime


class PlanCreate(BaseModel):
    objective: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
    source: str = Field(default="manual", max_length=50)
    items: List[PlanItemCreate] = []


class PlanGenerateRequest(BaseModel):
    objective: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[int] = None
    source: str = Field(default="generated", max_length=50)


class PlanUpdate(BaseModel):
    objective: Optional[str] = Field(default=None, min_length=1, max_length=4000)
    summary: Optional[str] = Field(default=None, max_length=4000)
    status: Optional[str] = Field(default=None, pattern="^(pending|in_progress|completed|blocked|cancelled)$")


class PlanProgressSummary(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int
    blocked: int
    cancelled: int


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    conversation_id: Optional[int] = None
    objective: str
    source: str
    status: str
    active_item_id: Optional[int] = None
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[PlanItemResponse] = []
    progress: PlanProgressSummary


# ============ MCP Registry 相关 ============
class McpServerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    transport: str = Field(default="stdio", pattern="^(stdio|http)$")
    command: Optional[str] = Field(default=None, max_length=500)
    args: List[str] = []
    url: Optional[str] = Field(default=None, max_length=1000)
    enabled: bool = True
    description: Optional[str] = Field(default=None, max_length=2000)
    capabilities: List[str] = []
    tags: List[str] = []
    metadata: Optional[dict] = None


class McpServerCreate(McpServerBase):
    pass


class McpServerUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    transport: Optional[str] = Field(default=None, pattern="^(stdio|http)$")
    command: Optional[str] = Field(default=None, max_length=500)
    args: Optional[List[str]] = None
    url: Optional[str] = Field(default=None, max_length=1000)
    enabled: Optional[bool] = None
    description: Optional[str] = Field(default=None, max_length=2000)
    capabilities: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class McpServerResponse(BaseModel):
    name: str
    display_name: str
    transport: str
    command: Optional[str] = None
    args: List[str] = []
    url: Optional[str] = None
    enabled: bool
    description: Optional[str] = None
    capabilities: List[str] = []
    tags: List[str] = []
    metadata: dict = {}
    status: str


class McpCapabilityCatalogEntry(BaseModel):
    capability: str
    server_names: List[str]


class McpCapabilityCatalogResponse(BaseModel):
    total_servers: int
    enabled_servers: int
    capabilities: List[McpCapabilityCatalogEntry]


class McpProbeResponse(BaseModel):
    server_name: str
    transport: str
    status: str
    detail: str
    command: Optional[str] = None
    resolved_command: Optional[str] = None
    args: List[str] = []
    url: Optional[str] = None


class McpSessionAuditEntry(BaseModel):
    server_name: str
    transport: str
    phase: str
    request_method: str
    ok: bool
    detail: str = ""
    response_excerpt: str = ""


class McpSessionHandshakeResponse(BaseModel):
    server_name: str
    transport: str
    status: str
    protocol_version: str
    server_info: dict = {}
    capabilities: dict = {}
    tools: List[dict] = []
    audit: List[McpSessionAuditEntry] = []


class McpToolCallRequest(BaseModel):
    arguments: dict = {}


class McpToolCallResponse(BaseModel):
    server_name: str
    tool_name: str
    status: str
    structured_content: dict = {}
    content: List[str] = []
    is_error: bool = False
    raw_result: dict = {}
    audit: McpSessionAuditEntry
