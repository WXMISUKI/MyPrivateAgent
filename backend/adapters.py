"""
模型输出适配器
统一不同模型的输出格式，支持推理链（reasoning_content）的提取
"""
from typing import Optional, Any, Dict
from pydantic import BaseModel


class StandardizedResponse(BaseModel):
    """标准化响应模型"""

    model_config = {"protected_namespaces": ()}

    content: str
    reasoning_content: Optional[str] = None
    has_reasoning: bool = False
    model_name: str = ""
    raw_response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """转换为字典（用于 API 响应）"""
        result = {
            "content": self.content,
            "model": self.model_name
        }

        if self.has_reasoning and self.reasoning_content:
            result["reasoning_content"] = self.reasoning_content

        return result


class ModelOutputAdapter:
    """模型输出适配器基类"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def adapt(self, raw_response: Any) -> StandardizedResponse:
        """适配不同模型的输出为统一格式"""
        raise NotImplementedError("子类必须实现此方法")


class DeepSeekOutputAdapter(ModelOutputAdapter):
    """DeepSeek R1 输出适配器"""

    def adapt(self, raw_response: Any) -> StandardizedResponse:
        """
        适配 DeepSeek R1 输出

        DeepSeek R1 输出格式：
        {
            "choices": [{
                "delta": {
                    "content": "最终答案",
                    "reasoning_content": "推理过程"
                }
            }]
        }
        """
        content = ""
        reasoning_content = None

        # 尝试从不同结构中提取内容
        if hasattr(raw_response, 'content'):
            content = raw_response.content
        elif isinstance(raw_response, dict):
            if 'content' in raw_response:
                content = raw_response['content']
            elif 'message' in raw_response:
                content = raw_response['message'].get('content', '')

        # 提取推理内容
        if hasattr(raw_response, 'choices') and raw_response.choices:
            delta = raw_response.choices[0].delta
            if hasattr(delta, 'reasoning_content'):
                reasoning_content = delta.reasoning_content
            elif isinstance(delta, dict) and 'reasoning_content' in delta:
                reasoning_content = delta['reasoning_content']

        # 如果没有推理内容，尝试从 raw 中提取
        if reasoning_content is None and hasattr(raw_response, 'raw'):
            if hasattr(raw_response.raw, 'choices'):
                delta = raw_response.raw.choices[0].delta
                if hasattr(delta, 'reasoning_content'):
                    reasoning_content = delta.reasoning_content

        return StandardizedResponse(
            content=content,
            reasoning_content=reasoning_content,
            has_reasoning=reasoning_content is not None,
            model_name=self.model_name,
            raw_response={"raw": str(raw_response)}
        )


class DoubaoOutputAdapter(ModelOutputAdapter):
    """豆包输出适配器"""

    def adapt(self, raw_response: Any) -> StandardizedResponse:
        """
        适配豆包输出

        豆包输出格式：标准 OpenAI 格式
        """
        content = ""

        # 尝试从不同结构中提取内容
        if hasattr(raw_response, 'content'):
            content = raw_response.content
        elif isinstance(raw_response, dict):
            if 'content' in raw_response:
                content = raw_response['content']
            elif 'message' in raw_response:
                content = raw_response['message'].get('content', '')

        return StandardizedResponse(
            content=content,
            reasoning_content=None,
            has_reasoning=False,
            model_name=self.model_name,
            raw_response={"raw": str(raw_response)}
        )


class StandardOutputAdapter(ModelOutputAdapter):
    """标准模型输出适配器（Llama 3.1 等）"""

    def adapt(self, raw_response: Any) -> StandardizedResponse:
        """适配标准模型输出"""
        content = ""

        # 尝试从不同结构中提取内容
        if hasattr(raw_response, 'content'):
            content = raw_response.content
        elif isinstance(raw_response, dict):
            if 'content' in raw_response:
                content = raw_response['content']
            elif 'message' in raw_response:
                content = raw_response['message'].get('content', '')
        else:
            content = str(raw_response)

        return StandardizedResponse(
            content=content,
            reasoning_content=None,
            has_reasoning=False,
            model_name=self.model_name,
            raw_response={"raw": str(raw_response)}
        )


def get_adapter(model_name: str) -> ModelOutputAdapter:
    """
    根据模型名称获取对应的适配器

    Args:
        model_name: 模型名称

    Returns:
        对应的适配器实例
    """
    model_name_lower = model_name.lower()

    if model_name_lower.startswith("deepseek"):
        return DeepSeekOutputAdapter(model_name)
    elif model_name_lower.startswith("doubao"):
        return DoubaoOutputAdapter(model_name)
    else:
        return StandardOutputAdapter(model_name)