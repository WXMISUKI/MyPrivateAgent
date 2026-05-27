import unittest
from pathlib import Path
import shutil
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.agent_server.app import create_app
from backend.agent_server.auth_provider import (
    create_anonymous_auth_provider,
    create_auth_provider,
    get_default_auth_provider,
)
from backend.agent_server.config import (
    API_ONLY_ROUTE_GROUPS,
    DEFAULT_SERVER_PRESET,
    EMBEDDED_ROUTE_GROUPS,
    KNOWLEDGE_DEMO_ROUTE_GROUPS,
    LEARNING_DEMO_ROUTE_GROUPS,
    PRESET_API_ONLY,
    PRESET_EMBEDDED,
    PRESET_FULL_STACK,
    PRESET_KNOWLEDGE_DEMO,
    PRESET_LEARNING_DEMO,
    PRESET_WEATHER_DEMO,
    AgentServerAuthConfig,
    AgentServerBootstrapConfig,
    AgentServerConfig,
    AgentServerUIConfig,
    WEATHER_DEMO_ROUTE_GROUPS,
    get_available_server_presets,
    get_server_config_for_preset,
)
from backend.agent_server.dependencies import get_current_user, get_db
from backend.agent_server.router_registry import get_api_router_registrations, get_api_routers, get_route_group_names


