"""Unified AI capability runtime API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

try:
    from capability_runtime.service import get_capability_runtime_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.capability_runtime.service import get_capability_runtime_service


router = APIRouter(prefix="/api", tags=["capabilities"])


def _not_found(capability_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "CAPABILITY_NOT_FOUND",
                "message": f"Capability not found: {capability_id}",
                "capability_id": capability_id,
            }
        },
    )


@router.get("/capabilities")
def list_capabilities() -> dict[str, Any]:
    return get_capability_runtime_service().list_capabilities()


@router.get("/capabilities/heartbeat")
def get_capability_provider_heartbeat() -> dict[str, Any]:
    return get_capability_runtime_service().get_provider_heartbeat()


@router.get("/capabilities/{capability_id}")
def get_capability(capability_id: str):
    try:
        return get_capability_runtime_service().get_capability(capability_id)
    except LookupError:
        return _not_found(capability_id)


@router.get("/capabilities/{capability_id}/health")
def get_capability_health(capability_id: str):
    try:
        return get_capability_runtime_service().get_capability_health(capability_id)
    except LookupError:
        return _not_found(capability_id)


@router.post("/capabilities/{capability_id}/invoke")
def invoke_capability(capability_id: str, payload: dict[str, Any]):
    try:
        result = get_capability_runtime_service().invoke(capability_id, payload)
    except LookupError:
        return _not_found(capability_id)
    if result.get("ok"):
        return result
    return JSONResponse(status_code=503, content=result)


@router.post("/capabilities/{capability_id}/test")
def test_capability(capability_id: str, payload: dict[str, Any] | None = None):
    try:
        result = get_capability_runtime_service().test_capability(capability_id, payload or {})
    except LookupError:
        return _not_found(capability_id)
    if result.get("ok"):
        return result
    if result.get("error", {}).get("code") == "CAPABILITY_TEST_UNSUPPORTED_MEDIA_TYPE":
        return JSONResponse(status_code=400, content=result)
    return JSONResponse(status_code=503, content=result)


@router.websocket("/capabilities/{capability_id}/stream")
async def stream_capability(capability_id: str, websocket: WebSocket):
    await websocket.accept()
    try:
        target = get_capability_runtime_service().get_stream_proxy_target(capability_id)
    except LookupError:
        await websocket.send_json(
            {
                "ok": False,
                "error": {
                    "code": "CAPABILITY_NOT_FOUND",
                    "message": f"Capability not found: {capability_id}",
                    "capability_id": capability_id,
                },
            }
        )
        await websocket.close(code=1000)
        return

    if not target.get("ok"):
        await websocket.send_json({"ok": False, "error": target.get("error") or {}})
        await websocket.close(code=1000)
        return

    try:
        import websockets

        async with websockets.connect(target["url"]) as provider_ws:
            while True:
                client_message = await websocket.receive()
                audio_bytes = client_message.get("bytes")
                text = client_message.get("text")
                if audio_bytes is not None:
                    await provider_ws.send(audio_bytes)
                elif text is not None:
                    await provider_ws.send(text)
                else:
                    continue

                provider_message = await provider_ws.recv()
                if isinstance(provider_message, bytes):
                    await websocket.send_bytes(provider_message)
                else:
                    await websocket.send_text(str(provider_message))
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_json(
            {
                "ok": False,
                "error": {
                    "code": "CAPABILITY_STREAM_PROVIDER_ERROR",
                    "message": f"ASR stream proxy failed: {exc}",
                    "provider": target.get("provider") or "unknown",
                },
            }
        )
        await websocket.close(code=1011)
