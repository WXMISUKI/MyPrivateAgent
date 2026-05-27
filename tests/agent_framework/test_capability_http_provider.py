import json
import unittest

import httpx

from backend.capability_runtime.clients.http_client import HttpCapabilityClient
from backend.capability_runtime.providers.voice_http_provider import build_http_voice_capabilities
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class CapabilityHttpProviderTests(unittest.TestCase):
    def test_http_voice_capabilities_report_remote_health(self):
        def handler(request):
            if request.url.path == "/api/capabilities/voice.tts.edge/health":
                return _json_response(
                    {
                        "capability_id": "voice.tts.edge",
                        "kind": "tts",
                        "provider": "edge_tts",
                        "transport": "http",
                        "status": "ready",
                        "reason": "",
                    }
                )
            return _json_response({"status": "ok"})

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        capability = service.get_capability("voice.tts.edge")

        self.assertEqual(capability["transport"], "http")
        self.assertEqual(capability["status"], "ready")
        self.assertEqual(capability["metadata"]["provider_base_url"], "http://voice.test")

    def test_http_voice_invocation_delegates_to_remote_provider(self):
        def handler(request):
            self.assertEqual(request.url.path, "/api/capabilities/voice.tts.edge/invoke")
            payload = json.loads(request.content.decode("utf-8"))
            self.assertEqual(payload["text"], "hello")
            return _json_response(
                {
                    "ok": True,
                    "capability_id": "voice.tts.edge",
                    "provider": "edge_tts",
                    "result": {"media_type": "audio/mpeg", "audio_base64": "QUJD"},
                }
            )

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        result = service.invoke("voice.tts.edge", {"text": "hello"})

        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["audio_base64"], "QUJD")

    def test_http_voice_health_handles_unreachable_provider(self):
        def handler(request):
            raise httpx.ConnectError("connect failed", request=request)

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        health = service.get_capability_health("voice.asr.vosk")

        self.assertEqual(health["status"], "unreachable")
        self.assertEqual(health["error"]["code"], "CAPABILITY_PROVIDER_UNREACHABLE")

    def test_heartbeat_reports_provider_and_capability_status(self):
        def handler(request):
            if request.url.path == "/health":
                return _json_response({"status": "ok", "service": "unifiedTTSandASR"})
            if request.url.path.endswith("/health"):
                capability_id = request.url.path.split("/")[-2]
                return _json_response(
                    {
                        "capability_id": capability_id,
                        "provider": "edge_tts" if capability_id.endswith("edge") else "vosk_server",
                        "transport": "http",
                        "status": "ready",
                        "reason": "",
                    }
                )
            return _json_response({})

        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        service = CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )

        heartbeat = service.get_provider_heartbeat()

        self.assertEqual(heartbeat["contract_version"], "capability-runtime-v1")
        self.assertEqual(heartbeat["providers"][0]["status"], "ok")
        self.assertEqual(len(heartbeat["providers"][0]["capabilities"]), 2)


if __name__ == "__main__":
    unittest.main()
