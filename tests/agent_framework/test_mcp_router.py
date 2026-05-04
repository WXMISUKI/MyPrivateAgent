import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.agent_server.app import create_app
from backend.agent_server.config import (
    AgentServerAuthConfig,
    AgentServerBootstrapConfig,
    AgentServerConfig,
    AgentServerUIConfig,
)
from backend.schemas import McpProbeResponse, McpServerResponse


class _StubRunTraceService:
    trace_calls = []
    audit_calls = []

    def append_latest_active_item_trace(self, **kwargs):
        self.__class__.trace_calls.append(kwargs)
        return True

    def append_latest_active_item_audit(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return True

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "MCP-REF-321",
            "generated_at": "2026-05-02T00:00:00Z",
            **kwargs,
        }


class _StubRegistryService:
    def upsert_server(self, _payload):
        return McpServerResponse(
            name="filesystem",
            display_name="Filesystem MCP",
            transport="stdio",
            command="python",
            args=["server.py"],
            url=None,
            enabled=True,
            description="filesystem access",
            capabilities=["filesystem.read"],
            tags=[],
            metadata={},
            status="ready",
        )


class _StubAdapterService:
    def probe_server(self, server_name):
        return McpProbeResponse(
            server_name=server_name,
            transport="stdio",
            status="ok",
            detail="probe ok",
            command="python",
            resolved_command="python",
            args=["server.py"],
            url=None,
        )


class McpRouterTests(unittest.TestCase):
    def setUp(self):
        _StubRunTraceService.trace_calls = []
        _StubRunTraceService.audit_calls = []

    def _build_app(self):
        return create_app(
            config=AgentServerConfig(
                route_names=("mcp",),
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
                auth=AgentServerAuthConfig(
                    current_user_dependency=lambda: SimpleNamespace(id=1, username="tester"),
                    database_dependency=lambda: object(),
                ),
            )
        )

    @patch("backend.routers.mcp.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.mcp.get_mcp_registry_service", return_value=_StubRegistryService())
    def test_create_server_records_governance_timeline(self, _mock_registry_service, _mock_trace_service):
        client = TestClient(self._build_app())

        response = client.post(
            "/api/mcp/servers?conversation_id=321",
            json={
                "name": "filesystem",
                "display_name": "Filesystem MCP",
                "transport": "stdio",
                "command": "python",
                "args": ["server.py"],
                "enabled": True,
                "description": "filesystem access",
                "capabilities": ["filesystem.read"],
                "tags": [],
                "metadata": {},
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "filesystem")
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "mcp_server_created")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["conversation_id"], 321)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["payload"]["snapshot_ref"]["snapshot_id"], "MCP-REF-321")
        self.assertEqual(len(_StubRunTraceService.audit_calls), 1)
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "mcp_server_created")
        self.assertEqual(_StubRunTraceService.audit_calls[0]["payload"]["snapshot_ref"]["snapshot_id"], "MCP-REF-321")

    @patch("backend.routers.mcp.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.routers.mcp.get_mcp_adapter_service", return_value=_StubAdapterService())
    def test_probe_server_records_governance_timeline(self, _mock_adapter_service, _mock_trace_service):
        client = TestClient(self._build_app())

        response = client.post("/api/mcp/servers/filesystem/probe?conversation_id=321")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "mcp_server_probed")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["source"], "mcp")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["payload"]["snapshot_ref"]["snapshot_id"], "MCP-REF-321")
        self.assertEqual(len(_StubRunTraceService.audit_calls), 1)
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "mcp_server_probed")


if __name__ == "__main__":
    unittest.main()
