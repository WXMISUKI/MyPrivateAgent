"""
学习记录管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json
import random
import string

from pydantic import BaseModel
try:
    from agent_server.dependencies import get_db
    from models import (
        Learning, LearningCategory, LearningStatus, Priority, Area,
        Error, FeatureRequest, SystemPrompt, BestPractice
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_db
    from backend.models import (
        Learning, LearningCategory, LearningStatus, Priority, Area,
        Error, FeatureRequest, SystemPrompt, BestPractice
    )

router = APIRouter(prefix="/api/learnings", tags=["learnings"])


class LearningCreate(BaseModel):
    category: str
    priority: str = "medium"
    area: Optional[str] = None
    summary: str
    details: Optional[str] = None
    suggested_action: Optional[str] = None
    source: Optional[str] = "conversation"
    related_files: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    pattern_key: Optional[str] = None


class LearningUpdate(BaseModel):
    status: Optional[str] = None
    summary: Optional[str] = None
    details: Optional[str] = None
    suggested_action: Optional[str] = None
    promoted_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class LearningResponse(BaseModel):
    id: int
    learning_id: str
    category: str
    priority: str
    status: str
    area: Optional[str]
    summary: str
    details: Optional[str]
    suggested_action: Optional[str]
    source: Optional[str]
    related_files: Optional[List[str]]
    tags: Optional[List[str]]
    pattern_key: Optional[str]
    recurrence_count: int
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    promoted_to: Optional[str]
    see_also: Optional[List[str]]


class ErrorCreate(BaseModel):
    priority: str = "high"
    area: Optional[str] = None
    summary: str
    error_message: Optional[str] = None
    context: Optional[str] = None
    suggested_fix: Optional[str] = None
    reproducible: bool = False
    related_files: Optional[List[str]] = None


class ErrorUpdate(BaseModel):
    status: Optional[str] = None
    summary: Optional[str] = None
    suggested_fix: Optional[str] = None
    resolution_notes: Optional[str] = None


class ErrorResponse(BaseModel):
    id: int
    error_id: str
    priority: str
    status: str
    area: Optional[str]
    summary: str
    error_message: Optional[str]
    context: Optional[str]
    suggested_fix: Optional[str]
    reproducible: bool
    related_files: Optional[List[str]]
    see_also: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]


class FeatureRequestCreate(BaseModel):
    priority: str = "medium"
    area: Optional[str] = None
    requested_capability: str
    user_context: Optional[str] = None
    complexity_estimate: str = "medium"
    suggested_implementation: Optional[str] = None
    frequency: str = "first_time"
    related_features: Optional[List[str]] = None


class FeatureRequestUpdate(BaseModel):
    status: Optional[str] = None
    suggested_implementation: Optional[str] = None
    resolution_notes: Optional[str] = None


class FeatureRequestResponse(BaseModel):
    id: int
    feature_id: str
    priority: str
    status: str
    area: Optional[str]
    requested_capability: str
    user_context: Optional[str]
    complexity_estimate: str
    suggested_implementation: Optional[str]
    frequency: str
    related_features: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]


class SystemPromptCreate(BaseModel):
    prompt_key: str
    prompt_type: str
    content: str
    priority: int = 1
    area: Optional[str] = None
    tags: Optional[List[str]] = None


class SystemPromptResponse(BaseModel):
    id: int
    prompt_key: str
    prompt_type: str
    content: str
    priority: int
    is_active: bool
    area: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


class BestPracticeCreate(BaseModel):
    practice_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = "medium"
    code_example: Optional[str] = None
    trade_offs: Optional[dict] = None
    source_learning_id: Optional[str] = None


class BestPracticeResponse(BaseModel):
    id: int
    practice_id: str
    title: str
    description: Optional[str]
    category: Optional[str]
    priority: str
    code_example: Optional[str]
    trade_offs: Optional[dict]
    source_learning_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class StatsResponse(BaseModel):
    total_learnings: int
    pending_learnings: int
    resolved_learnings: int
    total_errors: int
    pending_errors: int
    total_features: int
    pending_features: int
    total_prompts: int
    active_prompts: int
    total_practices: int


def generate_id(prefix: str) -> str:
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{prefix}-{date_str}-{random_str}"


def model_to_dict(model):
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}


@router.post("", response_model=LearningResponse)
async def create_learning(learning: LearningCreate, db: Session = Depends(get_db)):
    try:
        learning_id = generate_id("LRN")
        existing = db.query(Learning).filter(Learning.learning_id == learning_id).first()
        if existing:
            learning_id = generate_id("LRN")
        db_learning = Learning(
            learning_id=learning_id,
            category=LearningCategory[learning.category.upper()],
            priority=Priority[learning.priority.upper()],
            status=LearningStatus.PENDING,
            area=Area[learning.area.upper()] if learning.area else None,
            summary=learning.summary,
            details=learning.details,
            suggested_action=learning.suggested_action,
            source=learning.source,
            related_files=learning.related_files,
            tags=learning.tags,
            pattern_key=learning.pattern_key,
            first_seen=datetime.now(),
            last_seen=datetime.now()
        )
        db.add(db_learning)
        db.commit()
        db.refresh(db_learning)
        return LearningResponse(**model_to_dict(db_learning))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[LearningResponse])
async def get_learnings(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    area: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Learning)
    if status:
        query = query.filter(Learning.status == status)
    if area:
        query = query.filter(Learning.area == area)
    if category:
        query = query.filter(Learning.category == category)
    learnings = query.offset(skip).limit(limit).all()
    return [LearningResponse(**model_to_dict(learning)) for learning in learnings]


@router.get("/stats", response_model=StatsResponse)
async def get_learning_stats(db: Session = Depends(get_db)):
    total_learnings = db.query(Learning).count()
    pending_learnings = db.query(Learning).filter(Learning.status == LearningStatus.PENDING).count()
    resolved_learnings = db.query(Learning).filter(Learning.status == LearningStatus.RESOLVED).count()
    total_errors = db.query(Error).count()
    pending_errors = db.query(Error).filter(Error.status == "pending").count()
    total_features = db.query(FeatureRequest).count()
    pending_features = db.query(FeatureRequest).filter(FeatureRequest.status == "pending").count()
    total_prompts = db.query(SystemPrompt).count()
    active_prompts = db.query(SystemPrompt).filter(SystemPrompt.is_active == True).count()
    total_practices = db.query(BestPractice).count()
    return StatsResponse(
        total_learnings=total_learnings,
        pending_learnings=pending_learnings,
        resolved_learnings=resolved_learnings,
        total_errors=total_errors,
        pending_errors=pending_errors,
        total_features=total_features,
        pending_features=pending_features,
        total_prompts=total_prompts,
        active_prompts=active_prompts,
        total_practices=total_practices
    )


@router.post("/errors", response_model=ErrorResponse)
async def create_error(error: ErrorCreate, db: Session = Depends(get_db)):
    try:
        error_id = generate_id("ERR")
        db_error = Error(
            error_id=error_id,
            priority=Priority[error.priority.upper()],
            status="pending",
            area=Area[error.area.upper()] if error.area else None,
            summary=error.summary,
            error_message=error.error_message,
            context=error.context,
            suggested_fix=error.suggested_fix,
            reproducible=error.reproducible,
            related_files=error.related_files
        )
        db.add(db_error)
        db.commit()
        db.refresh(db_error)
        return ErrorResponse(**model_to_dict(db_error))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/errors", response_model=List[ErrorResponse])
async def get_errors(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Error)
    if status:
        query = query.filter(Error.status == status)
    if area:
        query = query.filter(Error.area == area)
    errors = query.offset(skip).limit(limit).all()
    return [ErrorResponse(**model_to_dict(error)) for error in errors]


@router.post("/features", response_model=FeatureRequestResponse)
async def create_feature_request(
    feature: FeatureRequestCreate,
    db: Session = Depends(get_db)
):
    try:
        feature_id = generate_id("FEAT")
        db_feature = FeatureRequest(
            feature_id=feature_id,
            priority=Priority[feature.priority.upper()],
            status="pending",
            area=Area[feature.area.upper()] if feature.area else None,
            requested_capability=feature.requested_capability,
            user_context=feature.user_context,
            complexity_estimate=feature.complexity_estimate,
            suggested_implementation=feature.suggested_implementation,
            frequency=feature.frequency,
            related_features=feature.related_features
        )
        db.add(db_feature)
        db.commit()
        db.refresh(db_feature)
        return FeatureRequestResponse(**model_to_dict(db_feature))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/features", response_model=List[FeatureRequestResponse])
async def get_feature_requests(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(FeatureRequest)
    if status:
        query = query.filter(FeatureRequest.status == status)
    if area:
        query = query.filter(FeatureRequest.area == area)
    features = query.offset(skip).limit(limit).all()
    return [FeatureRequestResponse(**model_to_dict(feature)) for feature in features]


@router.post("/prompts", response_model=SystemPromptResponse)
async def create_system_prompt(
    prompt: SystemPromptCreate,
    db: Session = Depends(get_db)
):
    try:
        db_prompt = SystemPrompt(
            prompt_key=prompt.prompt_key,
            prompt_type=prompt.prompt_type,
            content=prompt.content,
            priority=prompt.priority,
            area=Area[prompt.area.upper()] if prompt.area else None,
            tags=prompt.tags
        )
        db.add(db_prompt)
        db.commit()
        db.refresh(db_prompt)
        return SystemPromptResponse(**model_to_dict(db_prompt))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prompts", response_model=List[SystemPromptResponse])
async def get_system_prompts(
    skip: int = 0,
    limit: int = 100,
    prompt_type: Optional[str] = None,
    area: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SystemPrompt)
    if prompt_type:
        query = query.filter(SystemPrompt.prompt_type == prompt_type)
    if area:
        query = query.filter(SystemPrompt.area == area)
    if is_active is not None:
        query = query.filter(SystemPrompt.is_active == is_active)
    query = query.order_by(SystemPrompt.priority.desc())
    prompts = query.offset(skip).limit(limit).all()
    return [SystemPromptResponse(**model_to_dict(prompt)) for prompt in prompts]


@router.get("/prompts/active", response_model=List[SystemPromptResponse])
async def get_active_prompts(
    prompt_type: Optional[str] = None,
    area: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(SystemPrompt).filter(SystemPrompt.is_active == True)
    if prompt_type:
        query = query.filter(SystemPrompt.prompt_type == prompt_type)
    if area:
        query = query.filter(SystemPrompt.area == area)
    query = query.order_by(SystemPrompt.priority.desc())
    prompts = query.limit(20).all()
    return [SystemPromptResponse(**model_to_dict(prompt)) for prompt in prompts]


@router.post("/practices", response_model=BestPracticeResponse)
async def create_best_practice(
    practice: BestPracticeCreate,
    db: Session = Depends(get_db)
):
    try:
        db_practice = BestPractice(
            practice_id=practice.practice_id,
            title=practice.title,
            description=practice.description,
            category=practice.category,
            priority=Priority[practice.priority.upper()],
            code_example=practice.code_example,
            trade_offs=practice.trade_offs,
            source_learning_id=practice.source_learning_id
        )
        db.add(db_practice)
        db.commit()
        db.refresh(db_practice)
        return BestPracticeResponse(**model_to_dict(db_practice))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/practices", response_model=List[BestPracticeResponse])
async def get_best_practices(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BestPractice)
    if category:
        query = query.filter(BestPractice.category == category)
    practices = query.offset(skip).limit(limit).all()
    return [BestPracticeResponse(**model_to_dict(practice)) for practice in practices]


@router.post("/review/daily")
async def run_daily_review(db: Session = Depends(get_db)):
    try:
        from auto_reviewer import get_auto_reviewer
        reviewer = get_auto_reviewer()
        result = await reviewer.run_daily_review(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/promote")
async def run_auto_promotion(
    min_recurrence: int = 3,
    db: Session = Depends(get_db)
):
    try:
        from auto_reviewer import get_auto_reviewer
        reviewer = get_auto_reviewer()
        result = await reviewer.run_auto_promotion(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/trends")
async def get_learning_trends(
    days: int = 7,
    db: Session = Depends(get_db)
):
    try:
        from auto_reviewer import get_auto_reviewer
        reviewer = get_auto_reviewer()
        result = reviewer.daily_reviewer.get_learning_trends(db, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/errors")
async def get_error_patterns(db: Session = Depends(get_db)):
    try:
        from auto_reviewer import get_auto_reviewer
        reviewer = get_auto_reviewer()
        result = reviewer.daily_reviewer.get_error_patterns(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/optimization")
async def get_optimization_suggestions(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    try:
        from auto_reviewer import get_auto_reviewer
        reviewer = get_auto_reviewer()
        result = await reviewer.optimization_suggester.generate_optimization_suggestions(db, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/priorities")
async def get_improvement_priorities(db: Session = Depends(get_db)):
    try:
        from auto_reviewer import get_auto_reviewer
        reviewer = get_auto_reviewer()
        result = await reviewer.optimization_suggester.suggest_improvement_priorities(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{learning_id}", response_model=LearningResponse)
async def get_learning(learning_id: str, db: Session = Depends(get_db)):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    return LearningResponse(**model_to_dict(learning))


@router.put("/{learning_id}/resolve")
async def resolve_learning(
    learning_id: str,
    notes: Optional[str] = None,
    commit: Optional[str] = None,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    learning.status = LearningStatus.RESOLVED
    learning.resolved_at = datetime.now()
    if commit:
        learning.promoted_to = commit
        learning.status = LearningStatus.PROMOTED
    db.commit()
    db.refresh(learning)
    return {"message": "Learning resolved", "learning": model_to_dict(learning)}


@router.put("/{learning_id}", response_model=LearningResponse)
async def update_learning(
    learning_id: str,
    update: LearningUpdate,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    if update.status:
        learning.status = LearningStatus[update.status.upper()]
    if update.summary:
        learning.summary = update.summary
    if update.details:
        learning.details = update.details
    if update.suggested_action:
        learning.suggested_action = update.suggested_action
    if update.promoted_to:
        learning.promoted_to = update.promoted_to
        learning.status = LearningStatus.PROMOTED
    learning.updated_at = datetime.now()
    db.commit()
    db.refresh(learning)
    return LearningResponse(**model_to_dict(learning))


@router.put("/errors/{error_id}", response_model=ErrorResponse)
async def update_error(
    error_id: str,
    update: ErrorUpdate,
    db: Session = Depends(get_db)
):
    error = db.query(Error).filter(Error.error_id == error_id).first()
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    if update.status:
        error.status = update.status
        if update.status == "resolved":
            error.resolved_at = datetime.now()
    if update.summary:
        error.summary = update.summary
    if update.suggested_fix:
        error.suggested_fix = update.suggested_fix
    error.updated_at = datetime.now()
    db.commit()
    db.refresh(error)
    return ErrorResponse(**model_to_dict(error))


@router.put("/{feature_id}", response_model=FeatureRequestResponse)
async def update_feature_request(
    feature_id: str,
    update: FeatureRequestUpdate,
    db: Session = Depends(get_db)
):
    feature = db.query(FeatureRequest).filter(
        FeatureRequest.feature_id == feature_id
    ).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature request not found")
    if update.status:
        feature.status = update.status
        if update.status == "resolved":
            feature.resolved_at = datetime.now()
    if update.suggested_implementation:
        feature.suggested_implementation = update.suggested_implementation
    feature.updated_at = datetime.now()
    db.commit()
    db.refresh(feature)
    return FeatureRequestResponse(**model_to_dict(feature))


@router.put("/prompts/{prompt_key}", response_model=SystemPromptResponse)
async def update_system_prompt(
    prompt_key: str,
    is_active: Optional[bool] = None,
    content: Optional[str] = None,
    db: Session = Depends(get_db)
):
    prompt = db.query(SystemPrompt).filter(
        SystemPrompt.prompt_key == prompt_key
    ).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="System prompt not found")
    if is_active is not None:
        prompt.is_active = is_active
    if content:
        prompt.content = content
    prompt.updated_at = datetime.now()
    db.commit()
    db.refresh(prompt)
    return SystemPromptResponse(**model_to_dict(prompt))
