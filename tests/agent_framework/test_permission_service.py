import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.harness.permission_service import PermissionService
from backend.models import Conversation, PlanHandoffStatus, PlanItemRecord, PlanRunRecord, PlanStatus, User


class PermissionServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()
        user = User(username="tester", password_hash="hashed")
        self.db.add(user)
        self.db.flush()
        conversation = Conversation(user_id=user.id, title="权限测试", model_name="doubao")
        self.db.add(conversation)
        self.db.flush()
        plan = PlanRunRecord(
            user_id=user.id,
            conversation_id=conversation.id,
            objective="验证权限 runtime scope",
            source="manual",
            status=PlanStatus.IN_PROGRESS,
            summary="执行中",
            plan_metadata={},
        )
        self.db.add(plan)
        self.db.flush()
        item = PlanItemRecord(
            plan_id=plan.id,
            step_order=1,
            title="写入文件",
            details="需要权限批准",
            status=PlanStatus.IN_PROGRESS,
            owner="backend",
            agent_role="backend",
            agent_id="backend-agent-p1-i1",
            handoff_status=PlanHandoffStatus.EXECUTING,
            item_metadata={},
        )
        self.db.add(item)
        self.db.commit()

        self.user = user
        self.conversation = conversation
        self.plan = plan
        self.item = item
        self.TestingSessionLocal = TestingSessionLocal

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_create_request_persists_runtime_scope(self):
        service = PermissionService()
        service._get_session_factory = lambda: self.TestingSessionLocal

        request = service.create_request(
            tool_name="filesystem.write",
            tool_args={"path": "README.md"},
            permission_level="ask",
            user_id=self.user.id,
            conversation_id=self.conversation.id,
            runtime_scope={
                "plan_id": self.plan.id,
                "plan_item_id": self.item.id,
                "run_id": "child-run-001",
                "parent_run_id": "sched-run-001",
                "child_run_id": "child-run-001",
                "scheduler_run_id": "sched-run-001",
                "run_kind": "child",
            },
            request_metadata={
                "model_name": "doubao",
                "tool_call_id": "call-001",
                "iteration": 2,
            },
        )

        service._pending_requests.pop(request.id, None)
        reloaded = service.get_request(request.id)

        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.plan_id, self.plan.id)
        self.assertEqual(reloaded.plan_item_id, self.item.id)
        self.assertEqual(reloaded.run_id, "child-run-001")
        self.assertEqual(reloaded.scheduler_run_id, "sched-run-001")
        self.assertEqual(reloaded.run_kind, "child")
        self.assertEqual(reloaded.request_metadata["tool_call_id"], "call-001")


if __name__ == "__main__":
    unittest.main()
