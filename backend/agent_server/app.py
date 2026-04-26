"""FastAPI app factory for the reusable server package."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .bootstrap import init_database, load_environment
from .config import (
    DEFAULT_SERVER_PRESET,
    AgentServerConfig,
    AgentServerPreset,
    get_server_config_for_preset,
)
from .dependencies import get_current_user, get_current_user_optional, get_db
from .router_registry import get_api_routers


logger = logging.getLogger(__name__)

def _build_dependency_overrides(config: AgentServerConfig) -> dict[object, object]:
    """Merge framework-level dependency overrides into one mapping."""
    overrides = dict(config.dependency_overrides)
    auth_provider = config.auth.provider

    overrides[get_current_user] = auth_provider.current_user_dependency
    overrides[get_current_user_optional] = auth_provider.optional_user_dependency
    overrides[get_db] = auth_provider.database_dependency

    if config.auth.current_user_dependency is not None:
        overrides[get_current_user] = config.auth.current_user_dependency
    if config.auth.optional_user_dependency is not None:
        overrides[get_current_user_optional] = config.auth.optional_user_dependency
    if config.auth.database_dependency is not None:
        overrides[get_db] = config.auth.database_dependency

    return overrides


def _create_lifespan(config: AgentServerConfig):
    @asynccontextmanager
    async def app_lifespan(_: FastAPI):
        """Run startup bootstrap steps for the configured server app."""
        if config.bootstrap.init_database:
            init_database()
        yield

    return app_lifespan


def _register_spa_ui(app: FastAPI, config: AgentServerConfig) -> bool:
    """Mount the Vue SPA as the primary UI if built assets are available."""
    dist_dir = config.ui.spa_dist_dir
    index_path = dist_dir / "index.html"
    assets_dir = dist_dir / "assets"

    if not dist_dir.exists() or not index_path.exists():
        logger.warning("Vue SPA 构建产物不存在，无法启用主前端: %s", dist_dir)
        return False

    if assets_dir.exists():
        app.mount(
            config.ui.spa_assets_mount_path,
            StaticFiles(directory=str(assets_dir)),
            name="frontend_assets",
        )
    else:
        logger.warning("Vue SPA assets 目录不存在: %s", assets_dir)

    def serve_spa() -> FileResponse:
        return FileResponse(str(index_path))

    for path in config.ui.spa_route_paths:
        app.add_api_route(path, serve_spa, methods=["GET"], include_in_schema=False)

    @app.get(config.ui.index_route_path, include_in_schema=False)
    def spa_index_redirect() -> RedirectResponse:
        return RedirectResponse(url="/chat")

    return True


def _register_ui(app: FastAPI, config: AgentServerConfig) -> None:
    """Register the configured primary SPA UI."""
    if not config.ui.enabled or config.ui.mode == "disabled":
        return

    if config.ui.mode == "spa":
        _register_spa_ui(app, config)


def create_app(
    config: AgentServerConfig | None = None,
    *,
    preset: AgentServerPreset = DEFAULT_SERVER_PRESET,
) -> FastAPI:
    """Create the configured FastAPI application instance."""
    app_config = config or get_server_config_for_preset(preset)
    if app_config.bootstrap.load_environment:
        load_environment()

    app = FastAPI(
        title=app_config.title,
        description=app_config.description,
        lifespan=_create_lifespan(app_config),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_config.cors_allow_origins),
        allow_credentials=app_config.cors_allow_credentials,
        allow_methods=list(app_config.cors_allow_methods),
        allow_headers=list(app_config.cors_allow_headers),
    )

    for dependency, override in _build_dependency_overrides(app_config).items():
        app.dependency_overrides[dependency] = override

    for router in get_api_routers(
        route_groups=app_config.route_groups,
        route_names=app_config.route_names,
    ):
        app.include_router(router)

    _register_ui(app, app_config)

    return app
