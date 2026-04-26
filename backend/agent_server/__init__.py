"""Reusable server-layer entrypoints for the backend application.

Keep this module light to avoid package-import side effects and circular imports.
"""

from .auth_provider import (
    AgentServerAuthProvider,
    create_anonymous_auth_provider,
    create_auth_provider,
    get_default_auth_provider,
)
from .bootstrap import init_database, load_environment
from .config import (
    API_ONLY_ROUTE_GROUPS,
    DEFAULT_ROUTE_GROUPS,
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
    AgentServerPreset,
    AgentServerAuthConfig,
    AgentServerBootstrapConfig,
    AgentServerConfig,
    AgentServerUiMode,
    AgentServerUIConfig,
    WEATHER_DEMO_ROUTE_GROUPS,
    get_available_server_presets,
    get_server_config_for_preset,
)
from .dependencies import get_current_user, get_current_user_optional, get_db, oauth2_scheme
from .http import (
    build_error_event,
    build_sse_event,
    ensure_exists,
    permission_request_to_dict,
    success_response,
)


def create_app(*args, **kwargs):
    """Lazy import to avoid router package cycles during dependency import."""
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)


def get_api_router_registrations(*args, **kwargs):
    """Lazy import helper for router registry access."""
    from .router_registry import get_api_router_registrations as _get_api_router_registrations

    return _get_api_router_registrations(*args, **kwargs)


def get_api_routers(*args, **kwargs):
    """Lazy import helper for router registry access."""
    from .router_registry import get_api_routers as _get_api_routers

    return _get_api_routers(*args, **kwargs)


def get_route_group_names(*args, **kwargs):
    """Lazy import helper for router registry access."""
    from .router_registry import get_route_group_names as _get_route_group_names

    return _get_route_group_names(*args, **kwargs)

__all__ = [
    "AgentServerAuthConfig",
    "AgentServerAuthProvider",
    "AgentServerBootstrapConfig",
    "AgentServerConfig",
    "AgentServerPreset",
    "AgentServerUiMode",
    "AgentServerUIConfig",
    "API_ONLY_ROUTE_GROUPS",
    "DEFAULT_ROUTE_GROUPS",
    "DEFAULT_SERVER_PRESET",
    "EMBEDDED_ROUTE_GROUPS",
    "KNOWLEDGE_DEMO_ROUTE_GROUPS",
    "LEARNING_DEMO_ROUTE_GROUPS",
    "PRESET_API_ONLY",
    "PRESET_EMBEDDED",
    "PRESET_FULL_STACK",
    "PRESET_KNOWLEDGE_DEMO",
    "PRESET_LEARNING_DEMO",
    "PRESET_WEATHER_DEMO",
    "create_anonymous_auth_provider",
    "create_app",
    "create_auth_provider",
    "build_error_event",
    "build_sse_event",
    "ensure_exists",
    "get_available_server_presets",
    "get_api_router_registrations",
    "get_api_routers",
    "get_current_user",
    "get_current_user_optional",
    "get_default_auth_provider",
    "get_db",
    "get_route_group_names",
    "get_server_config_for_preset",
    "init_database",
    "load_environment",
    "oauth2_scheme",
    "permission_request_to_dict",
    "success_response",
    "WEATHER_DEMO_ROUTE_GROUPS",
]
