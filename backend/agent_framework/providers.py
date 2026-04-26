"""Provider interfaces and registry used by the reusable runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class ModelProvider(Protocol):
    """Minimal provider surface required by the runtime."""

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        ...

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        ...


@runtime_checkable
class ProviderBackend(Protocol):
    """Backend contract for a concrete model provider."""

    provider_name: str

    def supports_model(self, model_name: str) -> bool:
        ...

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        ...

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        ...

    def is_model_available(self, model_name: str) -> bool:
        ...

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        ...


@dataclass
class ProviderSelection:
    """Resolved backend selection for a model name."""

    backend: ProviderBackend
    normalized_model_name: str


class ModelProviderRegistry(ModelProvider):
    """Registry that routes model requests to concrete backends."""

    def __init__(self):
        self._backends: List[ProviderBackend] = []

    def register_backend(self, backend: ProviderBackend) -> None:
        self._backends.append(backend)

    def resolve(self, model_name: str) -> ProviderSelection:
        normalized = model_name.lower()
        for backend in self._backends:
            if backend.supports_model(normalized):
                return ProviderSelection(backend=backend, normalized_model_name=normalized)
        raise ValueError(f"不支持的模型: {model_name}")

    def get_model(self, model_name: str, purpose: str = "main") -> Any:
        selection = self.resolve(model_name)
        return selection.backend.get_model(model_name, purpose=purpose)

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        selection = self.resolve(model_name)
        return selection.backend.get_model_config(model_name)

    def is_model_available(self, model_name: str) -> bool:
        selection = self.resolve(model_name)
        return selection.backend.is_model_available(model_name)

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        models: Dict[str, Dict[str, Any]] = {}
        for backend in self._backends:
            models.update(backend.list_available_models())
        return models

    def list_backends(self) -> List[str]:
        return [backend.provider_name for backend in self._backends]
