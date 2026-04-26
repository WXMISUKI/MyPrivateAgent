import unittest

from backend.agent_server import (
    API_ONLY_ROUTE_GROUPS,
    DEFAULT_ROUTE_GROUPS,
    DEFAULT_SERVER_PRESET,
    EMBEDDED_ROUTE_GROUPS,
    PRESET_API_ONLY,
    PRESET_EMBEDDED,
    PRESET_FULL_STACK,
    AgentServerAuthConfig,
    AgentServerAuthProvider,
    AgentServerBootstrapConfig,
    AgentServerConfig,
    AgentServerPreset,
    AgentServerUIConfig,
    build_error_event,
    build_sse_event,
    create_anonymous_auth_provider,
    ensure_exists,
    get_available_server_presets,
    get_api_router_registrations,
    get_current_user,
    get_current_user_optional,
    get_db,
    get_default_auth_provider,
    get_route_group_names,
    get_server_config_for_preset,
    oauth2_scheme,
    permission_request_to_dict,
    success_response,
    create_auth_provider,
)
from backend.agent_server.auth_provider import (
    AgentServerAuthProvider as auth_provider_class,
    create_anonymous_auth_provider as auth_provider_create_anonymous,
    create_auth_provider as auth_provider_create,
    get_default_auth_provider as auth_provider_get_default,
)
from backend.agent_server.config import (
    API_ONLY_ROUTE_GROUPS as config_api_only_route_groups,
    DEFAULT_ROUTE_GROUPS as config_default_route_groups,
    DEFAULT_SERVER_PRESET as config_default_server_preset,
    EMBEDDED_ROUTE_GROUPS as config_embedded_route_groups,
    PRESET_API_ONLY as config_preset_api_only,
    PRESET_EMBEDDED as config_preset_embedded,
    PRESET_FULL_STACK as config_preset_full_stack,
    AgentServerPreset as config_server_preset,
    AgentServerAuthConfig as config_auth_config,
    AgentServerBootstrapConfig as config_bootstrap_config,
    AgentServerConfig as config_server_config,
    AgentServerUIConfig as config_ui_config,
    get_available_server_presets as config_get_available_server_presets,
    get_server_config_for_preset as config_get_server_config_for_preset,
)
from backend.agent_server.dependencies import (
    get_current_user as dependencies_get_current_user,
    get_current_user_optional as dependencies_get_current_user_optional,
    get_db as dependencies_get_db,
    oauth2_scheme as dependencies_oauth2_scheme,
)
from backend.agent_server.http import (
    build_error_event as http_build_error_event,
    build_sse_event as http_build_sse_event,
    ensure_exists as http_ensure_exists,
    permission_request_to_dict as http_permission_request_to_dict,
    success_response as http_success_response,
)
from backend.agent_server.router_registry import (
    get_api_router_registrations as registry_get_api_router_registrations,
    get_route_group_names as registry_get_route_group_names,
)


class AgentServerDependencyTests(unittest.TestCase):
    def test_public_dependency_exports_match_dependency_module(self):
        self.assertIs(get_db, dependencies_get_db)
        self.assertIs(get_current_user, dependencies_get_current_user)
        self.assertIs(get_current_user_optional, dependencies_get_current_user_optional)
        self.assertIs(oauth2_scheme, dependencies_oauth2_scheme)

    def test_public_http_exports_match_http_module(self):
        self.assertIs(build_sse_event, http_build_sse_event)
        self.assertIs(build_error_event, http_build_error_event)
        self.assertIs(ensure_exists, http_ensure_exists)
        self.assertIs(success_response, http_success_response)
        self.assertIs(permission_request_to_dict, http_permission_request_to_dict)

    def test_public_config_exports_match_config_module(self):
        self.assertIs(AgentServerConfig, config_server_config)
        self.assertIs(AgentServerAuthConfig, config_auth_config)
        self.assertIs(AgentServerAuthProvider, auth_provider_class)
        self.assertIs(AgentServerBootstrapConfig, config_bootstrap_config)
        self.assertIs(AgentServerUIConfig, config_ui_config)
        self.assertIs(AgentServerPreset, config_server_preset)
        self.assertEqual(DEFAULT_ROUTE_GROUPS, config_default_route_groups)
        self.assertEqual(API_ONLY_ROUTE_GROUPS, config_api_only_route_groups)
        self.assertEqual(EMBEDDED_ROUTE_GROUPS, config_embedded_route_groups)
        self.assertEqual(DEFAULT_SERVER_PRESET, config_default_server_preset)
        self.assertEqual(PRESET_FULL_STACK, config_preset_full_stack)
        self.assertEqual(PRESET_API_ONLY, config_preset_api_only)
        self.assertEqual(PRESET_EMBEDDED, config_preset_embedded)
        self.assertIs(get_available_server_presets, config_get_available_server_presets)
        self.assertIs(get_server_config_for_preset, config_get_server_config_for_preset)
        self.assertIs(create_auth_provider, auth_provider_create)
        self.assertIs(create_anonymous_auth_provider, auth_provider_create_anonymous)
        self.assertIs(get_default_auth_provider, auth_provider_get_default)

    def test_public_router_registry_exports_match_registry_module(self):
        public_names = [item.name for item in get_api_router_registrations()]
        registry_names = [item.name for item in registry_get_api_router_registrations()]
        self.assertEqual(public_names, registry_names)
        self.assertEqual(
            set(get_route_group_names()),
            set(registry_get_route_group_names()),
        )


if __name__ == "__main__":
    unittest.main()
