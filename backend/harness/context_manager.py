"""
上下文管理器 - 管理对话上下文
参考 Claude Code 的智能上下文管理
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息"""
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    token_count: int = 0


class ContextWindow:
    """
    上下文窗口管理

    管理对话消息的生命周期，包括：
    - 消息添加
    - Token 计数
    - 自动压缩/总结
    """

    # 不同模型的上下文限制
    CONTEXT_LIMITS = {
        "doubao": 4096,
        "llama3.1": 8192,
        "llama3": 8192,
        "deepseek-r1:7b": 8192,
        "deepseek-r1": 32768,
        "llava": 4096,
        "default": 4096
    }

    # 压缩阈值（达到此比例时触发压缩）
    COMPRESSION_THRESHOLD = 0.8

    # 最大保留消息数
    MAX_MESSAGES = 100

    def __init__(
        self,
        model_name: str = "default",
        max_tokens: int = None,
        compression_threshold: float = None
    ):
        self.model_name = model_name
        self.max_tokens = max_tokens or self.CONTEXT_LIMITS.get(
            model_name.lower(),
            self.CONTEXT_LIMITS["default"]
        )
        self.compression_threshold = compression_threshold or self.COMPRESSION_THRESHOLD
        self.messages: List[Message] = []
        self.total_tokens = 0
        self.compression_count = 0

    def add_message(self, role: str, content: str) -> Message:
        """
        添加消息

        Args:
            role: 角色（user/assistant/system）
            content: 内容

        Returns:
            创建的消息
        """
        token_count = self.estimate_tokens(content)

        message = Message(
            role=role,
            content=content,
            token_count=token_count
        )

        self.messages.append(message)
        self.total_tokens += token_count

        # 检查是否需要压缩
        if self.should_compress():
            self.compress()

        return message

    def add_user_message(self, content: str) -> Message:
        """添加用户消息"""
        return self.add_message("user", content)

    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息"""
        return self.add_message("assistant", content)

    def add_system_message(self, content: str) -> Message:
        """添加系统消息"""
        return self.add_message("system", content)

    def get_messages(self) -> List[Dict[str, str]]:
        """
        获取格式化的消息列表（用于模型输入）

        Returns:
            消息字典列表
        """
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages
        ]

    def should_compress(self) -> bool:
        """检查是否需要压缩"""
        return self.total_tokens >= self.max_tokens * self.compression_threshold

    def estimate_tokens(self, text: str) -> int:
        """
        估算 Token 数量

        简单的估算：中文约 2 tokens/字符，英文约 4 tokens/词
        """
        # 简单估算：平均每个汉字约 1.5 tokens，每个英文单词约 1.3 tokens
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if w.isascii()])
        other_chars = len(text) - chinese_chars - len(''.join([w for w in text.split() if w.isascii()]))

        return int(chinese_chars * 1.5 + english_words * 1.3 + other_chars * 1)

    def compress(self, preserve_recent: int = 10) -> bool:
        """
        压缩上下文

        策略：
        1. 保留最近的消息（用户最后的问题等）
        2. 总结早期对话的核心内容
        3. 删除中间消息

        Args:
            preserve_recent: 保留最近多少条消息

        Returns:
            是否成功压缩
        """
        if len(self.messages) <= preserve_recent:
            logger.info("[ContextWindow] 消息数量太少，无需压缩")
            return False

        self.compression_count += 1
        logger.info(f"[ContextWindow] 开始压缩上下文 (第 {self.compression_count} 次)")

        # 保留系统消息（如果有）
        system_messages = [m for m in self.messages if m.role == "system"]

        # 保留最近的消息
        recent_messages = self.messages[-preserve_recent:]

        # 总结早期消息的核心内容
        early_messages = self.messages[:-preserve_recent]
        summary = self._summarize_messages(early_messages)

        # 清空并重建
        self.messages = system_messages.copy()

        if summary:
            self.add_system_message(f"[早期对话摘要] {summary}")

        self.messages.extend(recent_messages)

        # 重新计算 token
        self.total_tokens = sum(m.token_count for m in self.messages)

        logger.info(f"[ContextWindow] 压缩完成，当前消息数: {len(self.messages)}, Token: {self.total_tokens}")
        return True

    def _summarize_messages(self, messages: List[Message]) -> str:
        """
        总结消息列表的核心内容

        Args:
            messages: 要总结的消息

        Returns:
            总结文本
        """
        if not messages:
            return ""

        # 简单总结：提取关键信息
        user_messages = [m.content for m in messages if m.role == "user"]
        assistant_messages = [m.content for m in messages if m.role == "assistant"]

        summary_parts = []

        if user_messages:
            # 取第一条和最后一条用户消息作为关键点
            key_topics = f"用户询问了 {len(user_messages)} 个问题"
            if user_messages[0]:
                key_topics += f"，从 '{user_messages[0][:30]}...' 开始"
            if len(user_messages) > 1 and user_messages[-1]:
                key_topics += f" 到 '{user_messages[-1][:30]}...' 结束"
            summary_parts.append(key_topics)

        if assistant_messages:
            # 统计助手回答的主题
            summary_parts.append(f"助手进行了 {len(assistant_messages)} 次回复")

        return "; ".join(summary_parts)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "message_count": len(self.messages),
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": self.total_tokens / self.max_tokens if self.max_tokens > 0 else 0,
            "compression_count": self.compression_count,
            "model": self.model_name
        }

    def clear(self):
        """清空上下文"""
        self.messages.clear()
        self.total_tokens = 0

    def is_empty(self) -> bool:
        """是否为空"""
        return len(self.messages) == 0


class ContextManager:
    """
    上下文管理器

    管理多个会话的上下文
    """

    def __init__(self):
        self.contexts: Dict[int, ContextWindow] = {}  # conversation_id -> ContextWindow
        self.default_model = "deepseek-r1:7b"

    def get_context(self, conversation_id: int, model_name: str = None) -> ContextWindow:
        """
        获取或创建上下文窗口

        Args:
            conversation_id: 会话ID
            model_name: 模型名称

        Returns:
            上下文窗口
        """
        if conversation_id not in self.contexts:
            model = model_name or self.default_model
            self.contexts[conversation_id] = ContextWindow(model_name=model)
            logger.info(f"[ContextManager] 为会话 {conversation_id} 创建新上下文 (模型: {model})")

        return self.contexts[conversation_id]

    def delete_context(self, conversation_id: int):
        """删除上下文"""
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
            logger.info(f"[ContextManager] 删除会话 {conversation_id} 的上下文")

    def get_stats(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """获取会话的上下文统计"""
        context = self.contexts.get(conversation_id)
        if context:
            return context.get_stats()
        return None


# 全局上下文管理器实例
global_context_manager = ContextManager()


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器"""
    return global_context_manager
