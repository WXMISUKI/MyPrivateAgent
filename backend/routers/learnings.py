"""
学习记录管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime
import json
import random
import string

from pydantic import BaseModel, Field
try:
    from agent_server.dependencies import get_db
    from models import (
        Learning, LearningCategory, LearningStatus, LearningReviewRecord, LearningReviewStatus, LearningVersionRecord, Priority, Area,
        Error, FeatureRequest, SystemPrompt, BestPractice
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_db
    from backend.models import (
        Learning, LearningCategory, LearningStatus, LearningReviewRecord, LearningReviewStatus, LearningVersionRecord, Priority, Area,
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


class LearningGovernanceActionRequest(BaseModel):
    note: Optional[str] = None
    promote_to: Optional[str] = None
    target_type: Optional[str] = None
    conversation_id: Optional[int] = None


class LearningDuplicateMergeRequest(BaseModel):
    source_learning_id: str
    note: Optional[str] = None
    conversation_id: Optional[int] = None


class LearningVersionApplyRequest(BaseModel):
    version_id: str
    note: Optional[str] = None
    fields: Optional[List[str]] = None
    conversation_id: Optional[int] = None


class LearningReviewCreate(BaseModel):
    review_status: str
    quality_score: Optional[int] = None
    reviewer: Optional[str] = None
    review_note: Optional[str] = None
    conversation_id: Optional[int] = None


class LearningReviewResponse(BaseModel):
    review_id: str
    learning_id: str
    review_status: str
    quality_score: Optional[int] = None
    reviewer: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    snapshot_ref: Optional[dict] = None
    timeline_recording: Optional[dict] = None


class LearningReviewSummaryResponse(BaseModel):
    review_id: str
    review_status: str
    quality_score: Optional[int] = None
    reviewer: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime


class LearningVersionResponse(BaseModel):
    version_id: str
    learning_id: str
    event_type: str
    actor: Optional[str] = None
    status: str
    summary: str
    details: Optional[str] = None
    tags: Optional[List[str]] = None
    promoted_to: Optional[str] = None
    change_note: Optional[str] = None
    version_metadata: Optional[dict] = None
    snapshot_ref: Optional[dict] = None
    created_at: datetime


class LearningVersionCompareFieldResponse(BaseModel):
    field: str
    before: Optional[str] = None
    after: Optional[str] = None


class LearningVersionCompareResponse(BaseModel):
    learning_id: str
    base_label: str
    target_label: str
    changed_fields: List[LearningVersionCompareFieldResponse] = Field(default_factory=list)
    has_changes: bool = False


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
    latest_review: Optional[LearningReviewSummaryResponse] = None
    history_count: int = 0
    conflict_flags: List[str] = Field(default_factory=list)
    conflict_context: dict = Field(default_factory=dict)
    snapshot_ref: Optional[dict] = None
    timeline_recording: Optional[dict] = None


class LearningVersionApplyResponse(BaseModel):
    learning: LearningResponse
    applied_version_id: str
    note: Optional[str] = None
    applied_fields: List[str] = Field(default_factory=list)
    snapshot_ref: Optional[dict] = None
    timeline_recording: Optional[dict] = None


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
    disabled_learnings: int
    rolled_back_learnings: int
    reviewed_learnings: int
    average_quality_score: Optional[float] = None
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


def _review_model_to_summary(review) -> Optional[dict]:
    if not review:
        return None
    return {
        "review_id": review.review_id,
        "review_status": review.review_status.value if hasattr(review.review_status, "value") else str(review.review_status),
        "quality_score": review.quality_score,
        "reviewer": review.reviewer,
        "review_note": review.review_note,
        "created_at": review.created_at,
    }


def _version_model_to_dict(version) -> Optional[dict]:
    if not version:
        return None
    snapshot_ref = None
    metadata = dict(version.version_metadata or {})
    generated_at = None
    if getattr(version, "created_at", None) is not None:
        try:
            generated_at = version.created_at.isoformat()
        except Exception:
            generated_at = None
    try:
        snapshot_ref = _get_run_trace_service(None).build_snapshot_ref(
            source="learning",
            event_type=version.event_type,
            conversation_id=metadata.get("conversation_id"),
            generated_at=generated_at,
        )
    except Exception:
        snapshot_ref = None
    return {
        "version_id": version.version_id,
        "learning_id": version.learning_id,
        "event_type": version.event_type,
        "actor": version.actor,
        "status": version.status,
        "summary": version.summary,
        "details": version.details,
        "tags": version.tags,
        "promoted_to": version.promoted_to,
        "change_note": version.change_note,
        "version_metadata": version.version_metadata,
        "snapshot_ref": snapshot_ref,
        "created_at": version.created_at,
    }


def _normalize_snapshot_payload(payload: Optional[dict]) -> dict:
    payload = payload or {}
    return {
        "status": str(payload.get("status") or "").strip(),
        "summary": str(payload.get("summary") or "").strip(),
        "details": payload.get("details"),
        "suggested_action": payload.get("suggested_action"),
        "tags": list(payload.get("tags") or []),
        "promoted_to": payload.get("promoted_to"),
        "source": payload.get("source"),
        "pattern_key": payload.get("pattern_key"),
        "category": payload.get("category"),
        "priority": payload.get("priority"),
        "area": payload.get("area"),
        "review_status": payload.get("review_status"),
        "quality_score": payload.get("quality_score"),
    }


def _learning_snapshot_from_model(learning) -> dict:
    return _normalize_snapshot_payload({
        "status": getattr(learning.status, "value", str(getattr(learning, "status", ""))),
        "summary": learning.summary,
        "details": learning.details,
        "suggested_action": learning.suggested_action,
        "tags": _normalize_tags(getattr(learning, "tags", None)),
        "promoted_to": learning.promoted_to,
        "source": learning.source,
        "pattern_key": learning.pattern_key,
        "category": getattr(getattr(learning, "category", None), "value", str(getattr(learning, "category", ""))),
        "priority": getattr(getattr(learning, "priority", None), "value", str(getattr(learning, "priority", ""))),
        "area": getattr(getattr(learning, "area", None), "value", str(getattr(learning, "area", ""))) if getattr(learning, "area", None) else None,
    })


def _learning_snapshot_from_version(version) -> dict:
    payload = dict(version.version_metadata or {})
    payload.update({
        "status": version.status,
        "summary": version.summary,
        "details": version.details,
        "tags": version.tags or [],
        "promoted_to": version.promoted_to,
    })
    return _normalize_snapshot_payload(payload)


def _build_learning_with_latest_review(
    learning,
    latest_review=None,
    *,
    history_count: int = 0,
    conflict_flags: Optional[List[str]] = None,
    conflict_context: Optional[dict] = None,
    snapshot_ref: Optional[dict] = None,
    timeline_recording: Optional[dict] = None,
) -> dict:
    data = model_to_dict(learning)
    data["latest_review"] = _review_model_to_summary(latest_review)
    data["history_count"] = int(history_count or 0)
    data["conflict_flags"] = list(conflict_flags or [])
    data["conflict_context"] = dict(conflict_context or {})
    data["snapshot_ref"] = snapshot_ref
    data["timeline_recording"] = timeline_recording
    return data


def _get_latest_reviews_for_learnings(db: Session, learning_ids: List[str]) -> dict:
    if not learning_ids:
        return {}
    review_rows = db.query(LearningReviewRecord).filter(
        LearningReviewRecord.learning_id.in_(learning_ids)
    ).order_by(
        LearningReviewRecord.learning_id.asc(),
        LearningReviewRecord.created_at.desc(),
        LearningReviewRecord.id.desc(),
    ).all()
    latest: dict[str, Any] = {}
    for review in review_rows:
        latest.setdefault(review.learning_id, review)
    return latest


def _get_history_counts_for_learnings(db: Session, learning_ids: List[str]) -> dict:
    if not learning_ids:
        return {}
    rows = db.query(
        LearningVersionRecord.learning_id,
        func.count(LearningVersionRecord.id),
    ).filter(
        LearningVersionRecord.learning_id.in_(learning_ids)
    ).group_by(
        LearningVersionRecord.learning_id
    ).all()
    return {learning_id: count for learning_id, count in rows}


def _get_duplicate_pattern_keys(db: Session, pattern_keys: List[str]) -> set[str]:
    normalized = [str(item or "").strip() for item in pattern_keys if str(item or "").strip()]
    if not normalized:
        return set()
    rows = db.query(
        Learning.pattern_key,
        func.count(Learning.id),
    ).filter(
        Learning.pattern_key.in_(normalized)
    ).filter(
        Learning.status != LearningStatus.DISABLED
    ).group_by(
        Learning.pattern_key
    ).having(
        func.count(Learning.id) > 1
    ).all()
    return {str(pattern_key) for pattern_key, _ in rows if pattern_key}


def _get_duplicate_learning_ids(db: Session, learning) -> List[str]:
    pattern_key = str(getattr(learning, "pattern_key", "") or "").strip()
    if not pattern_key:
        return []
    rows = db.query(Learning.learning_id).filter(
        Learning.pattern_key == pattern_key,
        Learning.learning_id != learning.learning_id,
        Learning.status != LearningStatus.DISABLED,
    ).order_by(Learning.created_at.desc(), Learning.id.desc()).all()
    return [learning_id for (learning_id,) in rows]


def _build_conflict_flags(
    learning,
    latest_review=None,
    *,
    duplicate_pattern_keys: Optional[set[str]] = None,
    duplicate_learning_ids: Optional[List[str]] = None,
) -> List[str]:
    flags: List[str] = []
    latest_review_status = str(
        getattr(getattr(latest_review, "review_status", None), "value", getattr(latest_review, "review_status", ""))
    ).strip().lower()
    if latest_review_status == LearningReviewStatus.NEEDS_CHANGES.value:
        flags.append("review_needs_changes")
    elif latest_review_status == LearningReviewStatus.REJECTED.value:
        flags.append("review_rejected")

    pattern_key = str(getattr(learning, "pattern_key", "") or "").strip()
    if pattern_key and pattern_key in (duplicate_pattern_keys or set()):
        flags.append("duplicate_pattern_key")
    if duplicate_learning_ids:
        flags.append("duplicate_learning_group")

    learning_status = getattr(learning, "status", None)
    if learning_status in {LearningStatus.PROMOTED, LearningStatus.PROMOTED_TO_SKILL}:
        if latest_review_status != LearningReviewStatus.APPROVED.value:
            flags.append("promotion_without_approved_review")

    return flags


def _record_learning_version(
    db: Session,
    learning,
    *,
    event_type: str,
    actor: Optional[str] = None,
    change_note: Optional[str] = None,
    version_metadata: Optional[dict] = None,
):
    snapshot_metadata = {
        "suggested_action": getattr(learning, "suggested_action", None),
        "source": getattr(learning, "source", None),
        "pattern_key": getattr(learning, "pattern_key", None),
        "category": getattr(getattr(learning, "category", None), "value", str(getattr(learning, "category", ""))),
        "priority": getattr(getattr(learning, "priority", None), "value", str(getattr(learning, "priority", ""))),
        "area": getattr(getattr(learning, "area", None), "value", str(getattr(learning, "area", ""))) if getattr(learning, "area", None) else None,
    }
    snapshot_metadata.update(version_metadata or {})
    snapshot = LearningVersionRecord(
        version_id=generate_id("LVH"),
        learning_id=learning.learning_id,
        event_type=str(event_type or "").strip() or "update",
        actor=(actor or "").strip() or None,
        status=getattr(getattr(learning, "status", None), "value", str(getattr(learning, "status", ""))),
        summary=learning.summary,
        details=learning.details,
        tags=_normalize_tags(getattr(learning, "tags", None)),
        promoted_to=getattr(learning, "promoted_to", None),
        change_note=(change_note or "").strip() or None,
        version_metadata=snapshot_metadata,
    )
    db.add(snapshot)
    return snapshot


def _build_conflict_context(
    learning,
    latest_review=None,
    *,
    duplicate_learning_ids: Optional[List[str]] = None,
) -> dict:
    return {
        "duplicate_learning_ids": list(duplicate_learning_ids or []),
        "latest_review_status": _review_model_to_summary(latest_review).get("review_status") if latest_review else None,
        "latest_review_quality_score": _review_model_to_summary(latest_review).get("quality_score") if latest_review else None,
        "pattern_key": getattr(learning, "pattern_key", None),
    }


def _format_snapshot_value(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _compare_snapshots(base_snapshot: dict, target_snapshot: dict) -> List[dict]:
    fields = [
        "status",
        "summary",
        "details",
        "suggested_action",
        "tags",
        "promoted_to",
        "source",
        "pattern_key",
        "category",
        "priority",
        "area",
        "review_status",
        "quality_score",
    ]
    changed_fields = []
    for field in fields:
        before = _format_snapshot_value(base_snapshot.get(field))
        after = _format_snapshot_value(target_snapshot.get(field))
        if before != after:
            changed_fields.append({
                "field": field,
                "before": before,
                "after": after,
            })
    return changed_fields


def _normalize_version_fields(fields: Optional[List[str]] = None) -> List[str]:
    allowed = {
        "status",
        "summary",
        "details",
        "suggested_action",
        "tags",
        "promoted_to",
        "source",
        "pattern_key",
        "category",
        "priority",
        "area",
    }
    if fields is None:
        return sorted(allowed)
    normalized = []
    seen = set()
    for field in fields:
        key = str(field or "").strip()
        if key and key in allowed and key not in seen:
            normalized.append(key)
            seen.add(key)
    return normalized


def _apply_snapshot_to_learning(learning, snapshot: dict, fields: Optional[List[str]] = None):
    selected_fields = set(_normalize_version_fields(fields))

    status = str(snapshot.get("status") or "").strip()
    if "status" in selected_fields and status:
        try:
            learning.status = LearningStatus[status.upper()]
        except KeyError:
            pass

    category = str(snapshot.get("category") or "").strip()
    if "category" in selected_fields and category:
        try:
            learning.category = LearningCategory[category.upper()]
        except KeyError:
            pass

    priority = str(snapshot.get("priority") or "").strip()
    if "priority" in selected_fields and priority:
        try:
            learning.priority = Priority[priority.upper()]
        except KeyError:
            pass

    area = snapshot.get("area")
    if "area" in selected_fields:
        if area:
            try:
                learning.area = Area[str(area).upper()]
            except KeyError:
                pass
        elif area is None:
            learning.area = None

    if "summary" in selected_fields:
        learning.summary = snapshot.get("summary") or learning.summary
    if "details" in selected_fields:
        learning.details = snapshot.get("details")
    if "suggested_action" in selected_fields:
        learning.suggested_action = snapshot.get("suggested_action")
    if "tags" in selected_fields:
        learning.tags = _normalize_tags(snapshot.get("tags"))
    if "promoted_to" in selected_fields:
        learning.promoted_to = snapshot.get("promoted_to")
    if "source" in selected_fields:
        learning.source = snapshot.get("source")
    if "pattern_key" in selected_fields:
        learning.pattern_key = snapshot.get("pattern_key")
    learning.updated_at = datetime.now()
    return sorted(selected_fields)


def _record_learning_timeline(
    *,
    db: Session,
    conversation_id: Optional[int],
    learning_id: str,
    event_type: str,
    summary: str,
    detail: str = "",
    severity: str = "info",
    payload: Optional[dict] = None,
) -> dict:
    trace_service = _get_run_trace_service(db)
    snapshot_ref = trace_service.build_snapshot_ref(
        source="learning",
        event_type=event_type,
        conversation_id=conversation_id,
    )
    final_payload = {
        **(payload or {}),
        "learning_id": learning_id,
        "conversation_id": conversation_id,
        "snapshot_ref": snapshot_ref,
    }
    trace_written = trace_service.append_latest_active_item_trace(
        user_id=None,
        conversation_id=conversation_id,
        source="learning",
        event_type=event_type,
        summary=summary,
        detail=detail,
        severity=severity,
        payload=final_payload,
    ) if conversation_id is not None else False
    audit_written = trace_service.append_latest_active_item_audit(
        user_id=None,
        conversation_id=conversation_id,
        event_type=event_type,
        content=summary,
        payload=final_payload,
    ) if conversation_id is not None else False
    return {
        "trace_written": trace_written,
        "audit_written": audit_written,
        "conversation_id": conversation_id,
        "snapshot_ref": snapshot_ref,
    }


def _build_learning_response(
    db: Session,
    learning,
    *,
    snapshot_ref: Optional[dict] = None,
    timeline_recording: Optional[dict] = None,
) -> LearningResponse:
    latest_review = db.query(LearningReviewRecord).filter(
        LearningReviewRecord.learning_id == learning.learning_id
    ).order_by(
        LearningReviewRecord.created_at.desc(),
        LearningReviewRecord.id.desc()
    ).first()
    history_count = db.query(LearningVersionRecord).filter(
        LearningVersionRecord.learning_id == learning.learning_id
    ).count()
    duplicate_pattern_keys = _get_duplicate_pattern_keys(db, [getattr(learning, "pattern_key", None)])
    duplicate_learning_ids = _get_duplicate_learning_ids(db, learning)
    return LearningResponse(
        **_build_learning_with_latest_review(
            learning,
            latest_review,
            history_count=history_count,
            conflict_flags=_build_conflict_flags(
                learning,
                latest_review,
                duplicate_pattern_keys=duplicate_pattern_keys,
                duplicate_learning_ids=duplicate_learning_ids,
            ),
            conflict_context=_build_conflict_context(
                learning,
                latest_review,
                duplicate_learning_ids=duplicate_learning_ids,
            ),
            snapshot_ref=snapshot_ref,
            timeline_recording=timeline_recording,
        )
    )


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
        db.flush()
        _record_learning_version(
            db,
            db_learning,
            event_type="created",
            change_note="创建学习记录",
            version_metadata={"source": db_learning.source, "pattern_key": db_learning.pattern_key},
        )
        db.commit()
        db.refresh(db_learning)
        return _build_learning_response(db, db_learning)
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
    latest_reviews = _get_latest_reviews_for_learnings(db, [learning.learning_id for learning in learnings])
    history_counts = _get_history_counts_for_learnings(db, [learning.learning_id for learning in learnings])
    duplicate_pattern_keys = _get_duplicate_pattern_keys(db, [learning.pattern_key for learning in learnings if learning.pattern_key])
    duplicate_learning_map = {
        learning.learning_id: _get_duplicate_learning_ids(db, learning)
        for learning in learnings
    }
    return [
        LearningResponse(**_build_learning_with_latest_review(
            learning,
            latest_reviews.get(learning.learning_id),
            history_count=history_counts.get(learning.learning_id, 0),
            conflict_flags=_build_conflict_flags(
                learning,
                latest_reviews.get(learning.learning_id),
                duplicate_pattern_keys=duplicate_pattern_keys,
                duplicate_learning_ids=duplicate_learning_map.get(learning.learning_id, []),
            ),
            conflict_context=_build_conflict_context(
                learning,
                latest_reviews.get(learning.learning_id),
                duplicate_learning_ids=duplicate_learning_map.get(learning.learning_id, []),
            ),
        ))
        for learning in learnings
    ]


@router.get("/stats", response_model=StatsResponse)
async def get_learning_stats(db: Session = Depends(get_db)):
    total_learnings = db.query(Learning).count()
    pending_learnings = db.query(Learning).filter(Learning.status == LearningStatus.PENDING).count()
    resolved_learnings = db.query(Learning).filter(Learning.status == LearningStatus.RESOLVED).count()
    disabled_learnings = db.query(Learning).filter(Learning.status == LearningStatus.DISABLED).count()
    rolled_back_learnings = db.query(Learning).filter(Learning.status == LearningStatus.ROLLED_BACK).count()
    reviewed_reviews = db.query(LearningReviewRecord).all()
    latest_reviews: dict[str, Any] = {}
    for review in sorted(reviewed_reviews, key=lambda item: (str(item.learning_id), item.created_at or datetime.min, item.id or 0), reverse=True):
        latest_reviews.setdefault(review.learning_id, review)
    reviewed_learnings = len(latest_reviews)
    average_quality_score = None
    if latest_reviews:
        scores = [review.quality_score for review in latest_reviews.values() if review.quality_score is not None]
        if scores:
            average_quality_score = round(sum(scores) / len(scores), 2)
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
        disabled_learnings=disabled_learnings,
        rolled_back_learnings=rolled_back_learnings,
        reviewed_learnings=reviewed_learnings,
        average_quality_score=average_quality_score,
        total_errors=total_errors,
        pending_errors=pending_errors,
        total_features=total_features,
        pending_features=pending_features,
        total_prompts=total_prompts,
        active_prompts=active_prompts,
        total_practices=total_practices
    )


def _normalize_tags(tags: Optional[List[str]]) -> List[str]:
    return [str(item).strip() for item in (tags or []) if str(item).strip()]


def _get_knowledge_transformer():
    try:
        from knowledge_transformer import get_knowledge_transformer
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.knowledge_transformer import get_knowledge_transformer
    return get_knowledge_transformer()


def _get_run_trace_service(db):
    try:
        from services.run_trace_service import get_run_trace_service
    except ModuleNotFoundError:  # pragma: no cover - package import compatibility
        from backend.services.run_trace_service import get_run_trace_service
    return get_run_trace_service(db)


def _remove_prefixed_tags(tags: List[str], prefix: str) -> List[str]:
    normalized_prefix = str(prefix or "").strip().lower()
    if not normalized_prefix:
        return list(tags)
    return [tag for tag in tags if not tag.lower().startswith(normalized_prefix)]


def _set_prev_status_tag(tags: List[str], status: Optional[str]) -> List[str]:
    base_tags = _remove_prefixed_tags(tags, "prev_status:")
    normalized_status = str(status or "").strip()
    if normalized_status:
        base_tags.append(f"prev_status:{normalized_status}")
    return base_tags


def _extract_prev_status(tags: List[str]) -> Optional[str]:
    for tag in tags:
        if str(tag).lower().startswith("prev_status:"):
            return str(tag).split(":", 1)[1].strip() or None
    return None


def _set_learning_tags(learning, *, add: Optional[List[str]] = None, remove: Optional[List[str]] = None):
    current = _normalize_tags(getattr(learning, "tags", None))
    removals = [str(item).strip().lower() for item in (remove or []) if str(item).strip()]
    next_tags = []
    for tag in current:
        lowered = tag.lower()
        should_remove = False
        for removal in removals:
            if removal.endswith(":"):
                if lowered.startswith(removal):
                    should_remove = True
                    break
            elif lowered == removal:
                should_remove = True
                break
        if not should_remove:
            next_tags.append(tag)
    existing_lower = {tag.lower() for tag in next_tags}
    for tag in add or []:
        normalized = str(tag).strip()
        if normalized and normalized.lower() not in existing_lower:
            next_tags.append(normalized)
            existing_lower.add(normalized.lower())
    learning.tags = next_tags


def _append_governance_note(learning, action: str, note: Optional[str] = None):
    note_text = str(note or "").strip()
    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = f"[governance] {timestamp} action={action}"
    if note_text:
        entry = f"{entry} note={note_text}"
    details = str(getattr(learning, "details", "") or "").strip()
    learning.details = f"{details}\n{entry}".strip() if details else entry


def _apply_learning_governance_action(learning, *, action: str, note: Optional[str] = None, promote_to: Optional[str] = None):
    current_status = getattr(learning, "status", None)
    if action == "disable":
        current_tags = _normalize_tags(getattr(learning, "tags", None))
        current_tag_values = _set_prev_status_tag(current_tags, getattr(current_status, "value", None))
        learning.tags = current_tag_values
        learning.status = LearningStatus.DISABLED
        _set_learning_tags(learning, add=["disabled"], remove=["rollback"])
    elif action == "rollback":
        current_tags = _normalize_tags(getattr(learning, "tags", None))
        current_tag_values = _set_prev_status_tag(current_tags, getattr(current_status, "value", None))
        learning.tags = current_tag_values
        learning.status = LearningStatus.ROLLED_BACK
        _set_learning_tags(learning, add=["rollback"], remove=["disabled"])
    elif action == "restore":
        current_tags = _normalize_tags(getattr(learning, "tags", None))
        previous_status = _extract_prev_status(current_tags)
        if previous_status:
            try:
                learning.status = LearningStatus[previous_status.upper()]
            except KeyError:
                learning.status = LearningStatus.PENDING
        else:
            if current_status in {LearningStatus.DISABLED, LearningStatus.ROLLED_BACK}:
                learning.status = LearningStatus.PENDING
        _set_learning_tags(learning, remove=["disabled", "rollback", "prev_status:"])
    elif action == "promote":
        current_tags = _normalize_tags(getattr(learning, "tags", None))
        current_tag_values = _set_prev_status_tag(current_tags, getattr(current_status, "value", None))
        learning.tags = current_tag_values
        learning.status = LearningStatus.PROMOTED
        learning.promoted_to = promote_to or getattr(learning, "promoted_to", None) or "CLAUDE.md"
        _set_learning_tags(learning, remove=["disabled", "rollback"])
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported governance action: {action}")

    _append_governance_note(learning, action, note)
    learning.updated_at = datetime.now()
    return learning


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
    return _build_learning_response(db, learning)


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
    _record_learning_version(
        db,
        learning,
        event_type="updated",
        change_note="更新学习记录",
        version_metadata={
            "updated_fields": [
                field for field, value in {
                    "status": update.status,
                    "summary": update.summary,
                    "details": update.details,
                    "suggested_action": update.suggested_action,
                    "promoted_to": update.promoted_to,
                }.items() if value is not None
            ]
        },
    )
    db.commit()
    db.refresh(learning)
    return _build_learning_response(db, learning)


@router.post("/{learning_id}/disable", response_model=LearningResponse)
async def disable_learning(
    learning_id: str,
    payload: LearningGovernanceActionRequest,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    _apply_learning_governance_action(learning, action="disable", note=payload.note)
    _record_learning_version(
        db,
        learning,
        event_type="governance:disable",
        change_note=payload.note,
        version_metadata={"action": "disable", "conversation_id": payload.conversation_id},
    )
    timeline_recording = _record_learning_timeline(
        db=db,
        conversation_id=payload.conversation_id,
        learning_id=learning.learning_id,
        event_type="learning_disabled",
        summary=f"Learning `{learning.learning_id}` 已禁用",
        detail=f"status={learning.status.value}",
        severity="warning",
        payload={"action": "disable"},
    )
    db.commit()
    db.refresh(learning)
    return _build_learning_response(
        db,
        learning,
        snapshot_ref=timeline_recording.get("snapshot_ref"),
        timeline_recording=timeline_recording,
    )


@router.post("/{learning_id}/rollback", response_model=LearningResponse)
async def rollback_learning(
    learning_id: str,
    payload: LearningGovernanceActionRequest,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    _apply_learning_governance_action(learning, action="rollback", note=payload.note)
    _record_learning_version(
        db,
        learning,
        event_type="governance:rollback",
        change_note=payload.note,
        version_metadata={"action": "rollback", "conversation_id": payload.conversation_id},
    )
    timeline_recording = _record_learning_timeline(
        db=db,
        conversation_id=payload.conversation_id,
        learning_id=learning.learning_id,
        event_type="learning_rolled_back",
        summary=f"Learning `{learning.learning_id}` 已回滚",
        detail=f"status={learning.status.value}",
        severity="warning",
        payload={"action": "rollback"},
    )
    db.commit()
    db.refresh(learning)
    return _build_learning_response(
        db,
        learning,
        snapshot_ref=timeline_recording.get("snapshot_ref"),
        timeline_recording=timeline_recording,
    )


@router.post("/{learning_id}/restore", response_model=LearningResponse)
async def restore_learning(
    learning_id: str,
    payload: LearningGovernanceActionRequest,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    _apply_learning_governance_action(learning, action="restore", note=payload.note)
    _record_learning_version(
        db,
        learning,
        event_type="governance:restore",
        change_note=payload.note,
        version_metadata={"action": "restore", "conversation_id": payload.conversation_id},
    )
    timeline_recording = _record_learning_timeline(
        db=db,
        conversation_id=payload.conversation_id,
        learning_id=learning.learning_id,
        event_type="learning_restored",
        summary=f"Learning `{learning.learning_id}` 已恢复",
        detail=f"status={learning.status.value}",
        severity="success",
        payload={"action": "restore"},
    )
    db.commit()
    db.refresh(learning)
    return _build_learning_response(
        db,
        learning,
        snapshot_ref=timeline_recording.get("snapshot_ref"),
        timeline_recording=timeline_recording,
    )


@router.post("/{learning_id}/promote", response_model=LearningResponse)
async def promote_learning(
    learning_id: str,
    payload: LearningGovernanceActionRequest,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    target_type = str(payload.target_type or "").strip().lower()
    if target_type not in {"best_practice", "system_prompt"}:
        if learning.category in {LearningCategory.BEST_PRACTICE, LearningCategory.CORRECTION}:
            target_type = "best_practice"
        else:
            target_type = "system_prompt"

    result = await _get_knowledge_transformer().transform_learning(
        learning_id=learning_id,
        target_type=target_type,
        db=db,
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error") or "Learning promotion failed")

    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found after promotion")
    _append_governance_note(
        learning,
        action=f"promote:{result.get('type') or target_type}:{result.get('id') or payload.promote_to or ''}",
        note=payload.note,
    )
    _record_learning_version(
        db,
        learning,
        event_type=f"governance:promote:{result.get('type') or target_type}",
        change_note=payload.note,
        version_metadata={
            "action": "promote",
            "target_type": result.get("type") or target_type,
            "promoted_id": result.get("id") or payload.promote_to,
            "conversation_id": payload.conversation_id,
        },
    )
    timeline_recording = _record_learning_timeline(
        db=db,
        conversation_id=payload.conversation_id,
        learning_id=learning.learning_id,
        event_type="learning_promoted",
        summary=f"Learning `{learning.learning_id}` 已提升",
        detail=f"target_type={result.get('type') or target_type} promoted_to={learning.promoted_to or ''}".strip(),
        severity="success",
        payload={
            "action": "promote",
            "target_type": result.get("type") or target_type,
            "promoted_id": result.get("id") or payload.promote_to,
        },
    )
    db.commit()
    db.refresh(learning)
    return _build_learning_response(
        db,
        learning,
        snapshot_ref=timeline_recording.get("snapshot_ref"),
        timeline_recording=timeline_recording,
    )


@router.post("/{learning_id}/review", response_model=LearningReviewResponse)
async def review_learning(
    learning_id: str,
    payload: LearningReviewCreate,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")

    try:
        review_status = LearningReviewStatus[payload.review_status.upper()]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Invalid review_status") from exc

    quality_score = payload.quality_score
    if quality_score is not None and not 1 <= int(quality_score) <= 5:
        raise HTTPException(status_code=400, detail="quality_score must be between 1 and 5")

    review = LearningReviewRecord(
        review_id=generate_id("LRV"),
        learning_id=learning.learning_id,
        review_status=review_status,
        quality_score=quality_score,
        reviewer=(payload.reviewer or "").strip() or None,
        review_note=(payload.review_note or "").strip() or None,
        review_metadata={
            "learning_status": learning.status.value if getattr(learning.status, "value", None) else str(learning.status),
            "source": learning.source,
            "pattern_key": learning.pattern_key,
        },
    )
    db.add(review)
    _record_learning_version(
        db,
        learning,
        event_type=f"review:{review_status.value}",
        actor=(payload.reviewer or "").strip() or None,
        change_note=payload.review_note,
        version_metadata={
            "review_id": review.review_id,
            "review_status": review_status.value,
            "quality_score": quality_score,
            "conversation_id": payload.conversation_id,
        },
    )
    timeline_recording = _record_learning_timeline(
        db=db,
        conversation_id=payload.conversation_id,
        learning_id=learning.learning_id,
        event_type=f"learning_review_{review_status.value}",
        summary=f"Learning `{learning.learning_id}` 已提交审核",
        detail=f"review_status={review_status.value} quality_score={quality_score if quality_score is not None else ''}".strip(),
        severity="success" if review_status == LearningReviewStatus.APPROVED else "warning" if review_status == LearningReviewStatus.NEEDS_CHANGES else "warning",
        payload={
            "review_id": review.review_id,
            "review_status": review_status.value,
            "quality_score": quality_score,
            "reviewer": (payload.reviewer or "").strip() or None,
        },
    )
    db.commit()
    db.refresh(review)
    return LearningReviewResponse(
        **model_to_dict(review),
        snapshot_ref=timeline_recording.get("snapshot_ref"),
        timeline_recording=timeline_recording,
    )


@router.get("/{learning_id}/review", response_model=Optional[LearningReviewResponse])
async def get_learning_review(
    learning_id: str,
    db: Session = Depends(get_db)
):
    review = db.query(LearningReviewRecord).filter(
        LearningReviewRecord.learning_id == learning_id
    ).order_by(
        LearningReviewRecord.created_at.desc(),
        LearningReviewRecord.id.desc()
    ).first()
    if not review:
        return None
    return LearningReviewResponse(**model_to_dict(review))


@router.get("/{learning_id}/history", response_model=List[LearningVersionResponse])
async def get_learning_history(
    learning_id: str,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")
    history = db.query(LearningVersionRecord).filter(
        LearningVersionRecord.learning_id == learning.learning_id
    ).order_by(
        LearningVersionRecord.created_at.desc(),
        LearningVersionRecord.id.desc()
    ).all()
    return [LearningVersionResponse(**_version_model_to_dict(version)) for version in history]


@router.get("/{learning_id}/compare", response_model=LearningVersionCompareResponse)
async def compare_learning_versions(
    learning_id: str,
    base_version_id: str,
    target_version_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")

    base_version = db.query(LearningVersionRecord).filter(
        LearningVersionRecord.learning_id == learning_id,
        LearningVersionRecord.version_id == base_version_id,
    ).first()
    if not base_version:
        raise HTTPException(status_code=404, detail="Base version not found")

    if target_version_id:
        target_version = db.query(LearningVersionRecord).filter(
            LearningVersionRecord.learning_id == learning_id,
            LearningVersionRecord.version_id == target_version_id,
        ).first()
        if not target_version:
            raise HTTPException(status_code=404, detail="Target version not found")
        target_snapshot = _learning_snapshot_from_version(target_version)
        target_label = target_version.version_id
    else:
        target_snapshot = _learning_snapshot_from_model(learning)
        target_label = "current"

    base_snapshot = _learning_snapshot_from_version(base_version)
    changed_fields = _compare_snapshots(base_snapshot, target_snapshot)
    return LearningVersionCompareResponse(
        learning_id=learning_id,
        base_label=base_version.version_id,
        target_label=target_label,
        changed_fields=[LearningVersionCompareFieldResponse(**item) for item in changed_fields],
        has_changes=bool(changed_fields),
    )


@router.post("/{learning_id}/merge-duplicate", response_model=LearningResponse)
async def merge_duplicate_learning(
    learning_id: str,
    payload: LearningDuplicateMergeRequest,
    db: Session = Depends(get_db)
):
    target_learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not target_learning:
        raise HTTPException(status_code=404, detail="Learning not found")

    source_learning_id = str(payload.source_learning_id or "").strip()
    if not source_learning_id or source_learning_id == learning_id:
        raise HTTPException(status_code=400, detail="source_learning_id is required and must be different from target")

    source_learning = db.query(Learning).filter(Learning.learning_id == source_learning_id).first()
    if not source_learning:
        raise HTTPException(status_code=404, detail="Source learning not found")
    if source_learning.status == LearningStatus.DISABLED:
        raise HTTPException(status_code=400, detail="Source learning is already disabled")

    target_pattern_key = str(target_learning.pattern_key or "").strip()
    source_pattern_key = str(source_learning.pattern_key or "").strip()
    if not target_pattern_key or target_pattern_key != source_pattern_key:
        raise HTTPException(status_code=400, detail="Only duplicate learnings with the same pattern_key can be merged")

    target_learning.tags = sorted(set(_normalize_tags(target_learning.tags) + _normalize_tags(source_learning.tags)))
    target_learning.recurrence_count = int(target_learning.recurrence_count or 0) + int(source_learning.recurrence_count or 0)
    target_learning.see_also = sorted(set((target_learning.see_also or []) + [source_learning.learning_id] + (source_learning.see_also or [])))
    merge_note = str(payload.note or "").strip()
    source_summary = str(source_learning.summary or "").strip()
    source_details = str(source_learning.details or "").strip()
    merged_block = f"[merged duplicate] source={source_learning.learning_id}"
    if source_summary:
        merged_block = f"{merged_block} summary={source_summary}"
    if merge_note:
        merged_block = f"{merged_block} note={merge_note}"
    if source_details:
        merged_block = f"{merged_block}\nsource_details={source_details}"
    target_learning.details = f"{str(target_learning.details or '').strip()}\n{merged_block}".strip()
    target_learning.updated_at = datetime.now()

    source_learning.status = LearningStatus.DISABLED
    source_learning.updated_at = datetime.now()
    source_learning.tags = sorted(set(_normalize_tags(source_learning.tags) + ["disabled", f"merged_into:{target_learning.learning_id}"]))
    _append_governance_note(source_learning, action=f"merge_duplicate:{target_learning.learning_id}", note=merge_note)

    _record_learning_version(
        db,
        target_learning,
        event_type="conflict:merge_duplicate",
        change_note=merge_note or f"merged {source_learning.learning_id}",
        version_metadata={"source_learning_id": source_learning.learning_id, "conversation_id": payload.conversation_id},
    )
    _record_learning_version(
        db,
        source_learning,
        event_type="conflict:merged_source",
        change_note=merge_note or f"merged into {target_learning.learning_id}",
        version_metadata={"target_learning_id": target_learning.learning_id, "conversation_id": payload.conversation_id},
    )
    timeline_recording = _record_learning_timeline(
        db=db,
        conversation_id=payload.conversation_id,
        learning_id=target_learning.learning_id,
        event_type="learning_duplicate_merged",
        summary=f"Learning `{target_learning.learning_id}` 已合并重复项",
        detail=f"source_learning_id={source_learning.learning_id}",
        severity="info",
        payload={"source_learning_id": source_learning.learning_id},
    )
    db.commit()
    db.refresh(target_learning)
    return _build_learning_response(
        db,
        target_learning,
        snapshot_ref=timeline_recording.get("snapshot_ref"),
        timeline_recording=timeline_recording,
    )


@router.post("/{learning_id}/apply-version", response_model=LearningVersionApplyResponse)
async def apply_learning_version(
    learning_id: str,
    payload: LearningVersionApplyRequest,
    db: Session = Depends(get_db)
):
    learning = db.query(Learning).filter(Learning.learning_id == learning_id).first()
    if not learning:
        raise HTTPException(status_code=404, detail="Learning not found")

    version_id = str(payload.version_id or "").strip()
    if not version_id:
        raise HTTPException(status_code=400, detail="version_id is required")

    version = db.query(LearningVersionRecord).filter(
        LearningVersionRecord.learning_id == learning_id,
        LearningVersionRecord.version_id == version_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    snapshot = _learning_snapshot_from_version(version)
    applied_fields = _apply_snapshot_to_learning(learning, snapshot, payload.fields)
    if not applied_fields:
        raise HTTPException(status_code=400, detail="No valid fields selected for version apply")
    apply_note = str(payload.note or "").strip() or f"applied version {version.version_id}"
    timeline_recording = _record_learning_timeline(
        db=db,
        conversation_id=payload.conversation_id,
        learning_id=learning.learning_id,
        event_type="learning_version_applied",
        summary=f"Learning `{learning.learning_id}` 已应用历史版本",
        detail=f"version_id={version.version_id} fields={','.join(applied_fields)}",
        severity="info",
        payload={
            "applied_version_id": version.version_id,
            "applied_fields": applied_fields,
        },
    )
    _append_governance_note(learning, action=f"apply_version:{version.version_id}", note=apply_note)
    _record_learning_version(
        db,
        learning,
        event_type="version:applied",
        change_note=apply_note,
        version_metadata={
            "applied_version_id": version.version_id,
            "applied_fields": applied_fields,
            "conversation_id": payload.conversation_id,
            "snapshot_ref": timeline_recording.get("snapshot_ref"),
        },
    )
    db.commit()
    db.refresh(learning)
    return LearningVersionApplyResponse(
        learning=_build_learning_response(db, learning),
        applied_version_id=version.version_id,
        note=apply_note,
        applied_fields=applied_fields,
        snapshot_ref=timeline_recording.get("snapshot_ref"),
        timeline_recording=timeline_recording,
    )


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
