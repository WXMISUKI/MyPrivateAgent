import os
import uuid
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
from backend.agent_server.dependencies import get_db as dependency_get_db
from backend.database import Base, get_db as database_get_db


class AuthConversationSmokeTests(unittest.TestCase):
    def setUp(self):
        temp_root = Path(__file__).resolve().parent / ".tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.db_path = temp_root / f"smoke-{uuid.uuid4().hex}.db"
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

    def test_guest_auth_and_conversation_flow(self):
        guest_response = self.client.post("/api/auth/guest")
        self.assertEqual(guest_response.status_code, 200)
        token = guest_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me_response = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["username"], "guest")

        create_response = self.client.post(
            "/api/conversations",
            headers=headers,
            json={"title": "Smoke Conversation", "model_name": "doubao"},
        )
        self.assertEqual(create_response.status_code, 200)
        conversation_id = create_response.json()["id"]

        list_response = self.client.get("/api/conversations", headers=headers)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        detail_response = self.client.get(f"/api/conversations/{conversation_id}", headers=headers)
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["title"], "Smoke Conversation")


if __name__ == "__main__":
    unittest.main()
