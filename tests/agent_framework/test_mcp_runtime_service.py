import unittest
from unittest.mock import AsyncMock

from backend.harness.tool_registry import ToolRegistry
from backend.services.mcp_runtime_service import McpRuntimeService


class _StubMcpRegistryService:
    def __init__(self):
        self.catalog = {
            "capabilities": [
                {"capability": "filesystem.read", "server_names": ["filesystem"]},
                {"capability": "search.query", "server_names": ["knowledge-base"]},
            ]
        }
        self.providers = {
            "filesystem.read": [
                {
                    "name": "filesystem",
                    "transport": "stdio",
                    "enabled": True,
                }
            ],
            "search.query": [
                {
                    "name": "knowledge-base",
                    "transport": "http",
                    "enabled": True,
                }
            ],
        }

    def build_capability_catalog(self):
        return self.catalog

    def get_server(self, name):
        for server_list in self.providers.values():
            for server in server_list:
                if server["name"] == name:
                    return server
        return None

    def resolve_servers_for_capability(self, capability):
        return list(self.providers.get(capability, []))


class McpRuntimeServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_sync_registry_tools_registers_capability_tools(self):
        service = McpRuntimeService()
        service.registry_service = _StubMcpRegistryService()
        registry = ToolRegistry()

        service.sync_registry_tools(registry)

        tool_names = [tool.name for tool in registry.list_all()]
        self.assertIn("mcp_filesystem_read", tool_names)
        self.assertIn("mcp_search_query", tool_names)
        self.assertEqual(registry.get_tool_spec("mcp_filesystem_read").permission_level, "ask")
        definitions = registry.get_doubao_tool_definitions()
        self.assertTrue(any(item["function"]["name"] == "mcp_search_query" for item in definitions))

    async def test_execute_capability_resolves_primary_provider(self):
        service = McpRuntimeService()
        service.registry_service = _StubMcpRegistryService()
        service.adapter_service.registry_service = service.registry_service
        service.session_service.execute_capability = AsyncMock(return_value="runtime ok")

        result = await service.execute_capability(
            "filesystem.read",
            request="读取 README.md",
            arguments={"path": "README.md"},
        )

        self.assertEqual(result, "runtime ok")

    async def test_execute_capability_falls_back_to_adapter_when_session_call_fails(self):
        service = McpRuntimeService()
        service.registry_service = _StubMcpRegistryService()
        service.session_service.execute_capability = AsyncMock(side_effect=ValueError("session failed"))
        service.adapter_service.execute = AsyncMock(return_value="adapter fallback ok")

        result = await service.execute_capability(
            "filesystem.read",
            request="读取 README.md",
            arguments={"path": "README.md"},
        )

        self.assertEqual(result, "adapter fallback ok")

    def test_validate_required_capabilities_delegates_to_adapter(self):
        service = McpRuntimeService()
        service.adapter_service.validate_capabilities = lambda capabilities: {
            "ready": False,
            "missing_capabilities": ["filesystem.read"],
            "unavailable_capabilities": [],
            "resolved_capabilities": [],
        }

        state = service.validate_required_capabilities(["filesystem.read"])

        self.assertFalse(state["ready"])
        self.assertEqual(state["missing_capabilities"], ["filesystem.read"])

    async def test_sync_registry_tools_removes_stale_capability_tools(self):
        service = McpRuntimeService()
        service.registry_service = _StubMcpRegistryService()
        registry = ToolRegistry()

        service.sync_registry_tools(registry)
        service.registry_service.catalog = {
            "capabilities": [
                {"capability": "search.query", "server_names": ["knowledge-base"]},
            ]
        }
        service.sync_registry_tools(registry)

        tool_names = [tool.name for tool in registry.list_all()]
        self.assertNotIn("mcp_filesystem_read", tool_names)
        self.assertIn("mcp_search_query", tool_names)


if __name__ == "__main__":
    unittest.main()
