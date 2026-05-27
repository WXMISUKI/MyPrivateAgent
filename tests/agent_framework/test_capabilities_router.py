import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.capability_runtime.providers.voice_provider import build_voice_capabilities
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService
from backend.routers.capabilities import router as capabilities_router
from backend.voice_runtime.service import VoiceRuntimeSettings


class CapabilitiesRouterTests(unittest.TestCase):
    def setUp(self):
        self.service = CapabilityRuntimeService(CapabilityRegistry(build_voice_capabilities()))
        self.service_patcher = patch(
            "backend.routers.capabilities.get_capability_runtime_service",
            return_value=self.service,
        )
        self.settings_patcher = patch(
            "backend.voice_runtime.service.VoiceRuntimeSettings.from_config",
            return_value=VoiceRuntimeSettings(enabled=False),
        )
        self.service_patcher.start()
        self.settings_patcher.start()
        self.addCleanup(self.service_patcher.stop)
        self.addCleanup(self.settings_patcher.stop)

        app = FastAPI()
        app.include_router(capabilities_router)
        self.client = TestClient(app)

    def test_list_capabilities_endpoint(self):
        response = self.client.get("/api/capabilities")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["contract_version"], "capability-runtime-v1")
        self.assertTrue(any(item["capability_id"] == "voice.tts.edge" for item in payload["capabilities"]))

    def test_get_capability_endpoint(self):
        response = self.client.get("/api/capabilities/voice.tts.edge")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["capability_id"], "voice.tts.edge")

    def test_health_endpoint(self):
        response = self.client.get("/api/capabilities/voice.tts.edge/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["capability_id"], "voice.tts.edge")

    def test_heartbeat_endpoint(self):
        response = self.client.get("/api/capabilities/heartbeat")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["contract_version"], "capability-runtime-v1")
        self.assertTrue(payload["providers"])

    def test_test_endpoint_returns_structured_response(self):
        response = self.client.post("/api/capabilities/voice.asr.vosk/test", json={})

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["capability_id"], "voice.asr.vosk")
        self.assertEqual(payload["mode"], "health_only")
        self.assertEqual(payload["status"], "disabled")

    def test_unknown_capability_endpoint_returns_404(self):
        response = self.client.post("/api/capabilities/unknown/invoke", json={})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "CAPABILITY_NOT_FOUND")

    def test_invoke_voice_capability_returns_structured_envelope(self):
        response = self.client.post("/api/capabilities/voice.tts.edge/invoke", json={"text": "hello"})

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["capability_id"], "voice.tts.edge")
        self.assertEqual(payload["error"]["code"], "VOICE_RUNTIME_DISABLED")


if __name__ == "__main__":
    unittest.main()
