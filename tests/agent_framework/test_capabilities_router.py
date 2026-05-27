import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.routers.capabilities import router as capabilities_router


class CapabilitiesRouterTests(unittest.TestCase):
    def setUp(self):
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

    def test_unknown_capability_endpoint_returns_404(self):
        response = self.client.post("/api/capabilities/unknown/invoke", json={})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "CAPABILITY_NOT_FOUND")

    def test_invoke_disabled_voice_capability_returns_503(self):
        response = self.client.post("/api/capabilities/voice.tts.edge/invoke", json={"text": "hello"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "VOICE_RUNTIME_DISABLED")


if __name__ == "__main__":
    unittest.main()
