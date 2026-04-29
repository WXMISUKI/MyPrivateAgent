import unittest
from backend.agent_server.middleware import RequestIDMiddleware, get_request_id


class TestRequestIDMiddleware(unittest.TestCase):
    def test_get_request_id_returns_none_outside_request(self):
        self.assertIsNone(get_request_id())


class TestRequestIDMiddlewareIntegration(unittest.IsolatedAsyncioTestCase):
    async def test_middleware_sets_response_header(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_endpoint():
            return {"request_id": get_request_id()}

        client = TestClient(app)
        response = client.get("/test")
        self.assertEqual(response.status_code, 200)
        self.assertIn("X-Request-ID", response.headers)
        body = response.json()
        self.assertEqual(body["request_id"], response.headers["X-Request-ID"])

    async def test_middleware_uses_incoming_header(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RequestIDMiddleware)

        @app.get("/test")
        def test_endpoint():
            return {"request_id": get_request_id()}

        client = TestClient(app)
        response = client.get("/test", headers={"X-Request-ID": "custom-id-123"})
        self.assertEqual(response.json()["request_id"], "custom-id-123")
        self.assertEqual(response.headers["X-Request-ID"], "custom-id-123")


class TestUnifiedErrorHandler(unittest.IsolatedAsyncioTestCase):
    async def test_validation_error_returns_422_with_structure(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel

        app = FastAPI()

        from backend.agent_server.middleware import RequestIDMiddleware, install_error_handlers
        app.add_middleware(RequestIDMiddleware)
        install_error_handlers(app)

        class Item(BaseModel):
            name: str

        @app.post("/test")
        def test_endpoint(item: Item):
            return {"ok": True}

        client = TestClient(app, raise_server_exceptions=False)
        response = client.post("/test", json={"wrong_field": 1})
        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertIn("error", body)
        self.assertIn("code", body["error"])
        self.assertIn("message", body["error"])
        self.assertIn("request_id", body["error"])

    async def test_unhandled_exception_returns_500(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()

        from backend.agent_server.middleware import RequestIDMiddleware, install_error_handlers
        app.add_middleware(RequestIDMiddleware)
        install_error_handlers(app)

        @app.get("/boom")
        def boom():
            raise RuntimeError("unexpected")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/boom")
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["error"]["code"], "INTERNAL_ERROR")


if __name__ == "__main__":
    unittest.main()
