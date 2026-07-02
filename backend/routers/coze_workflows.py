"""Coze migration workflow registry APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

try:
    from capability_runtime.service import get_capability_runtime_service
    from services.coze_workflow_lab_service import get_coze_workflow_lab_service
    from services.coze_workflow_registry_service import get_coze_workflow_registry_service
except ModuleNotFoundError:
    from backend.capability_runtime.service import get_capability_runtime_service
    from backend.services.coze_workflow_lab_service import get_coze_workflow_lab_service
    from backend.services.coze_workflow_registry_service import get_coze_workflow_registry_service


router = APIRouter(prefix="/api", tags=["coze-workflows"])


@router.get("/coze-workflows")
def list_coze_workflows() -> dict[str, Any]:
    return get_coze_workflow_registry_service().build_runtime_contract()


@router.get("/coze-workflow-lab")
def list_coze_workflow_lab() -> dict[str, Any]:
    return get_coze_workflow_lab_service().list_workflows()


@router.get("/coze-workflow-lab/{workflow_id}")
def get_coze_workflow_lab_detail(workflow_id: str) -> dict[str, Any]:
    workflow = get_coze_workflow_lab_service().get_workflow_detail(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coze workflow not found: {workflow_id}",
            headers={"X-Workflow-Error": "COZE_WORKFLOW_NOT_FOUND"},
        )
    return workflow


@router.get("/coze-workflow-lab/{workflow_id}/examples/{example_id}")
def get_coze_workflow_lab_example(workflow_id: str, example_id: str) -> dict[str, Any]:
    example = get_coze_workflow_lab_service().load_example(workflow_id, example_id)
    if example is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coze workflow example not found: {workflow_id}/{example_id}",
            headers={"X-Workflow-Error": "COZE_WORKFLOW_EXAMPLE_NOT_FOUND"},
        )
    return example


@router.post("/coze-workflow-lab/{workflow_id}/examples/{example_id}/invoke")
def invoke_coze_workflow_lab_example(workflow_id: str, example_id: str) -> dict[str, Any]:
    replay = get_coze_workflow_lab_service().invoke_example(workflow_id, example_id)
    if replay is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coze workflow example not found: {workflow_id}/{example_id}",
            headers={"X-Workflow-Error": "COZE_WORKFLOW_EXAMPLE_NOT_FOUND"},
        )
    if replay.get("status") == "completed":
        return replay
    return JSONResponse(status_code=503, content=replay)


@router.get("/coze-workflows/{workflow_id}")
def get_coze_workflow(workflow_id: str) -> dict[str, Any]:
    workflow = get_coze_workflow_registry_service().get_workflow_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coze workflow not found: {workflow_id}",
            headers={"X-Workflow-Error": "COZE_WORKFLOW_NOT_FOUND"},
        )
    return workflow


@router.get("/coze-workflows/{workflow_id}/readiness")
def get_coze_workflow_readiness(workflow_id: str) -> dict[str, Any]:
    workflow = get_coze_workflow_registry_service().get_workflow_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coze workflow not found: {workflow_id}",
            headers={"X-Workflow-Error": "COZE_WORKFLOW_NOT_FOUND"},
        )
    readiness = workflow.get("readiness", {})
    return {
        "workflow_id": workflow_id,
        "status": readiness.get("status"),
        "reason": readiness.get("reason"),
        "blockers": readiness.get("blockers", []),
        "capability_id": workflow.get("capability_id"),
    }


@router.get("/coze-workflows/{workflow_id}/capability")
def get_coze_workflow_capability(workflow_id: str) -> dict[str, Any]:
    workflow = get_coze_workflow_registry_service().get_workflow_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coze workflow not found: {workflow_id}",
            headers={"X-Workflow-Error": "COZE_WORKFLOW_NOT_FOUND"},
        )
    readiness = workflow.get("readiness", {})
    return {
        "capability_id": workflow.get("capability_id"),
        "workflow_id": workflow_id,
        "name": workflow.get("name"),
        "version": workflow.get("version"),
        "status": workflow.get("status"),
        "readiness": readiness.get("status"),
        "readiness_blockers": readiness.get("blockers", []),
        "inputs": workflow.get("inputs", {}).get("schema"),
        "outputs": workflow.get("outputs", {}).get("schema"),
        "owner": workflow.get("owner", {}).get("primary"),
        "governance": {
            "permission_level": workflow.get("governance", {}).get("permission_level"),
            "trace_required": workflow.get("governance", {}).get("trace_required"),
            "approval_required": workflow.get("governance", {}).get("approval_required"),
        },
    }


@router.post("/coze-workflows/{workflow_id}/invoke")
def invoke_coze_workflow(workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    workflow = get_coze_workflow_registry_service().get_workflow_by_id(workflow_id)
    if workflow is None:
        raise HTTPException(
            status_code=404,
            detail=f"Coze workflow not found: {workflow_id}",
            headers={"X-Workflow-Error": "COZE_WORKFLOW_NOT_FOUND"},
        )

    capability_id = str(workflow.get("capability_id") or f"coze.workflow.{workflow_id}").strip()
    try:
        result = get_capability_runtime_service().invoke(capability_id, payload)
    except LookupError:
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "workflow_id": workflow_id,
                "capability_id": capability_id,
                "workflow_version": str(workflow.get("version") or ""),
                "run_id": None,
                "status": "blocked",
                "error": {
                    "code": "COZE_WORKFLOW_CAPABILITY_NOT_REGISTERED",
                    "message": f"Workflow capability not registered: {capability_id}",
                    "blockers": ["capability_runtime_missing_registration"],
                    "details": {},
                },
                "authorization": {
                    "status": "not_evaluated",
                    "policy": "placeholder",
                    "reason": "Workflow API authorization is not implemented in this change.",
                },
                "invocation_policy": dict(workflow.get("invocation_policy") or {
                    "allowed_callers": [],
                    "approval_required": False,
                    "permission_level": "",
                    "placeholder": True,
                }),
                "trace_summary": {
                    "workflow_id": workflow_id,
                    "workflow_version": str(workflow.get("version") or ""),
                    "source": "coze_migration",
                },
                "trace": {
                    "workflow_id": workflow_id,
                    "workflow_version": str(workflow.get("version") or ""),
                    "source": "coze_migration",
                },
            },
        )

    if result.get("ok"):
        return result

    error_code = str(result.get("error", {}).get("code") or "")
    status_code = 503
    if error_code in {"COZE_WORKFLOW_INVALID_MANIFEST", "COZE_WORKFLOW_SCHEMA_VALIDATION_FAILED"}:
        status_code = 400
    return JSONResponse(status_code=status_code, content=result)
