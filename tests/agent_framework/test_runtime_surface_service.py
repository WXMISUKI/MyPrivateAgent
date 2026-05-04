import unittest
from unittest.mock import patch

from backend.services.runtime_surface_service import RuntimeSurfaceService


class RuntimeSurfaceServiceTests(unittest.TestCase):
    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    def test_runtime_profile_includes_models_and_providers(self, mock_hook_factory, mock_subagent_factory, mock_memory_factory, mock_capability_factory, mock_config_factory, mock_router_factory):
        mock_router = mock_router_factory.return_value
        mock_config_factory.return_value.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": ["volcengine-ark"],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config_factory.return_value.get_config_layers.return_value = {
            "defaults": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": [], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "overrides": {"enabled_providers": ["volcengine-ark"]},
            "effective": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": ["volcengine-ark"], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "override_path": ".myagent/runtime_surface.json",
            "editable_keys": ["auth_mode", "default_model", "enabled_providers", "failover_thresholds"],
        }
        mock_capability_factory.return_value.build_runtime_contract.return_value = {
            "identity_summary": "主协调智能体",
            "operating_principles": ["规则1"],
            "available_capabilities": ["天气查询"],
            "limited_capabilities": ["交通路线检索"],
            "enabled_mcp_capabilities": [],
            "registered_tools": [],
        }
        mock_memory_factory.return_value.build_runtime_contract.return_value = {
            "loaded_layers": [{"name": "global", "path": "GLOBAL_AGENT.md"}],
            "missing_layers": [{"name": "local", "path": "PROJECT_AGENT.local.md"}],
            "layer_order": ["global", "project", "local", "org_policy"],
            "active": True,
        }
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {
            "total_profiles": 1,
            "profiles": [{"name": "planner"}],
        }
        mock_hook_factory.return_value.build_runtime_contract.return_value = {
            "enabled_hooks": ["pre_tool_use", "post_tool_use"],
            "governance_model": "minimal",
        }
        mock_router.list_available_models.return_value = {
            "doubao": {
                "name": "doubao",
                "display_name": "豆包",
                "provider": "volcengine-ark",
                "provider_label": "火山引擎 Ark",
                "type": "cloud",
                "configured": True,
                "available": True,
                "is_default": True,
                "base_url": "https://ark.example.com",
                "actual_model": "doubao-seed-2-0-mini-260215",
                "source": "env",
            },
            "llama3.1": {
                "name": "llama3.1",
                "display_name": "Llama 3.1",
                "provider": "ollama",
                "provider_label": "Ollama",
                "type": "local",
                "configured": False,
                "available": False,
                "is_default": False,
                "base_url": "http://localhost:11434",
                "source": "builtin",
            },
        }

        service = RuntimeSurfaceService()
        profile = service.get_runtime_profile()

        self.assertEqual(profile["agent_mode"], "general_demo")
        self.assertEqual(len(profile["models"]), 1)
        self.assertEqual({item["provider_id"] for item in profile["providers"]}, {"volcengine-ark", "ollama"})
        self.assertEqual(profile["providers"][0]["models"], ["doubao"])
        self.assertEqual(profile["capability_contract"]["identity_summary"], "主协调智能体")
        self.assertEqual(profile["config_layers"]["editable_keys"], ["auth_mode", "default_model", "enabled_providers", "failover_thresholds"])
        self.assertEqual(profile["failover_thresholds"]["medium"], 0.2)
        self.assertEqual(profile["failover_thresholds"]["high"], 0.4)
        self.assertIn("configured_model_count", profile["providers"][0])
        self.assertEqual(profile["config_layers"]["provider_resolution"]["enabled_provider_ids"], ["volcengine-ark"])
        self.assertEqual(profile["providers"][1]["enabled"], False)
        self.assertEqual(profile["providers"][0]["model_sources"], ["env"])
        self.assertEqual(profile["providers"][0]["actual_models"], ["doubao-seed-2-0-mini-260215"])
        self.assertIn("business_auth_description", profile["auth_mode_contract"])
        self.assertTrue(profile["memory_contract"]["active"])
        self.assertEqual(profile["memory_contract"]["loaded_layers"][0]["name"], "global")
        self.assertEqual(profile["subagent_contract"]["total_profiles"], 1)
        self.assertIn("pre_tool_use", profile["hook_contract"]["enabled_hooks"])
        self.assertIn("command_contract", profile)
        self.assertGreaterEqual(profile["command_contract"]["total_commands"], 10)

    @patch("backend.services.runtime_surface_service.get_model_router")
    @patch("backend.services.runtime_surface_service.get_runtime_surface_config_service")
    @patch("backend.services.runtime_surface_service.get_capability_profile_service")
    @patch("backend.services.runtime_surface_service.get_agent_memory_service")
    @patch("backend.services.runtime_surface_service.get_subagent_runtime_service")
    @patch("backend.services.runtime_surface_service.get_agent_hook_service")
    def test_update_runtime_profile_validates_default_model(self, mock_hook_factory, mock_subagent_factory, mock_memory_factory, mock_capability_factory, mock_config_factory, mock_router_factory):
        mock_router = mock_router_factory.return_value
        mock_config = mock_config_factory.return_value
        mock_capability_factory.return_value.build_runtime_contract.return_value = {}
        mock_memory_factory.return_value.build_runtime_contract.return_value = {
            "loaded_layers": [],
            "missing_layers": [],
            "layer_order": [],
            "active": False,
        }
        mock_subagent_factory.return_value.build_runtime_contract.return_value = {
            "total_profiles": 0,
            "profiles": [],
        }
        mock_hook_factory.return_value.build_runtime_contract.return_value = {
            "enabled_hooks": [],
            "governance_model": "minimal",
        }
        mock_config.get_effective_config.return_value = {
            "auth_mode": "demo_guest",
            "default_model": "doubao",
            "enabled_providers": [],
            "failover_thresholds": {"medium": 0.2, "high": 0.4},
        }
        mock_config.get_config_layers.return_value = {
            "defaults": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": [], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "overrides": {},
            "effective": {"auth_mode": "demo_guest", "default_model": "doubao", "enabled_providers": [], "failover_thresholds": {"medium": 0.2, "high": 0.4}},
            "override_path": ".myagent/runtime_surface.json",
            "editable_keys": ["auth_mode", "default_model", "enabled_providers", "failover_thresholds"],
        }
        mock_router.list_available_models.return_value = {
            "doubao": {
                "name": "doubao",
                "display_name": "豆包",
                "provider": "volcengine-ark",
                "provider_label": "火山引擎 Ark",
                "type": "cloud",
                "configured": True,
                "available": True,
                "is_default": True,
            },
            "llama3.1": {
                "name": "llama3.1",
                "display_name": "Llama 3.1",
                "provider": "ollama",
                "provider_label": "Ollama",
                "type": "local",
                "configured": True,
                "available": True,
                "is_default": False,
            },
        }

        service = RuntimeSurfaceService()
        with self.assertRaises(ValueError):
            service.update_runtime_profile({"default_model": "not-found"})

        with self.assertRaises(ValueError):
            service.update_runtime_profile({"enabled_providers": ["ollama"]})

        with self.assertRaises(ValueError):
            service.update_runtime_profile({"enabled_providers": ["unknown-provider"]})

        service.update_runtime_profile({"default_model": "doubao"})
        mock_config.update_overrides.assert_called_once_with({"default_model": "doubao"})


if __name__ == "__main__":
    unittest.main()
