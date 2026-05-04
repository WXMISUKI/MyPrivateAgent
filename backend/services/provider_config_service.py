"""Provider configuration persistence — allows frontend to manage API keys and base URLs."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

KNOWN_PROVIDERS = {
    "volcengine-ark": {
        "display_name": "火山引擎 Ark (豆包)",
        "requires_api_key": True,
        "default_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "env_key_api_key": "ARK_API_KEY",
        "env_key_base_url": "ARK_BASE_URL",
        "env_key_model": "ARK_MODEL",
        "default_model": "doubao-seed-2-0-mini-260215",
        "test_endpoint": None,
    },
    "ollama": {
        "display_name": "Ollama (本地)",
        "requires_api_key": False,
        "default_base_url": "http://localhost:11434",
        "env_key_api_key": None,
        "env_key_base_url": "OLLAMA_BASE_URL",
        "env_key_model": None,
        "default_model": "",
        "test_endpoint": "/api/tags",
    },
}

CONFIG_FILENAME = "provider_config.json"


class ProviderConfigService:
    def __init__(self, data_dir: Path | None = None):
        self._is_vercel = os.getenv("VERCEL", "").strip() == "1"
        self._memory_overrides: dict[str, dict[str, Any]] = {}
        if data_dir is None:
            try:
                from config import LOCAL_DATA_DIR
            except ModuleNotFoundError:
                from backend.config import LOCAL_DATA_DIR
            data_dir = Path(LOCAL_DATA_DIR)
        self._data_dir = data_dir
        self._config_path = self._data_dir / CONFIG_FILENAME

    def _load_local_overrides(self) -> dict[str, dict[str, Any]]:
        if self._is_vercel:
            return dict(self._memory_overrides)
        if not self._config_path.exists():
            return {}
        try:
            data = json.loads(self._config_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("Failed to load provider config: %s", e)
            return {}

    def _save_local_overrides(self, overrides: dict[str, dict[str, Any]]) -> None:
        if self._is_vercel:
            self._memory_overrides = dict(overrides)
            return
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(overrides, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _get_env_value(self, env_key: str | None) -> str:
        if not env_key:
            return ""
        import os
        return os.getenv(env_key, "").strip()

    def mask_api_key(self, key: str | None) -> str | None:
        if not key or not key.strip():
            return None
        k = key.strip()
        if len(k) <= 8:
            return "****"
        return f"{k[:4]}****{k[-4:]}"

    def get_effective_config(self, provider_name: str) -> dict[str, Any]:
        spec = KNOWN_PROVIDERS.get(provider_name)
        if not spec:
            return {"config_source": "unconfigured"}

        overrides = self._load_local_overrides().get(provider_name, {})
        env_api_key = self._get_env_value(spec.get("env_key_api_key"))
        env_base_url = self._get_env_value(spec.get("env_key_base_url")) or spec["default_base_url"]

        api_key = overrides.get("api_key") or env_api_key
        base_url = overrides.get("base_url") or env_base_url
        env_model = self._get_env_value(spec.get("env_key_model")) or spec.get("default_model", "")
        model_name = overrides.get("model_name") or env_model

        if overrides.get("api_key") or overrides.get("base_url") or overrides.get("model_name"):
            config_source = "local_override"
        elif api_key or (not spec["requires_api_key"]):
            config_source = "env"
        else:
            config_source = "unconfigured"

        return {
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name,
            "config_source": config_source,
        }

    def list_providers(self) -> list[dict[str, Any]]:
        result = []
        for name, spec in KNOWN_PROVIDERS.items():
            effective = self.get_effective_config(name)
            result.append({
                "name": name,
                "display_name": spec["display_name"],
                "requires_api_key": spec["requires_api_key"],
                "configured": effective["config_source"] != "unconfigured",
                "api_key_masked": self.mask_api_key(effective["api_key"]) if spec["requires_api_key"] else None,
                "base_url": effective["base_url"],
                "model_name": effective.get("model_name", ""),
                "config_source": effective["config_source"],
                "last_test": None,
            })
        return result

    def update_provider(self, provider_name: str, updates: dict[str, Any]) -> dict[str, Any]:
        if provider_name not in KNOWN_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")

        overrides = self._load_local_overrides()
        provider_overrides = overrides.get(provider_name, {})

        if "api_key" in updates and updates["api_key"]:
            provider_overrides["api_key"] = updates["api_key"].strip()
        if "base_url" in updates and updates["base_url"]:
            provider_overrides["base_url"] = updates["base_url"].strip()
        if "model_name" in updates and updates["model_name"]:
            provider_overrides["model_name"] = updates["model_name"].strip()

        overrides[provider_name] = provider_overrides
        self._save_local_overrides(overrides)
        logger.info("Provider config updated: %s (source: local_override)", provider_name)

        return {"status": "saved", "config_source": "local_override"}


_instance: ProviderConfigService | None = None


def get_provider_config_service() -> ProviderConfigService:
    global _instance
    if _instance is None:
        _instance = ProviderConfigService()
    return _instance
