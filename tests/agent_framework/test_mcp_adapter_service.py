import unittest
from unittest.mock import AsyncMock, patch

from backend.services.mcp_adapter_service import McpAdapterService


class _StubMcpRegistryService:
    def __init__(self):
        self.servers = {
            "filesystem": {
                "name": "filesystem",
                "transport": "stdio",
                "command": "cmd",
                "args": ["/c", "echo", "hello"],
                "enabled": True,
                "capabilities": ["filesystem.read"],
            },
            "knowledge-base": {
                "name": "knowledge-base",
                "transport": "http",
                "url": "http://localhost:9001/mcp",
                "enabled": True,
                "capabilities": ["search.query"],
            },
        }

    def get_server(self, name):
        return self.servers.get(name)

    def resolve_servers_for_capability(self, capability):
        return [server for server in self.servers.values() if capability in server.get("capabilities", []) and server.get("enabled")]


class McpAdapterServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_execute_stdio_dispatches_and_returns_content(self):
        service = McpAdapterService()
        service.registry_service = _StubMcpRegistryService()
        fake_process = AsyncMock()
        fake_process.communicate = AsyncMock(return_value=(b'{"content":"stdio ok"}', b""))
        fake_process.returncode = 0

        with patch("backend.services.mcp_adapter_service.asyncio.create_subprocess_exec", return_value=fake_process):
            result = await service.execute(
                capability="filesystem.read",
                request="读取 README.md",
                arguments={"path": "README.md"},
            )

        self.assertEqual(result, "stdio ok")

    async def test_execute_http_dispatches_and_returns_result(self):
        service = McpAdapterService()
        service.registry_service = _StubMcpRegistryService()

        with patch.object(service, "_perform_http_request", return_value='{"result":"http ok"}'):
            result = await service.execute(
                capability="search.query",
                request="搜索最佳实践",
                arguments={"keyword": "planner"},
            )

        self.assertEqual(result, "http ok")

    async def test_send_session_request_returns_json_rpc_response(self):
        service = McpAdapterService()
        service.registry_service = _StubMcpRegistryService()

        with patch.object(service, "_dispatch_stdio_payload", return_value='{"jsonrpc":"2.0","id":1,"result":{"ok":true}}'):
            result = await service.send_session_request(
                server_name="filesystem",
                method="initialize",
                params={"protocolVersion": "2024-11-05"},
                request_id=1,
            )

        self.assertEqual(result["result"]["ok"], True)

    def test_validate_capabilities_reports_missing_and_unavailable(self):
        service = McpAdapterService()
        service.registry_service = _StubMcpRegistryService()

        with patch.object(service, "probe_server", side_effect=lambda server_name: {
            "server_name": server_name,
            "status": "missing_command" if server_name == "filesystem" else "ready",
        }):
            state = service.validate_capabilities([
                "filesystem.read",
                "search.query",
                "workspace.write",
            ])

        self.assertFalse(state["ready"])
        self.assertEqual(state["missing_capabilities"], ["workspace.write"])
        self.assertEqual(state["unavailable_capabilities"], ["filesystem.read"])
        self.assertEqual(state["resolved_capabilities"][0]["capability"], "search.query")

    def test_probe_stdio_server_returns_ready_or_missing(self):
        service = McpAdapterService()
        service.registry_service = _StubMcpRegistryService()

        probe = service.probe_server("filesystem")

        self.assertEqual(probe["transport"], "stdio")
        self.assertIn(probe["status"], {"ready", "missing_command"})

    def test_probe_http_server_returns_ready(self):
        service = McpAdapterService()
        service.registry_service = _StubMcpRegistryService()

        probe = service.probe_server("knowledge-base")

        self.assertEqual(probe["transport"], "http")
        self.assertEqual(probe["status"], "ready")


if __name__ == "__main__":
    unittest.main()
