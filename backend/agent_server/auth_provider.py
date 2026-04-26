"""Auth provider abstractions for reusable server assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

try:
    from auth import get_current_user, get_current_user_optional, oauth2_scheme
    from database import get_db
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.auth import get_current_user, get_current_user_optional, oauth2_scheme
    from backend.database import get_db


DependencyCallable = Callable[..., Any]


@dataclass(frozen=True)
class AgentServerAuthProvider:
    """Concrete auth provider definition used by the app factory."""

    name: str
    current_user_dependency: DependencyCallable
    optional_user_dependency: DependencyCallable
    database_dependency: DependencyCallable
    oauth2_scheme_dependency: Any | None = None


def get_default_auth_provider() -> AgentServerAuthProvider:
    """Return the default JWT/Bearer auth provider backed by the current app."""
    return AgentServerAuthProvider(
        name="default_jwt",
        current_user_dependency=get_current_user,
        optional_user_dependency=get_current_user_optional,
        database_dependency=get_db,
        oauth2_scheme_dependency=oauth2_scheme,
    )


def create_auth_provider(
    *,
    name: str,
    current_user_dependency: DependencyCallable,
    optional_user_dependency: DependencyCallable | None = None,
    database_dependency: DependencyCallable | None = None,
    oauth2_scheme_dependency: Any | None = None,
) -> AgentServerAuthProvider:
    """Create a reusable auth provider from dependency callables."""
    return AgentServerAuthProvider(
        name=name,
        current_user_dependency=current_user_dependency,
        optional_user_dependency=optional_user_dependency or current_user_dependency,
        database_dependency=database_dependency or get_db,
        oauth2_scheme_dependency=oauth2_scheme_dependency,
    )


def create_anonymous_auth_provider(
    *,
    user: Any | None = None,
    user_factory: Callable[[], Any] | None = None,
    database_dependency: DependencyCallable | None = None,
) -> AgentServerAuthProvider:
    """Create a provider that skips auth and always returns a synthetic user."""

    def _resolve_user() -> Any:
        if user_factory is not None:
            return user_factory()
        if user is not None:
            return user
        return {"id": "anonymous", "username": "anonymous"}

    def _get_current_user() -> Any:
        return _resolve_user()

    def _get_current_user_optional() -> Any:
        return _resolve_user()

    return AgentServerAuthProvider(
        name="anonymous",
        current_user_dependency=_get_current_user,
        optional_user_dependency=_get_current_user_optional,
        database_dependency=database_dependency or get_db,
        oauth2_scheme_dependency=None,
    )
