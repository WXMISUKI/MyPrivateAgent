from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated, List, Optional

try:
    from agent_server.dependencies import get_current_user, get_db
    from agent_server.http import ensure_exists, success_response
    from models import User
    from schemas import (
        PlanCreate,
        PlanGenerateRequest,
        PlanItemCreate,
        PlanItemUpdate,
        PlanResponse,
        PlanUpdate,
    )
    from services.planner_service import PlannerService
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server.dependencies import get_current_user, get_db
    from backend.agent_server.http import ensure_exists, success_response
    from backend.models import User
    from backend.schemas import (
        PlanCreate,
        PlanGenerateRequest,
        PlanItemCreate,
        PlanItemUpdate,
        PlanResponse,
        PlanUpdate,
    )
    from backend.services.planner_service import PlannerService


router = APIRouter(prefix="/api/plans", tags=["Planner"])


@router.get("", response_model=List[PlanResponse])
def list_plans(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    conversation_id: Optional[int] = None,
    limit: int = 20,
):
    service = PlannerService(db)
    plans = service.list_plans(
        user_id=current_user.id,
        conversation_id=conversation_id,
        limit=max(1, min(limit, 100)),
    )
    return [service.serialize_plan(plan) for plan in plans]


@router.post("", response_model=PlanResponse)
def create_plan(
    payload: PlanCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = PlannerService(db)
    try:
        plan = service.create_plan(
            user_id=current_user.id,
            objective=payload.objective,
            conversation_id=payload.conversation_id,
            source=payload.source,
            items=[item.model_dump() for item in payload.items],
        )
        return service.serialize_plan(plan)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/generate", response_model=PlanResponse)
def generate_plan(
    payload: PlanGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = PlannerService(db)
    try:
        plan = service.generate_plan(
            user_id=current_user.id,
            objective=payload.objective,
            conversation_id=payload.conversation_id,
            source=payload.source,
        )
        return service.serialize_plan(plan)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{plan_id}", response_model=PlanResponse)
def get_plan(
    plan_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = PlannerService(db)
    plan = ensure_exists(service.get_plan(plan_id=plan_id, user_id=current_user.id), "计划不存在")
    return service.serialize_plan(plan)


@router.patch("/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    payload: PlanUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = PlannerService(db)
    plan = ensure_exists(service.get_plan(plan_id=plan_id, user_id=current_user.id), "计划不存在")
    try:
        updated = service.update_plan(
            plan=plan,
            objective=payload.objective,
            summary=payload.summary,
            status=payload.status,
        )
        return service.serialize_plan(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{plan_id}/items", response_model=PlanResponse)
def add_plan_item(
    plan_id: int,
    payload: PlanItemCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = PlannerService(db)
    plan = ensure_exists(service.get_plan(plan_id=plan_id, user_id=current_user.id), "计划不存在")
    try:
        updated = service.add_plan_item(
            plan=plan,
            title=payload.title,
            details=payload.details,
            status=payload.status,
            owner=payload.owner,
            agent_role=payload.agent_role,
            agent_id=payload.agent_id,
            handoff_status=payload.handoff_status,
            required_capabilities=payload.required_capabilities,
            step_order=payload.step_order,
        )
        return service.serialize_plan(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{plan_id}/items/{item_id}", response_model=PlanResponse)
def update_plan_item(
    plan_id: int,
    item_id: int,
    payload: PlanItemUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = PlannerService(db)
    plan = ensure_exists(service.get_plan(plan_id=plan_id, user_id=current_user.id), "计划不存在")
    try:
        updated = service.update_plan_item(
            plan=plan,
            item_id=item_id,
            title=payload.title,
            details=payload.details,
            status=payload.status,
            owner=payload.owner,
            agent_role=payload.agent_role,
            agent_id=payload.agent_id,
            handoff_status=payload.handoff_status,
            required_capabilities=payload.required_capabilities,
            step_order=payload.step_order,
        )
        return service.serialize_plan(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{plan_id}/items/{item_id}", response_model=PlanResponse)
def delete_plan_item(
    plan_id: int,
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    service = PlannerService(db)
    plan = ensure_exists(service.get_plan(plan_id=plan_id, user_id=current_user.id), "计划不存在")
    try:
        updated = service.delete_plan_item(plan=plan, item_id=item_id)
        return service.serialize_plan(updated)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
