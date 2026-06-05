"""Service facade for capability discovery, health, and invocation."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from .contracts import CONTRACT_VERSION, CapabilityDefinition
from .registry import CapabilityRegistry, get_default_capability_registry


@dataclass
class ProviderHeartbeatState:
    failure_count: int = 0
    circuit_open_until: float = 0.0
    last_error: dict[str, Any] | None = None


class CapabilityRuntimeService:
    def __init__(self, registry: CapabilityRegistry | None = None):
        self.registry = registry or get_default_capability_registry()
        self._provider_heartbeat_state: dict[str, ProviderHeartbeatState] = {}
        self._heartbeat_failure_threshold = 3
        self._heartbeat_cooldown_seconds = 30.0
        self._load_heartbeat_config()

    def list_capabilities(self) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "capabilities": [
                self._capability_contract(capability)
                for capability in self.registry.list()
            ],
        }

    def get_capability(self, capability_id: str) -> dict[str, Any]:
        return self._capability_contract(self.registry.get(capability_id))

    def get_capability_health(self, capability_id: str) -> dict[str, Any]:
        capability = self.registry.get(capability_id)
        contract = self._capability_contract(capability)
        provider_health = self._resolve_health(capability)
        health = {
            "capability_id": capability.capability_id,
            "kind": capability.kind,
            "provider": capability.provider,
            "transport": capability.transport,
            "status": contract.get("status") or "unknown",
            "reason": contract.get("reason") or "",
            "provider_health": provider_health,
        }
        if contract.get("error"):
            health["error"] = contract["error"]
        return health

    def get_stream_proxy_target(self, capability_id: str) -> dict[str, Any]:
        capability = self.registry.get(capability_id)
        base_url = str(capability.metadata.get("provider_base_url") or "").strip()
        stream_path = str(capability.metadata.get("provider_stream_path") or "").strip()
        if capability.kind != "asr" or not base_url or not stream_path:
            return {
                "ok": False,
                "capability_id": capability.capability_id,
                "provider": capability.provider,
                "error": {
                    "code": "CAPABILITY_STREAM_UNAVAILABLE",
                    "message": "Capability does not expose an external realtime stream endpoint.",
                },
            }
        return {
            "ok": True,
            "capability_id": capability.capability_id,
            "provider": capability.provider,
            "url": self._to_websocket_url(urljoin(f"{base_url.rstrip('/')}/", stream_path.lstrip("/"))),
        }

    def invoke(self, capability_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        capability = self.registry.get(capability_id)
        if capability.invoker is None:
            return {
                "ok": False,
                "capability_id": capability.capability_id,
                "provider": capability.provider,
                "error": {
                    "code": "CAPABILITY_INVOKER_UNAVAILABLE",
                    "message": "Capability does not expose a local invoker.",
                },
            }
        result = capability.invoker(payload)
        if result.get("ok"):
            if "result" in result and "capability_id" in result:
                return result
            return {
                "ok": True,
                "capability_id": capability.capability_id,
                "provider": result.get("provider") or capability.provider,
                "result": {
                    key: value
                    for key, value in result.items()
                    if key not in {"ok", "provider"}
                },
            }
        return {
            "ok": False,
            "capability_id": capability.capability_id,
            "provider": capability.provider,
            "error": result.get("error") or {
                "code": "CAPABILITY_INVOCATION_FAILED",
                "message": "Capability invocation failed.",
            },
        }

    def test_capability(self, capability_id: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        capability = self.registry.get(capability_id)
        request_payload = dict(request or {})
        payload = dict(request_payload.get("payload") or {})
        mode = str(request_payload.get("mode") or "default").strip() or "default"
        started_at = perf_counter()

        if capability.kind == "asr" and not str(payload.get("audio_base64") or "").strip():
            health = self.get_capability_health(capability_id)
            latency_ms = round((perf_counter() - started_at) * 1000)
            ok = health.get("status") == "ready"
            result = {
                "ok": ok,
                "capability_id": capability_id,
                "provider": capability.provider,
                "status": health.get("status") or "unknown",
                "mode": "health_only",
                "latency_ms": latency_ms,
                "result_summary": {
                    "health_status": health.get("status") or "unknown",
                    "reason": health.get("reason") or "",
                },
            }
            if health.get("error"):
                result["error"] = health["error"]
            return result

        if capability.kind == "asr" and not self._is_supported_asr_media_type(payload.get("media_type")):
            latency_ms = round((perf_counter() - started_at) * 1000)
            return {
                "ok": False,
                "capability_id": capability_id,
                "provider": capability.provider,
                "status": "invalid_input",
                "mode": mode,
                "latency_ms": latency_ms,
                "error": {
                    "code": "CAPABILITY_TEST_UNSUPPORTED_MEDIA_TYPE",
                    "message": (
                        "ASR active test expects 16kHz mono PCM s16le audio. "
                        "Transcode compressed formats such as MP3 before invoking this capability."
                    ),
                    "media_type": str(payload.get("media_type") or ""),
                },
            }

        if capability.kind == "tts":
            payload.setdefault("text", "您好，这是 MyPrivateAgent 的语音能力测试。")

        invocation = self.invoke(capability_id, payload)
        latency_ms = round((perf_counter() - started_at) * 1000)
        if not invocation.get("ok"):
            return {
                "ok": False,
                "capability_id": capability_id,
                "provider": capability.provider,
                "status": "error",
                "mode": mode,
                "latency_ms": latency_ms,
                "error": invocation.get("error") or {
                    "code": "CAPABILITY_TEST_FAILED",
                    "message": "Capability test failed.",
                },
            }

        summary = self._summarize_test_result(capability, invocation.get("result") or {})
        return {
            "ok": True,
            "capability_id": capability_id,
            "provider": invocation.get("provider") or capability.provider,
            "status": "ok",
            "mode": mode,
            "latency_ms": latency_ms,
            "result_summary": summary,
        }

    def _capability_contract(self, capability: CapabilityDefinition) -> dict[str, Any]:
        health = self._resolve_health(capability)
        contract = capability.to_contract(
            status=str(health.get("status") or "unknown"),
            reason=str(health.get("reason") or ""),
        )
        if health.get("error"):
            contract["error"] = health["error"]
        return contract

    @staticmethod
    def _is_supported_asr_media_type(media_type: Any) -> bool:
        value = str(media_type or "application/octet-stream").lower().strip()
        return value.startswith("audio/pcm") or value == "application/octet-stream"

    @staticmethod
    def _to_websocket_url(url: str) -> str:
        parsed = urlparse(url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse(parsed._replace(scheme=scheme))

    @staticmethod
    def _summarize_test_result(capability: CapabilityDefinition, result: dict[str, Any]) -> dict[str, Any]:
        if capability.kind == "tts":
            audio_base64 = str(result.get("audio_base64") or "")
            return {
                "media_type": str(result.get("media_type") or ""),
                "audio_base64_length": len(audio_base64),
                "audio_base64": audio_base64,
            }
        if capability.kind == "asr":
            nested = result.get("result") if isinstance(result.get("result"), dict) else result
            return {
                "text": str(nested.get("text") or ""),
                "language": str(nested.get("language") or ""),
                "partial": bool(nested.get("partial")),
            }
        return result

    def _resolve_status(self, capability: CapabilityDefinition) -> tuple[str, str]:
        health = self._resolve_health(capability)
        return str(health.get("status") or "unknown"), str(health.get("reason") or "")

    def _resolve_health(self, capability: CapabilityDefinition) -> dict[str, Any]:
        if capability.health_checker is not None:
            health = capability.health_checker()
            if isinstance(health, dict):
                return health
        if capability.metadata.get("runtime") != "voice_runtime":
            return {"status": "unknown", "reason": ""}
        try:
            from voice_runtime.service import get_voice_runtime_service
        except ModuleNotFoundError:
            from backend.voice_runtime.service import get_voice_runtime_service
        voice_capabilities = get_voice_runtime_service().get_capabilities()
        key = "tts" if capability.kind == "tts" else "asr"
        provider_status = voice_capabilities.get(key) or {}
        return {
            "status": str(provider_status.get("status") or "unknown"),
            "reason": str(provider_status.get("reason") or ""),
        }

    def get_provider_heartbeat(self) -> dict[str, Any]:
        providers: dict[str, dict[str, Any]] = {}
        for capability in self.registry.list():
            base_url = str(capability.metadata.get("provider_base_url") or "").strip()
            provider_key = base_url or "local"
            provider = providers.setdefault(
                provider_key,
                {
                    "provider_id": capability.metadata.get("external_provider") or capability.provider,
                    "base_url": base_url,
                    "transport": capability.transport,
                    "status": "unknown",
                    "reason": "",
                    "capabilities": [],
                },
            )
            provider["capabilities"].append(self.get_capability_health(capability.capability_id))
            if base_url and provider["status"] == "unknown":
                provider.update(self._probe_provider_heartbeat(capability))
        return {
            "contract_version": CONTRACT_VERSION,
            "providers": list(providers.values()),
        }

    def _probe_provider_heartbeat(self, capability: CapabilityDefinition) -> dict[str, Any]:
        from .clients.http_client import CapabilityProviderError, HttpCapabilityClient

        base_url = str(capability.metadata.get("provider_base_url") or "").strip()
        heartbeat_path = str(capability.metadata.get("provider_heartbeat_path") or "/health")
        if not base_url:
            return {"status": "unknown", "reason": "No provider base URL configured."}
        breaker = self._provider_heartbeat_state.setdefault(base_url, ProviderHeartbeatState())
        now = perf_counter()
        if breaker.circuit_open_until > now:
            retry_after_seconds = round(breaker.circuit_open_until - now, 2)
            return {
                "status": "unreachable",
                "reason": (
                    f"Provider heartbeat circuit open after {breaker.failure_count} failures; "
                    f"retry after {retry_after_seconds}s."
                ),
                "error": breaker.last_error
                or {
                    "code": "CAPABILITY_PROVIDER_CIRCUIT_OPEN",
                    "message": "Provider heartbeat circuit is open.",
                },
                "circuit_breaker": {
                    "state": "open",
                    "failure_count": breaker.failure_count,
                    "retry_after_seconds": retry_after_seconds,
                },
            }

        def do_probe() -> dict[str, Any]:
            if capability.heartbeat_checker is not None:
                return capability.heartbeat_checker()
            return HttpCapabilityClient(base_url=base_url).get_json(heartbeat_path)

        try:
            data = do_probe()
            if data.get("error"):
                raise CapabilityProviderError(
                    str(data["error"].get("code") or "CAPABILITY_PROVIDER_UNREACHABLE"),
                    str(data["error"].get("message") or data.get("reason") or "Provider heartbeat failed."),
                )
        except CapabilityProviderError as exc:
            breaker.failure_count += 1
            breaker.last_error = exc.to_payload()
            response: dict[str, Any] = {
                "status": "unreachable",
                "reason": exc.message,
                "error": exc.to_payload(),
                "circuit_breaker": {
                    "state": "closed",
                    "failure_count": breaker.failure_count,
                    "threshold": self._heartbeat_failure_threshold,
                    "cooldown_seconds": self._heartbeat_cooldown_seconds,
                },
            }
            if breaker.failure_count >= self._heartbeat_failure_threshold:
                breaker.circuit_open_until = now + self._heartbeat_cooldown_seconds
                response["circuit_breaker"] = {
                    "state": "open",
                    "failure_count": breaker.failure_count,
                    "threshold": self._heartbeat_failure_threshold,
                    "cooldown_seconds": self._heartbeat_cooldown_seconds,
                    "retry_after_seconds": round(self._heartbeat_cooldown_seconds, 2),
                }
                response["reason"] = (
                    f"{exc.message} (heartbeat circuit opened for {self._heartbeat_cooldown_seconds:.0f}s)"
                )
            return response
        breaker.failure_count = 0
        breaker.circuit_open_until = 0.0
        breaker.last_error = None
        return {
            "status": str(data.get("status") or "unknown"),
            "reason": str(data.get("message") or ""),
            "raw": data,
            "circuit_breaker": {
                "state": "closed",
                "failure_count": 0,
                "threshold": self._heartbeat_failure_threshold,
                "cooldown_seconds": self._heartbeat_cooldown_seconds,
            },
        }

    def _load_heartbeat_config(self) -> None:
        try:
            from backend import config as app_config
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            import config as app_config

        threshold = int(getattr(app_config, "CAPABILITY_PROVIDER_HEARTBEAT_FAILURE_THRESHOLD", 3))
        cooldown_seconds = float(getattr(app_config, "CAPABILITY_PROVIDER_HEARTBEAT_COOLDOWN_SECONDS", 30.0))
        self._heartbeat_failure_threshold = max(1, threshold)
        self._heartbeat_cooldown_seconds = max(1.0, cooldown_seconds)


def get_capability_runtime_service() -> CapabilityRuntimeService:
    global _capability_runtime_service_singleton
    try:
        service = _capability_runtime_service_singleton
    except NameError:
        service = None
    if service is None:
        service = CapabilityRuntimeService()
        _capability_runtime_service_singleton = service
    return service
