import json
import os
import uuid
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
from backend.agent_server.dependencies import get_db as dependency_get_db
from backend.database import Base, get_db as database_get_db


class _EmptyOrchestrator:
    async def process_message(self, user_message: str, selected_model: str, execution_context=None):
        if False:
            yield None


class ChatEmptyResponseSmokeTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.db_path = temp_root / f"chat-empty-{uuid.uuid4().hex}.db"
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[dependency_get_db] = override_get_db
        app.dependency_overrides[database_get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        self.engine.dispose()
        if self.db_path.exists():
            os.remove(self.db_path)

    def test_chat_stream_uses_fallback_message_when_response_is_empty(self):
        with (
            patch("backend.routers.chat.get_orchestrator", return_value=_EmptyOrchestrator()),
            patch("backend.routers.chat.record_learning_if_possible", return_value=None),
        ):
            guest_response = self.client.post("/api/auth/guest")
            token = guest_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = self.client.post(
                "/api/chat",
                headers=headers,
                json={"message": "测试空响应", "model_name": "doubao"},
            )

        self.assertEqual(response.status_code, 200)
        payloads = []
        for block in response.text.strip().split("\n\n"):
            if block.startswith("data: "):
                payloads.append(json.loads(block[6:]))

        self.assertEqual(payloads[-2]["type"], "content")
        self.assertEqual(payloads[-2]["content"], "本次未生成有效回复，请重试")
        self.assertEqual(payloads[-1]["type"], "done")
        self.assertEqual(payloads[-1]["content"], "本次未生成有效回复，请重试")


if __name__ == "__main__":
    unittest.main()
