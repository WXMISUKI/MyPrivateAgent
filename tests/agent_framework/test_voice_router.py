import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.agent_server.router_registry import get_api_router_registrations, get_route_group_names
from backend.routers.voice import router as voice_router


class VoiceRouterTests(unittest.TestCase):
    def _client(self):
        app = FastAPI()
        app.include_router(voice_router)
        return TestClient(app)

    def test_voice_router_is_registered_in_default_server_surface(self):
        names = tuple(registration.name for registration in get_api_router_registrations())

        self.assertIn("voice", names)
        self.assertIn("voice", get_route_group_names())

    def test_capabilities_endpoint_returns_disabled_contract(self):
        client = self._client()

        response = client.get("/api/voice/capabilities")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["contract_version"], "voice-runtime-v1")
        self.assertFalse(payload["enabled"])
        self.assertEqual(payload["asr"]["provider"], "vosk_server")
        self.assertEqual(payload["tts"]["provider"], "edge_tts")

    def test_tts_endpoint_returns_structured_unavailable_error_when_disabled(self):
        client = self._client()

        response = client.post("/api/voice/tts", json={"text": "你好"})

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "VOICE_RUNTIME_DISABLED")

    def test_asr_endpoint_returns_structured_unavailable_error_when_disabled(self):
        client = self._client()

        response = client.post(
            "/api/voice/asr",
            files={"file": ("sample.pcm", b"test", "audio/pcm")},
        )

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "VOICE_RUNTIME_DISABLED")


if __name__ == "__main__":
    unittest.main()
