"""Reusable FastAPI dependency entrypoints for the server package."""

from __future__ import annotations

try:
    from auth import get_current_user, get_current_user_optional, oauth2_scheme
    from database import get_db
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.auth import get_current_user, get_current_user_optional, oauth2_scheme
    from backend.database import get_db

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "get_db",
    "oauth2_scheme",
]
