"""Persist small runtime-surface overrides for demo mode."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:
    from config import AUTH_MODE, DEFAULT_MODEL, IS_VERCEL, LOCAL_DATA_DIR
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import AUTH_MODE, DEFAULT_MODEL, IS_VERCEL, LOCAL_DATA_DIR


RUNTIME_SURFACE_CONFIG_PATH = Path(LOCAL_DATA_DIR) / "runtime_surface.json"
ALLOWED_AUTH_MODES = {"demo_guest", "business_auth"}


class RuntimeSurfaceConfigService:
    """Read and persist safe runtime-surface overrides."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or RUNTIME_SURFACE_CONFIG_PATH
        self._memory_overrides: Dict[str, Any] = {}

    def get_defaults(self) -> Dict[str, Any]:
        return {
            "auth_mode": AUTH_MODE,
            "default_model": DEFAULT_MODEL,
            "enabled_providers": [],
            "failover_thresholds": {
                "medium": 0.2,
                "high": 0.4,
            },
        }

    def get_config_layers(self) -> Dict[str, Any]:
        defaults = self.get_defaults()
        overrides = self.load_overrides()
        return {
            "defaults": defaults,
            "overrides": overrides,
            "effective": self.get_effective_config(),
            "override_path": str(self.config_path),
            "editable_keys": ["auth_mode", "default_model", "enabled_providers", "failover_thresholds"],
        }

    def load_overrides(self) -> Dict[str, Any]:
        if IS_VERCEL:
            return dict(self._memory_overrides)
        if not self.config_path.exists():
            return {}
        try:
            parsed = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(parsed, dict):
            return {}
        return parsed

    def get_effective_config(self) -> Dict[str, Any]:
        effective = self.get_defaults()
        effective.update(self.load_overrides())
        return effective

    def update_overrides(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        current = self.load_overrides()
        updated = dict(current)

        if "auth_mode" in payload:
            auth_mode = str(payload.get("auth_mode") or "").strip().lower()
            if auth_mode not in ALLOWED_AUTH_MODES:
                raise ValueError("auth_mode 仅支持 demo_guest 或 business_auth")
            updated["auth_mode"] = auth_mode

        if "default_model" in payload:
            default_model = str(payload.get("default_model") or "").strip()
            if not default_model:
                raise ValueError("default_model 不能为空")
            updated["default_model"] = default_model

        if "enabled_providers" in payload:
            raw_enabled = payload.get("enabled_providers") or []
            if not isinstance(raw_enabled, list):
                raise ValueError("enabled_providers 必须是 provider_id 字符串列表")
            normalized: list[str] = []
            for item in raw_enabled:
                provider_id = str(item or "").strip()
                if provider_id and provider_id not in normalized:
                    normalized.append(provider_id)
            updated["enabled_providers"] = normalized

        if "failover_thresholds" in payload:
            raw_thresholds = payload.get("failover_thresholds") or {}
            if not isinstance(raw_thresholds, dict):
                raise ValueError("failover_thresholds 必须是对象")
            current_thresholds = dict((updated.get("failover_thresholds") or self.get_defaults()["failover_thresholds"]))
            medium = raw_thresholds.get("medium", current_thresholds.get("medium"))
            high = raw_thresholds.get("high", current_thresholds.get("high"))
            try:
                medium_value = float(medium)
                high_value = float(high)
            except (TypeError, ValueError) as exc:
                raise ValueError("failover_thresholds.medium/high 必须是数字") from exc
            if not (0 < medium_value < 1 and 0 < high_value < 1):
                raise ValueError("failover_thresholds.medium/high 必须在 (0,1) 区间")
            if high_value <= medium_value:
                raise ValueError("failover_thresholds.high 必须大于 medium")
            updated["failover_thresholds"] = {
                "medium": round(medium_value, 4),
                "high": round(high_value, 4),
            }

        if IS_VERCEL:
            self._memory_overrides = dict(updated)
            return self.get_effective_config()

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return self.get_effective_config()


_runtime_surface_config_service: RuntimeSurfaceConfigService | None = None


def get_runtime_surface_config_service() -> RuntimeSurfaceConfigService:
    global _runtime_surface_config_service
    if _runtime_surface_config_service is None:
        _runtime_surface_config_service = RuntimeSurfaceConfigService()
    return _runtime_surface_config_service
