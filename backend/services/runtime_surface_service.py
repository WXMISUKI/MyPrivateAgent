"""Runtime surface helpers for demo mode and dynamic model/provider catalogs."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from config import AUTH_MODE, DEFAULT_MODEL
    from model_router import get_model_router
    from services.agent_memory_service import get_agent_memory_service
    from services.agent_hook_service import get_agent_hook_service
    from services.capability_profile_service import get_capability_profile_service
    from services.runtime_surface_config_service import get_runtime_surface_config_service
    from services.subagent_service import get_subagent_runtime_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import AUTH_MODE, DEFAULT_MODEL
    from backend.model_router import get_model_router
    from backend.services.agent_memory_service import get_agent_memory_service
    from backend.services.agent_hook_service import get_agent_hook_service
    from backend.services.capability_profile_service import get_capability_profile_service
    from backend.services.runtime_surface_config_service import get_runtime_surface_config_service
    from backend.services.subagent_service import get_subagent_runtime_service


class RuntimeSurfaceService:
    """Expose model/provider/auth surface to clients."""

    def __init__(self):
        self.model_router = get_model_router()
        self.config_service = get_runtime_surface_config_service()
        self.capability_profile_service = get_capability_profile_service()
        self.agent_memory_service = get_agent_memory_service()
        self.agent_hook_service = get_agent_hook_service()
        self.subagent_runtime_service = get_subagent_runtime_service()

    def _list_all_models(self) -> List[Dict[str, Any]]:
        models = list(self.model_router.list_available_models().values())
        models.sort(key=lambda item: (not bool(item.get("is_default")), item.get("provider", ""), item.get("display_name", item.get("name", ""))))
        return models

    def _resolve_enabled_provider_ids(self, provider_ids: List[str], effective_config: Dict[str, Any]) -> set[str]:
        configured = [
            str(item or "").strip()
            for item in (effective_config.get("enabled_providers") or [])
            if str(item or "").strip()
        ]
        if not configured:
            return set(provider_ids)
        return {provider_id for provider_id in configured if provider_id in provider_ids}

    def list_models(self) -> List[Dict[str, Any]]:
        effective_config = self.config_service.get_effective_config()
        models = self._list_all_models()
        provider_ids = sorted({str(item.get("provider") or "unknown") for item in models})
        enabled_provider_ids = self._resolve_enabled_provider_ids(provider_ids, effective_config)
        return [item for item in models if str(item.get("provider") or "unknown") in enabled_provider_ids]

    def get_runtime_profile(self) -> Dict[str, Any]:
        effective_config = self.config_service.get_effective_config()
        all_models = self._list_all_models()
        providers: Dict[str, Dict[str, Any]] = {}
        provider_ids = sorted({str(item.get("provider") or "unknown") for item in all_models})
        enabled_provider_ids = self._resolve_enabled_provider_ids(provider_ids, effective_config)
        models = [item for item in all_models if str(item.get("provider") or "unknown") in enabled_provider_ids]

        override_provider_ids = {
            str(item or "").strip()
            for item in (self.config_service.load_overrides().get("enabled_providers") or [])
            if str(item or "").strip()
        }

        for item in all_models:
            provider_id = str(item.get("provider") or "unknown")
            provider_entry = providers.setdefault(
                provider_id,
                {
                    "provider_id": provider_id,
                    "display_name": item.get("provider_label") or provider_id,
                    "type": item.get("type") or "unknown",
                    "base_url": item.get("base_url"),
                    "configured": False,
                    "models": [],
                    "enabled": provider_id in enabled_provider_ids,
                    "enabled_source": "override" if provider_id in override_provider_ids else "default",
                    "model_sources": [],
                    "actual_models": [],
                },
            )
            provider_entry["configured"] = provider_entry["configured"] or bool(item.get("configured", False))
            provider_entry["models"].append(item["name"])
            provider_entry.setdefault("available_model_count", 0)
            provider_entry.setdefault("configured_model_count", 0)
            provider_entry.setdefault("total_model_count", 0)
            source_name = str(item.get("source") or "unknown")
            if source_name and source_name not in provider_entry["model_sources"]:
                provider_entry["model_sources"].append(source_name)
            actual_model = str(item.get("actual_model") or "").strip()
            if actual_model and actual_model not in provider_entry["actual_models"]:
                provider_entry["actual_models"].append(actual_model)
            if item.get("available"):
                provider_entry["available_model_count"] += 1
            if item.get("configured"):
                provider_entry["configured_model_count"] += 1
            provider_entry["total_model_count"] += 1

        config_layers = self.config_service.get_config_layers()
        config_layers["provider_resolution"] = {
            "available_provider_ids": provider_ids,
            "enabled_provider_ids": sorted(enabled_provider_ids),
            "disabled_provider_ids": sorted(set(provider_ids) - set(enabled_provider_ids)),
            "default_behavior": "all_enabled" if not override_provider_ids else "override_selected",
        }

        return {
            "agent_mode": "general_demo",
            "auth_mode": effective_config.get("auth_mode", AUTH_MODE),
            "default_model": effective_config.get("default_model", DEFAULT_MODEL),
            "models": models,
            "providers": list(providers.values()),
            "capability_contract": self.capability_profile_service.build_runtime_contract(),
            "memory_contract": self.agent_memory_service.build_runtime_contract(),
            "subagent_contract": self.subagent_runtime_service.build_runtime_contract(),
            "hook_contract": self.agent_hook_service.build_runtime_contract(),
            "config_layers": config_layers,
            "auth_mode_contract": {
                "current_mode": effective_config.get("auth_mode", AUTH_MODE),
                "demo_guest_description": "免登录直达，适合通用框架演示、能力盘点与本地调试。",
                "business_auth_description": "登录页作为正式入口，适合后续接入真实鉴权、组织和权限体系。",
            },
        }

    def update_runtime_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(payload or {})
        all_models = self._list_all_models()
        available_model_names = {item["name"] for item in all_models}
        provider_by_model = {
            item["name"]: str(item.get("provider") or "unknown")
            for item in all_models
        }
        available_provider_ids = sorted({provider_by_model[item["name"]] for item in all_models})
        current_effective = self.config_service.get_effective_config()

        requested_enabled = payload.get("enabled_providers")
        if requested_enabled is None:
            enabled_provider_ids = self._resolve_enabled_provider_ids(available_provider_ids, current_effective)
        else:
            if not isinstance(requested_enabled, list):
                raise ValueError("enabled_providers 必须是 provider_id 字符串列表")
            unknown_provider_ids = sorted(
                {
                    str(item or "").strip()
                    for item in requested_enabled
                    if str(item or "").strip() and str(item or "").strip() not in available_provider_ids
                }
            )
            if unknown_provider_ids:
                raise ValueError(f"enabled_providers 包含未知 provider: {', '.join(unknown_provider_ids)}")
            enabled_provider_ids = self._resolve_enabled_provider_ids(
                available_provider_ids,
                {"enabled_providers": requested_enabled},
            )

        candidate_default_model = str(
            payload.get("default_model")
            or current_effective.get("default_model", DEFAULT_MODEL)
        ).strip()
        if "default_model" in payload:
            if payload["default_model"] not in available_model_names:
                raise ValueError(f"default_model `{payload['default_model']}` 不在当前运行时模型目录中")
        if candidate_default_model:
            model_provider = provider_by_model.get(candidate_default_model)
            if model_provider and model_provider not in enabled_provider_ids:
                raise ValueError(f"default_model `{candidate_default_model}` 所属 provider 当前未启用，请先启用对应 provider 或切换默认模型")

        self.config_service.update_overrides(payload)
        return self.get_runtime_profile()


_runtime_surface_service: RuntimeSurfaceService | None = None


def get_runtime_surface_service() -> RuntimeSurfaceService:
    global _runtime_surface_service
    if _runtime_surface_service is None:
        _runtime_surface_service = RuntimeSurfaceService()
    return _runtime_surface_service
