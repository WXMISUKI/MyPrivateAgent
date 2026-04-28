"""Concrete provider backends for the current application."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

try:
    from config import (
        ARK_API_KEY,
        ARK_BASE_URL,
        ARK_EXTRA_MODELS,
        ARK_MODEL,
        ARK_MODEL_ALIAS,
        ARK_MODEL_DISPLAY_NAME,
        DEFAULT_MODEL,
        OLLAMA_BASE_URL,
        load_model_catalog_config,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import (
        ARK_API_KEY,
        ARK_BASE_URL,
        ARK_EXTRA_MODELS,
        ARK_MODEL,
        ARK_MODEL_ALIAS,
        ARK_MODEL_DISPLAY_NAME,
        DEFAULT_MODEL,
        OLLAMA_BASE_URL,
        load_model_catalog_config,
    )
from .providers import ModelProviderRegistry

logger = logging.getLogger(__name__)


def _coerce_bool(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


class DoubaoProviderBackend:
    """Volcengine Ark / Doubao provider backend with configurable model aliases."""

    provider_name = "volcengine-ark"

    def __init__(self):
        self._models = self._build_model_catalog()
        self._clients: Dict[str, Any] = {}

    def _build_model_catalog(self) -> Dict[str, Dict[str, Any]]:
        catalog: Dict[str, Dict[str, Any]] = {
            ARK_MODEL_ALIAS.lower(): {
                "name": ARK_MODEL_ALIAS.lower(),
                "display_name": ARK_MODEL_DISPLAY_NAME,
                "actual_model": ARK_MODEL,
                "has_reasoning": False,
                "type": "cloud",
                "provider": self.provider_name,
                "source": "env",
            }
        }

        for chunk in [item.strip() for item in ARK_EXTRA_MODELS.split(",") if item.strip()]:
            alias_part, sep, rest = chunk.partition("=")
            if not sep or not alias_part.strip() or not rest.strip():
                continue
            segments = [item.strip() for item in rest.split("|")]
            actual_model = segments[0] if segments else ""
            if not actual_model:
                continue
            alias = alias_part.strip().lower()
            catalog[alias] = {
                "name": alias,
                "display_name": segments[1] if len(segments) > 1 and segments[1] else alias,
                "actual_model": actual_model,
                "has_reasoning": _coerce_bool(segments[2]) if len(segments) > 2 else False,
                "type": "cloud",
                "provider": self.provider_name,
                "source": "env",
            }

        for item in load_model_catalog_config():
            if str(item.get("provider", "")).strip().lower() not in {self.provider_name, "doubao", "volcengine"}:
                continue
            alias = str(item.get("name") or "").strip().lower()
            actual_model = str(item.get("actual_model") or item.get("model") or "").strip()
            if not alias or not actual_model:
                continue
            catalog[alias] = {
                "name": alias,
                "display_name": str(item.get("display_name") or alias).strip(),
                "actual_model": actual_model,
                "has_reasoning": bool(item.get("has_reasoning", False)),
                "type": "cloud",
                "provider": self.provider_name,
                "source": "catalog_json",
            }

        return catalog

    def supports_model(self, model_name: str) -> bool:
        return model_name in self._models

    def _create_client(self, alias: str) -> Any:
        if alias in self._clients:
            return self._clients[alias]
        if not ARK_API_KEY:
            raise ValueError("ARK_API_KEY 未配置")

        from langchain_openai import ChatOpenAI

        config = self._models[alias]
        client = ChatOpenAI(
            base_url=ARK_BASE_URL,
            model=config["actual_model"],
            api_key=ARK_API_KEY,
            temperature=0.7,
            max_tokens=2048,
            streaming=True,
            timeout=30,
        )
        self._clients[alias] = client
        return client

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        alias = model_name.lower()
        if alias not in self._models:
            raise ValueError(f"豆包 provider 不支持模型: {model_name}")

        if ARK_API_KEY:
            return self._create_client(alias)

        logger.warning("豆包 provider 未配置 API key，自动降级使用本地模型 llama3.1")
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model="llama3.1",
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
            streaming=True,
        )

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        alias = model_name.lower()
        config = self._models.get(alias) or self._models.get(ARK_MODEL_ALIAS.lower())
        return {
            "supports_reasoning": bool(config.get("has_reasoning", False)),
            "type": "cloud",
            "name": alias,
            "provider": self.provider_name,
            "actual_model": config.get("actual_model", ARK_MODEL),
            "base_url": ARK_BASE_URL,
        }

    def is_model_available(self, model_name: str) -> bool:
        return bool(ARK_API_KEY) and model_name.lower() in self._models

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        models: Dict[str, Dict[str, Any]] = {}
        for alias, config in self._models.items():
            models[alias] = {
                "name": alias,
                "display_name": config["display_name"],
                "type": "cloud",
                "provider": self.provider_name,
                "provider_label": "火山引擎 Ark",
                "has_reasoning": bool(config.get("has_reasoning", False)),
                "available": bool(ARK_API_KEY),
                "configured": bool(ARK_API_KEY),
                "is_default": alias == DEFAULT_MODEL,
                "base_url": ARK_BASE_URL,
                "actual_model": config["actual_model"],
                "source": config.get("source", "env"),
            }
        return models


class OllamaProviderBackend:
    """Local Ollama provider backend with installed-model discovery."""

    provider_name = "ollama"
    _SUPPORTED_MODELS = {
        "llama3.1": {"display_name": "Llama 3.1", "has_reasoning": False},
        "deepseek-r1:7b": {"display_name": "DeepSeek R1 7B", "has_reasoning": True},
        "deepseek-r1": {"display_name": "DeepSeek R1", "has_reasoning": True},
        "llava": {"display_name": "LLaVA", "has_reasoning": False},
    }

    def __init__(self):
        self._installed_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def _infer_display_name(self, name: str) -> str:
        base = name.replace(":", " ").replace("-", " ").strip()
        return " ".join(part.capitalize() for part in base.split()) or name

    def _infer_reasoning(self, name: str) -> bool:
        lowered = name.lower()
        return "deepseek" in lowered or "r1" in lowered or "reason" in lowered

    def _fetch_installed_models(self) -> Dict[str, Dict[str, Any]]:
        if self._installed_cache is not None:
            return self._installed_cache

        models: Dict[str, Dict[str, Any]] = {}
        try:
            response = httpx.get(f"{OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=2.5)
            response.raise_for_status()
            payload = response.json()
            for item in payload.get("models", []):
                name = str(item.get("name") or "").strip()
                if not name:
                    continue
                models[name] = {
                    "name": name,
                    "display_name": self._infer_display_name(name),
                    "type": "local",
                    "provider": self.provider_name,
                    "provider_label": "Ollama",
                    "has_reasoning": self._infer_reasoning(name),
                    "available": True,
                    "configured": True,
                    "is_default": name == DEFAULT_MODEL,
                    "base_url": OLLAMA_BASE_URL,
                    "source": "ollama_probe",
                }
        except Exception as exc:  # pragma: no cover - depends on local ollama
            logger.info("Ollama 模型探测失败，回退到内置目录: %s", exc)

        self._installed_cache = models
        return models

    def supports_model(self, model_name: str) -> bool:
        normalized = model_name.lower()
        installed = self._fetch_installed_models()
        return normalized in {name.lower() for name in installed} or normalized in self._SUPPORTED_MODELS

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
            streaming=True,
        )

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        return {
            "supports_reasoning": self._infer_reasoning(model_name),
            "type": "local",
            "name": model_name,
            "provider": self.provider_name,
            "base_url": OLLAMA_BASE_URL,
        }

    def is_model_available(self, model_name: str) -> bool:
        installed = self._fetch_installed_models()
        if installed:
            return model_name in installed
        return True

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        models = dict(self._fetch_installed_models())
        has_probe_results = bool(models)
        for model_name, config in self._SUPPORTED_MODELS.items():
            models.setdefault(
                model_name,
                {
                    "name": model_name,
                    "display_name": config["display_name"],
                    "type": "local",
                    "provider": self.provider_name,
                    "provider_label": "Ollama",
                    "has_reasoning": config["has_reasoning"],
                    "available": has_probe_results,
                    "configured": has_probe_results,
                    "is_default": model_name == DEFAULT_MODEL,
                    "base_url": OLLAMA_BASE_URL,
                    "source": "builtin",
                },
            )
        return models


def create_default_provider_registry() -> ModelProviderRegistry:
    """Create the app's default provider registry."""
    registry = ModelProviderRegistry()
    registry.register_backend(DoubaoProviderBackend())
    registry.register_backend(OllamaProviderBackend())
    return registry
