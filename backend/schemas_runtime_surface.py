"""Schemas for runtime-surface read/write APIs."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class RuntimeSurfaceUpdateRequest(BaseModel):
    auth_mode: Optional[str] = None
    default_model: Optional[str] = None
    enabled_providers: Optional[List[str]] = None
