"""Public facade for external framework adapter SPI.

The implementation lives in ``framework_adapter_spi`` so the public import path
can stay stable while the adapter modules remain small and focused.
"""

from __future__ import annotations

from typing import List, Optional

try:
    from config import (
        ENABLE_LANGGRAPH_DRAFT_ADAPTER,
        ENABLE_LANGGRAPH_EXTERNAL_PILOT,
        ENABLE_LANGGRAPH_RUNTIME_EXECUTION,
        ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER,
        LANGGRAPH_ASSISTANT_ID,
        LANGGRAPH_RUNTIME_ENDPOINT,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.config import (
        ENABLE_LANGGRAPH_DRAFT_ADAPTER,
        ENABLE_LANGGRAPH_EXTERNAL_PILOT,
        ENABLE_LANGGRAPH_RUNTIME_EXECUTION,
        ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER,
        LANGGRAPH_ASSISTANT_ID,
        LANGGRAPH_RUNTIME_ENDPOINT,
    )

from .framework_adapter_spi import (
    AgentFrameworkAdapter,
    AgentFrameworkAdapterRegistry,
    FrameworkAdapterHealth,
    LangGraphDraftAdapter,
    LocalFakeFrameworkAdapter,
    NoopFrameworkAdapter,
    _is_python_package_available,
)


_framework_adapter_registry: Optional[AgentFrameworkAdapterRegistry] = None


def get_framework_adapter_registry() -> AgentFrameworkAdapterRegistry:
    global _framework_adapter_registry
    if _framework_adapter_registry is None:
        adapters: List[AgentFrameworkAdapter] = []
        if ENABLE_LANGGRAPH_DRAFT_ADAPTER:
            adapters.append(LangGraphDraftAdapter())
        if ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER:
            adapters.append(LocalFakeFrameworkAdapter())
        _framework_adapter_registry = AgentFrameworkAdapterRegistry(adapters)
    return _framework_adapter_registry


__all__ = [
    "AgentFrameworkAdapter",
    "AgentFrameworkAdapterRegistry",
    "FrameworkAdapterHealth",
    "LangGraphDraftAdapter",
    "LocalFakeFrameworkAdapter",
    "NoopFrameworkAdapter",
    "ENABLE_LANGGRAPH_DRAFT_ADAPTER",
    "ENABLE_LANGGRAPH_EXTERNAL_PILOT",
    "ENABLE_LANGGRAPH_RUNTIME_EXECUTION",
    "ENABLE_LOCAL_FAKE_FRAMEWORK_ADAPTER",
    "LANGGRAPH_ASSISTANT_ID",
    "LANGGRAPH_RUNTIME_ENDPOINT",
    "_framework_adapter_registry",
    "_is_python_package_available",
    "get_framework_adapter_registry",
]
