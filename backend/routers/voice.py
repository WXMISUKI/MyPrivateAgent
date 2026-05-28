"""Legacy local voice runtime compatibility API.

New voice integrations should use /api/capabilities/voice.* through the
capability runtime. These routes remain for older callers and local fallback.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

try:
    from voice_runtime.service import get_voice_runtime_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.voice_runtime.service import get_voice_runtime_service


router = APIRouter(prefix="/api", tags=["voice"])


class VoiceTtsRequest(BaseModel):
    text: str
    voice: str | None = None
    rate: str | None = None
    volume: str | None = None
    pitch: str | None = None


@router.get("/voice/capabilities")
def get_voice_capabilities() -> dict[str, Any]:
    return get_voice_runtime_service().get_capabilities()


@router.post("/voice/tts")
async def synthesize_voice(request: VoiceTtsRequest):
    result = await get_voice_runtime_service().synthesize_speech_async(
        request.model_dump(exclude_none=True)
    )
    if not result.ok:
        return JSONResponse(
            status_code=503,
            content={"error": result.error.to_payload() if result.error else {}},
        )
    return Response(
        content=result.content or b"",
        media_type=result.media_type,
        headers={"X-Voice-Provider": result.provider},
    )


@router.post("/voice/asr")
async def transcribe_voice(file: UploadFile = File(...), language: str | None = None):
    content = await file.read()
    result = await get_voice_runtime_service().transcribe_audio_async(
        content,
        media_type=file.content_type or "application/octet-stream",
        language=language,
    )
    payload = result.to_payload()
    if not payload.get("ok"):
        return JSONResponse(status_code=503, content={"error": payload.get("error") or {}})
    return payload


@router.websocket("/voice/asr/ws")
async def stream_voice_asr(websocket: WebSocket):
    await websocket.accept()
    service = get_voice_runtime_service()
    capabilities = service.get_capabilities()
    asr_capability = capabilities.get("asr") or {}
    if not capabilities.get("enabled") or asr_capability.get("status") != "ready":
        await websocket.send_json(
            {
                "ok": False,
                "error": {
                    "code": "VOICE_PROVIDER_UNAVAILABLE"
                    if capabilities.get("enabled")
                    else "VOICE_RUNTIME_DISABLED",
                    "message": asr_capability.get("reason") or "Voice ASR streaming is unavailable.",
                    "provider": asr_capability.get("provider") or "vosk_server",
                },
            }
        )
        await websocket.close(code=1000)
        return

    import websockets

    try:
        async with websockets.connect(asr_capability.get("server_url")) as vosk_ws:
            sample_rate = int(asr_capability.get("sample_rate") or 16000)
            await vosk_ws.send(json.dumps({"config": {"sample_rate": sample_rate}}))
            while True:
                client_message = await websocket.receive()
                audio_bytes = client_message.get("bytes")
                if audio_bytes is not None:
                    await vosk_ws.send(audio_bytes)
                elif client_message.get("text") == "__end__":
                    await vosk_ws.send(json.dumps({"eof": 1}))
                else:
                    continue
                raw_result = await vosk_ws.recv()
                parsed = json.loads(raw_result) if isinstance(raw_result, str) else {}
                await websocket.send_json(
                    {
                        "ok": True,
                        "provider": asr_capability.get("provider") or "vosk_server",
                        "language": asr_capability.get("language") or "zh-cn",
                        "text": parsed.get("text") or parsed.get("partial") or "",
                        "partial": "partial" in parsed and "text" not in parsed,
                        "raw": parsed,
                    }
                )
    except WebSocketDisconnect:
        return
    except Exception as exc:
        await websocket.send_json(
            {
                "ok": False,
                "error": {
                    "code": "VOICE_PROVIDER_ERROR",
                    "message": f"Vosk streaming failed: {exc}",
                    "provider": asr_capability.get("provider") or "vosk_server",
                },
            }
        )
        await websocket.close(code=1011)
