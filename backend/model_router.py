"""
模型路由器
统一管理不同模型的创建和调用
"""
import logging
from typing import Dict, Any, Optional, List
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from config import (
    OLLAMA_BASE_URL,
    ARK_API_KEY,
    ARK_BASE_URL,
    ARK_MODEL,
    AVAILABLE_MODELS
)

logger = logging.getLogger(__name__)


class ModelRouter:
    """模型路由器"""

    def __init__(self):
        self.models: Dict[str, Any] = {}
        self._initialize_models()

    def _initialize_models(self):
        """初始化所有模型"""
        # 初始化豆包模型
        print(f"开始初始化模型，ARK_API_KEY: {'已配置' if ARK_API_KEY else '未配置'}")
        print(f"[ModelRouter] ARK_BASE_URL: {ARK_BASE_URL}")
        print(f"[ModelRouter] ARK_MODEL: {ARK_MODEL}")
        print(f"[ModelRouter] ARK_API_KEY: {ARK_API_KEY[:10] if ARK_API_KEY else 'None'}...")
        
        if ARK_API_KEY:
            try:
                print(f"正在初始化豆包模型: {ARK_MODEL}")
                print(f"[ModelRouter] 准备初始化 ChatOpenAI")
                print(f"[ModelRouter] 参数: base_url={ARK_BASE_URL}, model={ARK_MODEL}, temperature=0.7, max_tokens=2048, streaming=True, timeout=30")
                
                self.models["doubao"] = ChatOpenAI(
                    base_url=ARK_BASE_URL,
                    model=ARK_MODEL,
                    api_key=ARK_API_KEY,
                    temperature=0.7,
                    max_tokens=2048,
                    streaming=True,
                    timeout=30,
                )
                print("豆包模型初始化成功")
                print(f"[ModelRouter] 模型对象: {self.models['doubao']}")
            except Exception as e:
                print(f"初始化豆包模型失败: {e}")
                print(f"[ModelRouter] 错误类型: {type(e).__name__}")
                print(f"[ModelRouter] 错误信息: {str(e)}")
                import traceback
                print(f"[ModelRouter] 堆栈跟踪:\n{traceback.format_exc()}")
                print("将使用本地模型作为降级选项")
        else:
            print("豆包模型未配置，将使用本地模型")

        # 初始化本地模型（延迟加载，按需创建）
        # Ollama 模型会在调用时动态创建

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
        model_name_lower = model_name.lower()

        # 豆包模型
        if model_name_lower.startswith("doubao"):
            logger.info(f"[ModelRouter] 检测到豆包模型请求")
            logger.info(f"[ModelRouter] 当前已加载的模型: {list(self.models.keys())}")
            if "doubao" not in self.models:
                logger.warning(f"[ModelRouter] 豆包模型未初始化，自动降级使用本地模型 llama3.1")
                print("警告: 豆包模型未初始化，自动降级使用本地模型 llama3.1")
                return ChatOllama(
                    model="llama3.1",
                    base_url=OLLAMA_BASE_URL,
                    temperature=0.7,
                )
            logger.info(f"[ModelRouter] 返回豆包模型: {self.models['doubao']}")
            return self.models["doubao"]

        # 本地 Ollama 模型
        if model_name_lower.startswith("ollama") or model_name_lower in [
            "llama3.1",
            "deepseek-r1:7b",
            "deepseek-r1",
            "llava"
        ]:
            return ChatOllama(
                model=model_name,
                base_url=OLLAMA_BASE_URL,
                temperature=0.7,
                streaming=True,
            )

        raise ValueError(f"不支持的模型: {model_name}")

    def create_ollama_model(
        self,
        model_name: str,
        temperature: float = 0.7
    ) -> ChatOllama:
        """
        创建 Ollama 模型实例

        Args:
            model_name: 模型名称
            temperature: 温度参数

        Returns:
            ChatOllama 实例
        """
        return ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=temperature,
        )

    def is_model_available(self, model_name: str) -> bool:
        """
        检查模型是否可用

        Args:
            model_name: 模型名称

        Returns:
            是否可用
        """
        model_name_lower = model_name.lower()

        # 豆包模型
        if model_name_lower.startswith("doubao"):
            return "doubao" in self.models

        # 本地模型总是返回 True（实际可用性需要调用时检测）
        return True

    def list_available_models(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有可用模型

        Returns:
            模型列表
        """
        models = {}

        # 豆包模型
        if "doubao" in self.models:
            models["doubao"] = {
                "name": "doubao",
                "display_name": "豆包 (火山引擎)",
                "type": "cloud",
                "has_reasoning": False,
                "available": True
            }

        # 本地模型
        local_models = [
            {"name": "llama3.1", "display_name": "Llama 3.1", "has_reasoning": False},
            {"name": "deepseek-r1:7b", "display_name": "DeepSeek R1 7B", "has_reasoning": True},
            {"name": "llava", "display_name": "LLaVA", "has_reasoning": False},
        ]

        for model in local_models:
            models[model["name"]] = {
                "name": model["name"],
                "display_name": model["display_name"],
                "type": "local",
                "has_reasoning": model["has_reasoning"],
                "available": True  # 需要实际检测
            }

        return models

    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        获取模型配置信息

        Args:
            model_name: 模型名称

        Returns:
            模型配置字典
        """
        model_name_lower = model_name.lower()
        print(f"[ModelConfig] 获取配置, 模型名: {model_name}, 小写: {model_name_lower}")

        # 豆包模型配置
        if model_name_lower.startswith("doubao"):
            print(f"[ModelConfig] 匹配到豆包")
            return {
                "supports_reasoning": False,
                "type": "cloud",
                "name": "doubao"
            }

        # DeepSeek R1 支持推理
        if "deepseek" in model_name_lower:
            print(f"[ModelConfig] 匹配到 DeepSeek")
            return {
                "supports_reasoning": True,
                "type": "local",
                "name": model_name
            }

        # Llama 3.1 不支持推理
        if "llama" in model_name_lower:
            return {
                "supports_reasoning": False,
                "type": "local",
                "name": model_name
            }

        # LLaVA 不支持推理
        if "llava" in model_name_lower:
            return {
                "supports_reasoning": False,
                "type": "local",
                "name": model_name
            }

        # 默认配置
        return {
            "supports_reasoning": False,
            "type": "unknown",
            "name": model_name
        }


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