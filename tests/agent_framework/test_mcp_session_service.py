import unittest

from backend.services.mcp_session_service import McpSessionService


class _StubRegistryService:
    def resolve_servers_for_capability(self, capability):
        if capability == "filesystem.read":
            return [{
                "name": "filesystem",
                "transport": "stdio",
                "metadata": {"capability_tools": {"filesystem.read": "read_file"}},
            }]
        return []

    def get_server(self, name):
        if name != "filesystem":
            return None
        return {
            "name": "filesystem",
            "transport": "stdio",
            "metadata": {
                "protocol_version": "2024-11-05",
                "capability_tools": {"filesystem.read": "read_file"},
            },
        }


class _StubAdapterService:
    def __init__(self):
        self.calls = []

    async def send_session_request(self, *, server_name, method, params=None, request_id=1):
        self.calls.append({
            "server_name": server_name,
            "method": method,
            "params": params,
            "request_id": request_id,
        })
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "filesystem-mcp", "version": "1.0.0"},
                    "capabilities": {"tools": {"listChanged": False}},
                },
            }
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {"name": "read_file", "description": "Read file"},
                        {"name": "list_dir", "description": "List directory"},
                    ]
                },
            }
        if method == "tools/call":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": "file content"}],
                    "structuredContent": {"path": "README.md"},
                    "isError": False,
                },
            }
        raise AssertionError(f"unexpected method: {method}")


class McpSessionServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_handshake_server_returns_protocol_server_info_and_tools(self):
        service = McpSessionService()
        service.registry_service = _StubRegistryService()
        service.adapter_service = _StubAdapterService()

        result = await service.handshake_server("filesystem")

        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["protocol_version"], "2024-11-05")
        self.assertEqual(result["server_info"]["name"], "filesystem-mcp")
        self.assertEqual(len(result["tools"]), 2)
        self.assertEqual(result["audit"][0]["phase"], "initialize")
        self.assertEqual(result["audit"][1]["request_method"], "tools/list")

    async def test_handshake_server_uses_cache_when_not_forced(self):
        service = McpSessionService()
        adapter = _StubAdapterService()
        service.registry_service = _StubRegistryService()
        service.adapter_service = adapter

        first = await service.handshake_server("filesystem")
        second = await service.handshake_server("filesystem")

        self.assertEqual(first["server_name"], second["server_name"])
        self.assertEqual(len(adapter.calls), 2)

    async def test_call_tool_returns_normalized_content_and_audit(self):
        service = McpSessionService()
        service.registry_service = _StubRegistryService()
        service.adapter_service = _StubAdapterService()

        result = await service.call_tool(
            server_name="filesystem",
            tool_name="read_file",
            arguments={"path": "README.md"},
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["content"], ["file content"])
        self.assertEqual(result["structured_content"]["path"], "README.md")
        self.assertEqual(result["audit"]["phase"], "tools_call")

    async def test_execute_capability_uses_mapped_tool_and_returns_text(self):
        service = McpSessionService()
        service.registry_service = _StubRegistryService()
        service.adapter_service = _StubAdapterService()

        result = await service.execute_capability(
            capability="filesystem.read",
            request="读取 README.md",
            arguments={"path": "README.md"},
        )

        self.assertEqual(result, "file content")

    async def test_handshake_server_raises_for_missing_server(self):
        service = McpSessionService()
        service.registry_service = _StubRegistryService()
        service.adapter_service = _StubAdapterService()

        with self.assertRaisesRegex(ValueError, "不存在"):
            await service.handshake_server("missing")


if __name__ == "__main__":
    unittest.main()
