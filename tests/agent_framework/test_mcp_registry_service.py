import unittest
from pathlib import Path
import shutil
import uuid

from backend.services.mcp_registry_service import McpRegistryService


class McpRegistryServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(__file__).resolve().parents[1] / ".tmp" / f"mcp-{uuid.uuid4().hex}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.temp_dir / "mcp_servers.json"
        self.service = McpRegistryService(self.registry_path)

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_upsert_and_list_servers_persists_registry(self):
        saved = self.service.upsert_server({
            "name": "filesystem",
            "display_name": "Filesystem MCP",
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
            "capabilities": ["filesystem.read", "filesystem.write"],
            "tags": ["local", "dev"],
        })

        self.assertEqual(saved["name"], "filesystem")
        self.assertTrue(self.registry_path.exists())

        servers = self.service.list_servers()
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["status"], "enabled")
        self.assertIn("filesystem.read", servers[0]["capabilities"])

    def test_update_server_can_disable_and_merge_fields(self):
        self.service.upsert_server({
            "name": "github",
            "display_name": "GitHub MCP",
            "transport": "http",
            "url": "http://localhost:8811/mcp",
            "capabilities": ["repo.read"],
        })

        updated = self.service.update_server("github", {
            "enabled": False,
            "capabilities": ["repo.read", "pr.comment"],
        })

        self.assertFalse(updated["enabled"])
        self.assertEqual(updated["status"], "disabled")
        self.assertIn("pr.comment", updated["capabilities"])

    def test_build_capability_catalog_groups_server_names(self):
        self.service.upsert_server({
            "name": "filesystem",
            "display_name": "Filesystem MCP",
            "transport": "stdio",
            "command": "npx",
            "capabilities": ["filesystem.read", "filesystem.write"],
        })
        self.service.upsert_server({
            "name": "knowledge-base",
            "display_name": "Knowledge Base MCP",
            "transport": "http",
            "url": "http://localhost:9001/mcp",
            "capabilities": ["search.query", "filesystem.read"],
        })

        catalog = self.service.build_capability_catalog()

        self.assertEqual(catalog["total_servers"], 2)
        self.assertEqual(catalog["enabled_servers"], 2)
        capability_names = [item["capability"] for item in catalog["capabilities"]]
        self.assertIn("filesystem.read", capability_names)
        self.assertIn("search.query", capability_names)

    def test_resolve_servers_for_capability_only_returns_enabled_servers(self):
        self.service.upsert_server({
            "name": "filesystem",
            "display_name": "Filesystem MCP",
            "transport": "stdio",
            "command": "npx",
            "capabilities": ["filesystem.read"],
        })
        self.service.upsert_server({
            "name": "archived-filesystem",
            "display_name": "Archived Filesystem MCP",
            "transport": "stdio",
            "command": "npx",
            "enabled": False,
            "capabilities": ["filesystem.read"],
        })

        resolved = self.service.resolve_servers_for_capability("filesystem.read")

        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["name"], "filesystem")

    def test_stdio_requires_command_and_http_requires_url(self):
        with self.assertRaisesRegex(ValueError, "command"):
            self.service.upsert_server({
                "name": "bad-stdio",
                "display_name": "Bad Stdio",
                "transport": "stdio",
            })

        with self.assertRaisesRegex(ValueError, "url"):
            self.service.upsert_server({
                "name": "bad-http",
                "display_name": "Bad Http",
                "transport": "http",
            })


if __name__ == "__main__":
    unittest.main()