class AgentServerAppTests(unittest.TestCase):
    def test_router_registry_returns_expected_count(self):
        routers = tuple(get_api_routers())
        self.assertEqual(len(routers), 12)

    def test_router_registry_can_filter_by_group(self):
        registrations = get_api_router_registrations(route_groups=("admin",))
        self.assertEqual(tuple(registration.name for registration in registrations), ("memory",))

    def test_router_registry_exposes_supported_groups(self):
        self.assertEqual(
            get_route_group_names(),
            (
                "auth",
                "core",
                "skills",
                "mcp",
                "planner",
                "learning",
                "permissions",
                "admin",
                "voice",
                "capabilities",
            ),
        )

    def test_create_app_registers_core_routes(self):
        app = create_app()
        route_paths = {route.path for route in app.router.routes}
        spa_index = Path("D:/AI/AIcode/MyPrivateAgent/frontend-vue/dist/index.html")

        self.assertIn("/", route_paths)
        self.assertIn("/login", route_paths)
        self.assertIn("/api/chat", route_paths)
        self.assertIn("/api/conversations", route_paths)
        self.assertIn("/api/admin/memory/stats", route_paths)
        if spa_index.exists():
            self.assertIn("/chat", route_paths)
            self.assertIn("/index", route_paths)
        else:
            self.assertNotIn("/chat", route_paths)

    def test_create_app_allows_api_only_route_selection(self):
        app = create_app(
            AgentServerConfig(
                route_groups=("core",),
                bootstrap=AgentServerBootstrapConfig(
                    load_environment=False,
                    init_database=False,
                ),
                ui=AgentServerUIConfig(enabled=False),
            )
        )
        route_paths = {route.path for route in app.router.routes}

        self.assertIn("/api/chat", route_paths)
        self.assertIn("/api/conversations", route_paths)
        self.assertNotIn("/api/auth/login", route_paths)
        self.assertNotIn("/api/admin/memory/stats", route_paths)
        self.assertNotIn("/login", route_paths)

    def test_create_app_applies_auth_dependency_overrides(self):
        def fake_current_user():
            return {"id": "test-user"}

        app = create_app(
            AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(
                    load_environment=False,
                    init_database=False,
                ),
                ui=AgentServerUIConfig(enabled=False),
                auth=AgentServerAuthConfig(
                    current_user_dependency=fake_current_user,
                ),
            )
        )

        self.assertIs(app.dependency_overrides[get_current_user], fake_current_user)

    def test_create_app_can_serve_spa_primary_ui(self):
        dist_dir = Path("D:/AI/AIcode/MyPrivateAgent/.tmp_test_spa_dist") / uuid.uuid4().hex
        try:
            assets_dir = dist_dir / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)
            (dist_dir / "index.html").write_text("<html><body><div id='app'></div></body></html>", encoding="utf-8")

            app = create_app(
                AgentServerConfig(
                    bootstrap=AgentServerBootstrapConfig(
                        load_environment=False,
                        init_database=False,
                    ),
                    ui=AgentServerUIConfig(spa_dist_dir=dist_dir),
                )
            )
            route_paths = {route.path for route in app.router.routes}

            self.assertIn("/chat", route_paths)
            self.assertIn("/index", route_paths)
        finally:
            if dist_dir.exists():
                shutil.rmtree(dist_dir.parent, ignore_errors=True)

    def test_create_app_applies_auth_provider_dependencies(self):
        def fake_current_user():
            return {"id": "provider-user"}

        def fake_optional_user():
            return {"id": "provider-optional-user"}

        def fake_db():
            return "provider-db"

        provider = create_auth_provider(
            name="test_provider",
            current_user_dependency=fake_current_user,
            optional_user_dependency=fake_optional_user,
            database_dependency=fake_db,
        )

        app = create_app(
            AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(
                    load_environment=False,
                    init_database=False,
                ),
                ui=AgentServerUIConfig(enabled=False),
                auth=AgentServerAuthConfig(provider=provider),
            )
        )

        self.assertIs(app.dependency_overrides[get_current_user], fake_current_user)
        self.assertIs(app.dependency_overrides[get_db], fake_db)

    def test_preset_registry_exposes_supported_presets(self):
        self.assertEqual(
            get_available_server_presets(),
            (
                PRESET_FULL_STACK,
                PRESET_API_ONLY,
                PRESET_EMBEDDED,
                PRESET_LEARNING_DEMO,
                PRESET_WEATHER_DEMO,
                PRESET_KNOWLEDGE_DEMO,
            ),
        )
        self.assertEqual(DEFAULT_SERVER_PRESET, PRESET_FULL_STACK)

    def test_api_only_preset_builds_without_admin_and_ui(self):
        config = get_server_config_for_preset(PRESET_API_ONLY)
        self.assertEqual(config.route_groups, API_ONLY_ROUTE_GROUPS)
        self.assertFalse(config.ui.enabled)

        app = create_app(preset=PRESET_API_ONLY)
        route_paths = {route.path for route in app.router.routes}
        self.assertIn("/api/auth/login", route_paths)
        self.assertIn("/api/chat", route_paths)
        self.assertNotIn("/api/admin/memory/stats", route_paths)
        self.assertNotIn("/login", route_paths)

    def test_embedded_preset_disables_bootstrap_and_limits_routes(self):
        config = get_server_config_for_preset(PRESET_EMBEDDED)
        self.assertEqual(config.route_groups, EMBEDDED_ROUTE_GROUPS)
        self.assertFalse(config.bootstrap.load_environment)
        self.assertFalse(config.bootstrap.init_database)
        self.assertFalse(config.ui.enabled)

        app = create_app(preset=PRESET_EMBEDDED)
        route_paths = {route.path for route in app.router.routes}
        self.assertIn("/api/chat", route_paths)
        self.assertIn("/api/skills", route_paths)
        self.assertNotIn("/api/auth/login", route_paths)
        self.assertNotIn("/api/permissions/pending", route_paths)
        self.assertNotIn("/login", route_paths)

    def test_learning_demo_preset_focuses_on_chat_and_learning_routes(self):
        config = get_server_config_for_preset(PRESET_LEARNING_DEMO)
        self.assertEqual(config.route_groups, LEARNING_DEMO_ROUTE_GROUPS)
        self.assertFalse(config.ui.enabled)

        app = create_app(preset=PRESET_LEARNING_DEMO)
        route_paths = {route.path for route in app.router.routes}
        self.assertIn("/api/chat", route_paths)
        self.assertIn("/api/learnings", route_paths)
        self.assertIn("/api/auth/login", route_paths)
        self.assertNotIn("/api/skills", route_paths)
        self.assertNotIn("/login", route_paths)

    def test_weather_demo_preset_focuses_on_core_weather_shape(self):
        config = get_server_config_for_preset(PRESET_WEATHER_DEMO)
        self.assertEqual(config.route_groups, WEATHER_DEMO_ROUTE_GROUPS)
        self.assertTrue(config.ui.enabled)
        self.assertEqual(config.ui.mode, "spa")

        app = create_app(preset=PRESET_WEATHER_DEMO)
        route_paths = {route.path for route in app.router.routes}
        self.assertIn("/api/chat", route_paths)
        self.assertIn("/api/auth/login", route_paths)
        self.assertNotIn("/api/learnings", route_paths)
        self.assertNotIn("/api/skills", route_paths)

    def test_knowledge_demo_preset_focuses_on_learning_and_chat(self):
        config = get_server_config_for_preset(PRESET_KNOWLEDGE_DEMO)
        self.assertEqual(config.route_groups, KNOWLEDGE_DEMO_ROUTE_GROUPS)
        self.assertTrue(config.ui.enabled)
        self.assertEqual(config.ui.mode, "spa")

        app = create_app(preset=PRESET_KNOWLEDGE_DEMO)
        route_paths = {route.path for route in app.router.routes}
        self.assertIn("/api/chat", route_paths)
        self.assertIn("/api/learnings", route_paths)
        self.assertIn("/api/auth/login", route_paths)
        self.assertNotIn("/api/skills", route_paths)

    def test_default_auth_provider_keeps_current_bearer_dependencies(self):
        provider = get_default_auth_provider()
        self.assertEqual(provider.name, "default_jwt")

    def test_anonymous_auth_provider_returns_synthetic_user(self):
        provider = create_anonymous_auth_provider(user={"id": "anon-user"})
        self.assertEqual(provider.current_user_dependency(), {"id": "anon-user"})
        self.assertEqual(provider.optional_user_dependency(), {"id": "anon-user"})

    @patch("backend.routers.chat.get_runtime_surface_service")
    def test_models_endpoint_uses_runtime_surface_catalog(self, mock_surface_factory):
        mock_surface_factory.return_value.list_models.return_value = [
            {"name": "doubao", "display_name": "豆包", "provider": "volcengine-ark"}
        ]
        app = create_app(
            AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(
                    load_environment=False,
                    init_database=False,
                ),
                ui=AgentServerUIConfig(enabled=False),
            )
        )
        client = TestClient(app)

        response = client.get("/api/models")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["name"], "doubao")


if __name__ == "__main__":
    unittest.main()
