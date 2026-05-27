import json
import unittest

import httpx

from backend.capability_runtime.clients.http_client import HttpCapabilityClient
from backend.capability_runtime.providers.voice_provider import build_voice_capabilities
from backend.capability_runtime.providers.voice_http_provider import build_http_voice_capabilities
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class CapabilityActiveTestTests(unittest.TestCase):
    def test_tts_active_test_invokes_provider_and_summarizes_audio(self):
        def handler(request):
            self.assertEqual(request.url.path, "/api/capabilities/voice.tts.edge/invoke")
            payload = json.loads(request.content.decode("utf-8"))
            self.assertTrue(payload["text"])
            return _json_response(
                {
                    "ok": True,
                    "capability_id": "voice.tts.edge",
                    "provider": "edge_tts",
                    "result": {"media_type": "audio/mpeg", "audio_base64": "QUJDRA=="},
                }
            )

        service = self._service(handler)

        result = service.test_capability("voice.tts.edge", {})

        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["result_summary"]["media_type"], "audio/mpeg")
        self.assertEqual(result["result_summary"]["audio_base64_length"], 8)
        self.assertEqual(result["result_summary"]["audio_base64"], "QUJDRA==")
        self.assertGreaterEqual(result["latency_ms"], 0)

    def test_asr_active_test_without_audio_uses_health_only(self):
        def handler(request):
            self.assertEqual(request.url.path, "/api/capabilities/voice.asr.vosk/health")
            return _json_response(
                {
                    "capability_id": "voice.asr.vosk",
                    "provider": "vosk_server",
                    "transport": "http",
                    "status": "ready",
                    "reason": "",
                }
            )

        service = self._service(handler)

        result = service.test_capability("voice.asr.vosk", {})

        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "health_only")
        self.assertEqual(result["status"], "ready")
        self.assertNotIn("text", result.get("result_summary", {}))

    def test_asr_active_test_rejects_compressed_audio(self):
        def handler(request):
            raise AssertionError("Compressed audio must not be forwarded to the ASR provider")

        service = self._service(handler)

        result = service.test_capability(
            "voice.asr.vosk",
            {
                "payload": {
                    "audio_base64": "//NkxAAAAANIAAAAAExBTUVVVVURtA7qIGMIwwxCHJg4XpMmT",
                    "media_type": "audio/mpeg",
                    "language": "zh-cn",
                }
            },
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "invalid_input")
        self.assertEqual(result["error"]["code"], "CAPABILITY_TEST_UNSUPPORTED_MEDIA_TYPE")

    def test_asr_stream_target_uses_external_provider_metadata(self):
        service = self._service(lambda request: _json_response({"status": "ready"}))

        result = service.get_stream_proxy_target("voice.asr.vosk")

        self.assertTrue(result["ok"])
        self.assertEqual(result["capability_id"], "voice.asr.vosk")
        self.assertEqual(result["url"], "ws://voice.test/api/voice/asr/ws")

    def test_asr_stream_target_requires_external_stream_metadata(self):
        service = CapabilityRuntimeService(CapabilityRegistry(build_voice_capabilities()))

        result = service.get_stream_proxy_target("voice.asr.vosk")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "CAPABILITY_STREAM_UNAVAILABLE")

    def test_active_test_returns_structured_error_for_unreachable_provider(self):
        def handler(request):
            raise httpx.ConnectError("connect failed", request=request)

        service = self._service(handler)

        result = service.test_capability("voice.tts.edge", {})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "CAPABILITY_PROVIDER_UNREACHABLE")

    def _service(self, handler):
        client = HttpCapabilityClient(
            base_url="http://voice.test",
            transport=httpx.MockTransport(handler),
        )
        return CapabilityRuntimeService(
            CapabilityRegistry(build_http_voice_capabilities(base_url="http://voice.test", client=client))
        )


if __name__ == "__main__":
    unittest.main()
