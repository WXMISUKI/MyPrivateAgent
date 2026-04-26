"""Central router registration for the server package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

try:
    from routers import auth, chat, conversations, health, learnings, mcp, memory, permissions, plans, skills
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.routers import auth, chat, conversations, health, learnings, mcp, memory, permissions, plans, skills


@dataclass(frozen=True)
class RouterRegistration:
    """Metadata describing how a router participates in server assembly."""

    name: str
    groups: tuple[str, ...]
    router: object


ROUTER_REGISTRATIONS = (
    RouterRegistration(name="auth", groups=("auth",), router=auth.router),
    RouterRegistration(name="health", groups=("core",), router=health.router),
    RouterRegistration(name="conversations", groups=("core",), router=conversations.router),
    RouterRegistration(name="chat", groups=("core",), router=chat.router),
    RouterRegistration(name="skills", groups=("skills",), router=skills.router),
    RouterRegistration(name="mcp", groups=("mcp", "core"), router=mcp.router),
    RouterRegistration(name="plans", groups=("planner", "core"), router=plans.router),
    RouterRegistration(name="learnings", groups=("learning",), router=learnings.router),
    RouterRegistration(name="permissions", groups=("permissions",), router=permissions.router),
    RouterRegistration(name="memory", groups=("admin",), router=memory.router),
)


def get_route_group_names() -> tuple[str, ...]:
    """Return the supported router group names."""
    return tuple(
        dict.fromkeys(
            group
            for registration in ROUTER_REGISTRATIONS
            for group in registration.groups
        )
    )


def get_api_router_registrations(
    route_groups: Sequence[str] | None = None,
    route_names: Sequence[str] | None = None,
) -> tuple[RouterRegistration, ...]:
    """Return router registrations filtered by groups and explicit router names."""
    allowed_groups = set(route_groups) if route_groups is not None else None
    allowed_names = set(route_names) if route_names is not None else None

    registrations = []
    for registration in ROUTER_REGISTRATIONS:
        if allowed_groups is not None and not allowed_groups.intersection(registration.groups):
            continue
        if allowed_names is not None and registration.name not in allowed_names:
            continue
        registrations.append(registration)

    return tuple(registrations)


def get_api_routers(
    route_groups: Sequence[str] | None = None,
    route_names: Sequence[str] | None = None,
) -> Iterable[object]:
    """Return FastAPI routers filtered by configuration."""
    return tuple(
        registration.router
        for registration in get_api_router_registrations(
            route_groups=route_groups,
            route_names=route_names,
        )
    )
