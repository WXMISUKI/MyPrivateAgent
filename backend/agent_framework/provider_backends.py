"""Concrete provider backends for the current application."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

try:
    from config import ARK_API_KEY, ARK_BASE_URL, ARK_MODEL, OLLAMA_BASE_URL
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import ARK_API_KEY, ARK_BASE_URL, ARK_MODEL, OLLAMA_BASE_URL
from .providers import ModelProviderRegistry

logger = logging.getLogger(__name__)


class DoubaoProviderBackend:
    """Volcengine Ark / Doubao provider backend."""

    provider_name = "doubao"

    def __init__(self):
        self._model: Optional[Any] = None
        self._initialize()

    def _initialize(self) -> None:
        logger.info("开始初始化豆包 provider，ARK_API_KEY=%s", "已配置" if ARK_API_KEY else "未配置")
        if not ARK_API_KEY:
            logger.warning("豆包模型未配置，将使用本地模型降级")
            return

        try:
            from langchain_openai import ChatOpenAI

            self._model = ChatOpenAI(
                base_url=ARK_BASE_URL,
                model=ARK_MODEL,
                api_key=ARK_API_KEY,
                temperature=0.7,
                max_tokens=2048,
                streaming=True,
                timeout=30,
            )
            logger.info("豆包 provider 初始化成功 model=%s", ARK_MODEL)
        except Exception as exc:
            logger.exception("初始化豆包 provider 失败: %s", exc)
            self._model = None

    def supports_model(self, model_name: str) -> bool:
        return model_name.lower().startswith("doubao")

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        if self._model is not None:
            return self._model

        logger.warning("豆包 provider 不可用，自动降级使用本地模型 llama3.1")
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model="llama3.1",
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
            streaming=True,
        )

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        return {
            "supports_reasoning": False,
            "type": "cloud",
            "name": "doubao",
            "provider": self.provider_name,
        }

    def is_model_available(self, model_name: str) -> bool:
        return self._model is not None

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        if not self._model:
            return {}
        return {
            "doubao": {
                "name": "doubao",
                "display_name": "豆包 (火山引擎)",
                "type": "cloud",
                "provider": self.provider_name,
                "has_reasoning": False,
                "available": True,
            }
        }


class OllamaProviderBackend:
    """Local Ollama provider backend."""

    provider_name = "ollama"
    _SUPPORTED_MODELS = {
        "llama3.1": {"display_name": "Llama 3.1", "has_reasoning": False},
        "deepseek-r1:7b": {"display_name": "DeepSeek R1 7B", "has_reasoning": True},
        "deepseek-r1": {"display_name": "DeepSeek R1", "has_reasoning": True},
        "llava": {"display_name": "LLaVA", "has_reasoning": False},
    }

    def supports_model(self, model_name: str) -> bool:
        normalized = model_name.lower()
        return normalized.startswith("ollama") or normalized in self._SUPPORTED_MODELS

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
            streaming=True,
        )

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        normalized = model_name.lower()
        if "deepseek" in normalized:
            return {
                "supports_reasoning": True,
                "type": "local",
                "name": model_name,
                "provider": self.provider_name,
            }
        return {
            "supports_reasoning": False,
            "type": "local",
            "name": model_name,
            "provider": self.provider_name,
        }

    def is_model_available(self, model_name: str) -> bool:
        return True

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        models: Dict[str, Dict[str, Any]] = {}
        for model_name, config in self._SUPPORTED_MODELS.items():
            models[model_name] = {
                "name": model_name,
                "display_name": config["display_name"],
                "type": "local",
                "provider": self.provider_name,
                "has_reasoning": config["has_reasoning"],
                "available": True,
            }
        return models


def create_default_provider_registry() -> ModelProviderRegistry:
    """Create the app's default provider registry."""
    registry = ModelProviderRegistry()
    registry.register_backend(DoubaoProviderBackend())
    registry.register_backend(OllamaProviderBackend())
    return registry
