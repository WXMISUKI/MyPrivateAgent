import unittest
from unittest.mock import patch

from backend.agent_framework.tools import ToolSpec
from backend.harness.tool_registry import BaseTool, PermissionLevel, ToolRegistry
from backend.services.capability_profile_service import CapabilityProfileService


class CapabilityProfileServiceTests(unittest.TestCase):
    @patch("backend.services.capability_profile_service.get_mcp_registry_service")
    def test_build_profile_includes_tools_mcp_and_boundaries(self, mock_registry_factory):
        mock_registry_factory.return_value.build_capability_catalog.return_value = {
            "capabilities": [{"capability": "weather_lookup", "server_names": ["demo-weather"]}]
        }
        service = CapabilityProfileService()
        tool_registry = ToolRegistry()
        tool_registry.register(
            BaseTool(
                name="search",
                description="搜索天气和基础知识",
                func=lambda **_: "ok",
                permission_level=PermissionLevel.AUTO,
            )
        )
        tool_registry.register_tool_spec(
            ToolSpec(
                name="search",
                description="搜索天气和基础知识",
                permission_level="auto",
                tags=("search", "weather", "knowledge"),
            )
        )

        profile = service.build_profile(tool_registry=tool_registry)

        self.assertIn("用户意图识别与多步执行协调", profile.available_capabilities)
        self.assertIn("weather_lookup", profile.enabled_mcp_capabilities)
        self.assertTrue(profile.tool_summaries)
        self.assertIn("你是 MyPrivateAgent 通用智能体框架中的主协调智能体", profile.system_prompt)
        self.assertIn("当前注册工具", profile.system_prompt)
        self.assertIn("交通路线检索", profile.system_prompt)


if __name__ == "__main__":
    unittest.main()
