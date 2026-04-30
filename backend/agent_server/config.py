"""Configuration objects for assembling reusable FastAPI server apps."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, Mapping

from .auth_provider import AgentServerAuthProvider, get_default_auth_provider


DependencyCallable = Callable[..., Any]
AgentServerPreset = Literal["full_stack", "api_only", "embedded", "learning_demo", "weather_demo", "knowledge_demo"]
AgentServerUiMode = Literal["spa", "disabled"]

try:
    from config import PROJECT_ROOT
except ModuleNotFoundError:
    from backend.config import PROJECT_ROOT
DEFAULT_ROUTE_GROUPS = (
    "auth",
    "core",
    "skills",
    "mcp",
    "learning",
    "permissions",
    "admin",
)
API_ONLY_ROUTE_GROUPS = (
    "auth",
    "core",
    "skills",
    "mcp",
    "learning",
    "permissions",
)
EMBEDDED_ROUTE_GROUPS = ("core", "skills")
LEARNING_DEMO_ROUTE_GROUPS = (
    "auth",
    "core",
    "learning",
    "permissions",
)
WEATHER_DEMO_ROUTE_GROUPS = (
    "auth",
    "core",
    "permissions",
)
KNOWLEDGE_DEMO_ROUTE_GROUPS = (
    "auth",
    "core",
    "learning",
    "permissions",
)
PRESET_FULL_STACK = "full_stack"
PRESET_API_ONLY = "api_only"
PRESET_EMBEDDED = "embedded"
PRESET_LEARNING_DEMO = "learning_demo"
PRESET_WEATHER_DEMO = "weather_demo"
PRESET_KNOWLEDGE_DEMO = "knowledge_demo"
DEFAULT_SERVER_PRESET: AgentServerPreset = PRESET_FULL_STACK


def _load_cors_settings() -> dict[str, object]:
    """Load shared CORS settings from environment-backed backend config."""
    try:
        from config import CORS_ALLOWED_ORIGINS, CORS_ALLOWED_ORIGIN_REGEX
    except ModuleNotFoundError:
        from backend.config import CORS_ALLOWED_ORIGINS, CORS_ALLOWED_ORIGIN_REGEX
    return {
        "cors_allow_origins": tuple(CORS_ALLOWED_ORIGINS),
        "cors_allow_origin_regex": CORS_ALLOWED_ORIGIN_REGEX,
        "cors_allow_credentials": True,
    }


@dataclass(frozen=True)
class AgentServerBootstrapConfig:
    """Startup bootstrap toggles for reusable deployments."""

    load_environment: bool = True
    init_database: bool = True


@dataclass(frozen=True)
class AgentServerUIConfig:
    """Vue SPA mounting configuration."""

    enabled: bool = True
    mode: AgentServerUiMode = "spa"
    spa_dist_dir: Path = PROJECT_ROOT / "frontend-vue" / "dist"
    spa_assets_mount_path: str = "/assets"
    spa_route_paths: tuple[str, ...] = (
        "/",
        "/login",
        "/chat",
        "/learnings",
        "/skills",
        "/settings",
        "/search",
        "/feedback-analytics",
    )
    index_route_path: str = "/index"


@dataclass(frozen=True)
class AgentServerAuthConfig:
    """Auth-related dependency overrides for the server package."""

    provider: AgentServerAuthProvider = field(default_factory=get_default_auth_provider)
    current_user_dependency: DependencyCallable | None = None
    optional_user_dependency: DependencyCallable | None = None
    database_dependency: DependencyCallable | None = None


@dataclass(frozen=True)
class AgentServerConfig:
    """Composable FastAPI app configuration for the agent server."""

    title: str = "MyPrivateAgent"
    description: str = "私有 AI 对话助手"
    route_groups: tuple[str, ...] = DEFAULT_ROUTE_GROUPS
    route_names: tuple[str, ...] | None = None
    bootstrap: AgentServerBootstrapConfig = field(default_factory=AgentServerBootstrapConfig)
    ui: AgentServerUIConfig = field(default_factory=AgentServerUIConfig)
    cors_allow_origins: tuple[str, ...] = ("http://localhost:5173", "http://localhost:8000")
    cors_allow_origin_regex: str | None = None
    cors_allow_credentials: bool = True
    cors_allow_methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    cors_allow_headers: tuple[str, ...] = ("Authorization", "Content-Type", "X-Requested-With")
    cors_expose_headers: tuple[str, ...] = ("X-Request-Id",)
    cors_max_age: int = 600
    dependency_overrides: Mapping[DependencyCallable, DependencyCallable] = field(default_factory=dict)
    auth: AgentServerAuthConfig = field(default_factory=AgentServerAuthConfig)


def get_server_config_for_preset(preset: AgentServerPreset = DEFAULT_SERVER_PRESET) -> AgentServerConfig:
    """Return a reusable server config for a named deployment preset."""
    if preset == PRESET_FULL_STACK:
        return AgentServerConfig(
            **_load_cors_settings(),
        )

    if preset == PRESET_API_ONLY:
        return AgentServerConfig(
            route_groups=API_ONLY_ROUTE_GROUPS,
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            **_load_cors_settings(),
        )

    if preset == PRESET_EMBEDDED:
        return AgentServerConfig(
            route_groups=EMBEDDED_ROUTE_GROUPS,
            bootstrap=AgentServerBootstrapConfig(
                load_environment=False,
                init_database=False,
            ),
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            **_load_cors_settings(),
        )

    if preset == PRESET_LEARNING_DEMO:
        return AgentServerConfig(
            title="MyPrivateAgent Learning Demo",
            description="带自学习与运行时知识注入的通用 Agent Demo",
            route_groups=LEARNING_DEMO_ROUTE_GROUPS,
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            **_load_cors_settings(),
        )

    if preset == PRESET_WEATHER_DEMO:
        return AgentServerConfig(
            title="MyPrivateAgent Weather Demo",
            description="面向天气与实时查询场景的通用 Agent Demo",
            route_groups=WEATHER_DEMO_ROUTE_GROUPS,
            ui=AgentServerUIConfig(mode="spa"),
            **_load_cors_settings(),
        )

    if preset == PRESET_KNOWLEDGE_DEMO:
        return AgentServerConfig(
            title="MyPrivateAgent Knowledge Demo",
            description="面向知识问答与学习治理场景的通用 Agent Demo",
            route_groups=KNOWLEDGE_DEMO_ROUTE_GROUPS,
            ui=AgentServerUIConfig(mode="spa"),
            **_load_cors_settings(),
        )

    raise ValueError(f"Unsupported agent server preset: {preset}")


def get_available_server_presets() -> tuple[AgentServerPreset, ...]:
    """Return supported preset names."""
    return (
        PRESET_FULL_STACK,
        PRESET_API_ONLY,
        PRESET_EMBEDDED,
        PRESET_LEARNING_DEMO,
        PRESET_WEATHER_DEMO,
        PRESET_KNOWLEDGE_DEMO,
    )
