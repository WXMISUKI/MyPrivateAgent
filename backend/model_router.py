"""
模型路由器
统一管理不同模型的创建和调用
"""
import logging
from typing import Any, Dict, Optional

try:
    from agent_framework.provider_backends import create_default_provider_registry
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.provider_backends import create_default_provider_registry

logger = logging.getLogger(__name__)


class ModelRouter:
    """模型路由器"""

    def __init__(self):
        self.registry = create_default_provider_registry()

    def get_model(
        self,
        model_name: str,
        purpose: str = "main"
    ) -> Any:
        """
        获取模型实例

        Args:
            model_name: 模型名称
            purpose: 用途（main/safety/compression）

        Returns:
            模型实例
        """
        logger.info(f"[ModelRouter] get_model 被调用: model_name={model_name}, purpose={purpose}")
        return self.registry.get_model(model_name, purpose=purpose)

    def create_ollama_model(
        self,
        model_name: str,
        temperature: float = 0.7
    ) -> Any:
        """
        创建 Ollama 模型实例

        Args:
            model_name: 模型名称
            temperature: 温度参数

        Returns:
            模型实例
        """
        return self.registry.get_model(model_name, purpose="main")

    def is_model_available(self, model_name: str) -> bool:
        """
        检查模型是否可用

        Args:
            model_name: 模型名称

        Returns:
            是否可用
        """
        return self.registry.is_model_available(model_name)

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用模型

        Returns:
            模型列表
        """
        return self.registry.list_available_models()

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型配置信息

        Args:
            model_name: 模型名称

        Returns:
            模型配置字典
        """
        logger.info("[ModelRouter] 获取模型配置: %s", model_name)
        return self.registry.get_model_config(model_name)


# 全局单例
_model_router_instance: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """
    获取全局模型路由器实例

    Returns:
        ModelRouter 实例
    """
    global _model_router_instance
    if _model_router_instance is None:
        _model_router_instance = ModelRouter()
    return _model_router_instance
