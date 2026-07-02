import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.capability_runtime.contracts import CapabilityDefinition
from backend.capability_runtime.registry import CapabilityRegistry
from backend.capability_runtime.service import CapabilityRuntimeService
from backend.routers.capabilities import router as capabilities_router
from backend.routers.coze_workflows import router as coze_workflows_router


class CozeWorkflowsRouterTests(unittest.TestCase):
    def setUp(self):
        capability = CapabilityDefinition(
            capability_id="coze.workflow.demo_workflow",
            kind="workflow",
            transport="local",
            provider="coze_migration",
            title="Demo Workflow",
            description="Demo workflow for router tests",
            metadata={
                "workflow_id": "demo_workflow",
                "workflow_version": "0.1.0",
                "workflow_status": "active",
            },
            invoker=lambda payload: {
                "ok": True,
                "workflow_id": "demo_workflow",
                "capability_id": "coze.workflow.demo_workflow",
                "workflow_version": "0.1.0",
                "run_id": "run-demo-1",
                "status": "completed",
                "result": {"echo": payload},
                "authorization": {"status": "not_evaluated"},
                "invocation_policy": {"placeholder": True},
                "trace_summary": {
                    "workflow_id": "demo_workflow",
                    "workflow_version": "0.1.0",
                    "source": "coze_migration",
                },
                "trace": {
                    "workflow_id": "demo_workflow",
                    "workflow_version": "0.1.0",
                    "source": "coze_migration",
                },
            },
        )
        self.runtime_service = CapabilityRuntimeService(CapabilityRegistry([capability]))
        self.workflow_record = {
            "id": "demo_workflow",
            "name": "Demo Workflow",
            "version": "0.1.0",
            "status": "active",
            "capability_id": "coze.workflow.demo_workflow",
            "invocation_policy": {"placeholder": True},
        }
        self.registry_service = unittest.mock.Mock()
        self.registry_service.get_workflow_by_id.side_effect = (
            lambda workflow_id: self.workflow_record if workflow_id == "demo_workflow" else None
        )

        self.runtime_patcher = patch(
            "backend.routers.coze_workflows.get_capability_runtime_service",
            return_value=self.runtime_service,
        )
        self.capabilities_runtime_patcher = patch(
            "backend.routers.capabilities.get_capability_runtime_service",
            return_value=self.runtime_service,
        )
        self.registry_patcher = patch(
            "backend.routers.coze_workflows.get_coze_workflow_registry_service",
            return_value=self.registry_service,
        )
        self.runtime_patcher.start()
        self.capabilities_runtime_patcher.start()
        self.registry_patcher.start()
        self.addCleanup(self.runtime_patcher.stop)
        self.addCleanup(self.capabilities_runtime_patcher.stop)
        self.addCleanup(self.registry_patcher.stop)

        app = FastAPI()
        app.include_router(coze_workflows_router)
        app.include_router(capabilities_router)
        self.client = TestClient(app)

    def test_workflow_route_reuses_capability_runtime_envelope(self):
        payload = {"input": "hello"}

        workflow_response = self.client.post("/api/coze-workflows/demo_workflow/invoke", json=payload)
        capability_response = self.client.post("/api/capabilities/coze.workflow.demo_workflow/invoke", json=payload)

        self.assertEqual(workflow_response.status_code, 200)
        self.assertEqual(capability_response.status_code, 200)

        workflow_body = workflow_response.json()
        capability_body = capability_response.json()

        self.assertEqual(workflow_body["workflow_id"], capability_body["workflow_id"])
        self.assertEqual(workflow_body["capability_id"], capability_body["capability_id"])
        self.assertEqual(workflow_body["workflow_version"], capability_body["workflow_version"])
        self.assertEqual(workflow_body["status"], capability_body["status"])
        self.assertEqual(workflow_body["authorization"], capability_body["authorization"])
        self.assertEqual(workflow_body["invocation_policy"], capability_body["invocation_policy"])
        self.assertEqual(workflow_body["trace_summary"], capability_body["trace_summary"])
        self.assertEqual(workflow_body["result"], capability_body["result"])

    def test_unknown_workflow_returns_workflow_scoped_404(self):
        response = self.client.post("/api/coze-workflows/unknown_workflow/invoke", json={})

        self.assertEqual(response.status_code, 404)
        self.assertIn("Coze workflow not found: unknown_workflow", response.text)

    def test_workflow_route_preserves_capability_runtime_failure_envelope(self):
        blocked_capability = CapabilityDefinition(
            capability_id="coze.workflow.blocked_workflow",
            kind="workflow",
            transport="local",
            provider="coze_migration",
            title="Blocked Workflow",
            description="Blocked workflow for router tests",
            invoker=lambda _payload: {
                "ok": False,
                "workflow_id": "blocked_workflow",
                "capability_id": "coze.workflow.blocked_workflow",
                "workflow_version": "0.2.0",
                "run_id": None,
                "status": "review",
                "error": {
                    "code": "COZE_WORKFLOW_BLOCKED",
                    "message": "Workflow is not ready for invocation.",
                    "blockers": [],
                    "details": {"reason": "Workflow is under review"},
                },
                "authorization": {"status": "not_evaluated"},
                "invocation_policy": {"placeholder": True},
                "trace_summary": {
                    "workflow_id": "blocked_workflow",
                    "workflow_version": "0.2.0",
                    "source": "coze_migration",
                },
                "trace": {
                    "workflow_id": "blocked_workflow",
                    "workflow_version": "0.2.0",
                    "source": "coze_migration",
                },
            },
        )
        runtime_service = CapabilityRuntimeService(CapabilityRegistry([blocked_capability]))
        workflow_record = {
            "id": "blocked_workflow",
            "name": "Blocked Workflow",
            "version": "0.2.0",
            "status": "review",
            "capability_id": "coze.workflow.blocked_workflow",
            "invocation_policy": {"placeholder": True},
        }
        self.registry_service.get_workflow_by_id.side_effect = (
            lambda workflow_id: workflow_record if workflow_id == "blocked_workflow" else None
        )

        with patch(
            "backend.routers.coze_workflows.get_capability_runtime_service",
            return_value=runtime_service,
        ):
            response = self.client.post("/api/coze-workflows/blocked_workflow/invoke", json={"input": "x"})

        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["capability_id"], "coze.workflow.blocked_workflow")
        self.assertEqual(payload["workflow_version"], "0.2.0")
        self.assertEqual(payload["error"]["code"], "COZE_WORKFLOW_BLOCKED")
        self.assertEqual(payload["authorization"]["status"], "not_evaluated")


if __name__ == "__main__":
    unittest.main()
