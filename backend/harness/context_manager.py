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
    - 三层自动压缩/总结
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

    # 三层压缩阈值
    MICRO_COMPACT_THRESHOLD = 0.6   # 60% 时触发 MicroCompact
    AUTO_COMPACT_THRESHOLD = 0.8    # 80% 时触发 AutoCompact
    FULL_COMPACT_THRESHOLD = 0.95   # 95% 时触发 FullCompact

    # MicroCompact：单条消息最大 token 数
    MAX_MESSAGE_TOKENS = 2000

    # 压缩保留消息数
    PRESERVE_RECENT_MICRO = 5
    PRESERVE_RECENT_AUTO = 10
    PRESERVE_RECENT_FULL = 3

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
        self.compression_threshold = compression_threshold or self.AUTO_COMPACT_THRESHOLD
        self.messages: List[Message] = []
        self.total_tokens = 0
        self.compression_count = 0
        self.last_compression_level = None

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

        self._auto_compress()

        return message

    def _auto_compress(self):
        """自动压缩检查"""
        usage_ratio = self.total_tokens / self.max_tokens if self.max_tokens > 0 else 0

        if usage_ratio >= self.FULL_COMPACT_THRESHOLD:
            self._full_compact()
        elif usage_ratio >= self.AUTO_COMPACT_THRESHOLD:
            self._auto_compact()
        elif usage_ratio >= self.MICRO_COMPACT_THRESHOLD:
            self._micro_compact()

    def _micro_compact(self) -> bool:
        """
        层1: MicroCompact - 本地修剪过长的单条消息

        Returns:
            是否执行了压缩
        """
        if self.last_compression_level == "micro":
            return False

        self.compression_count += 1
        self.last_compression_level = "micro"
        logger.info(f"[ContextWindow] MicroCompact (第 {self.compression_count} 次)")

        compacted = False
        for msg in self.messages:
            if msg.token_count > self.MAX_MESSAGE_TOKENS:
                original_len = len(msg.content)
                msg.content = msg.content[:self.MAX_MESSAGE_TOKENS * 2] + "...[已截断]"
                msg.token_count = self.MAX_MESSAGE_TOKENS
                compacted = True
                logger.info(f"[ContextWindow] 截断消息 {msg.role}: {original_len} -> {len(msg.content)}")

        if compacted:
            self.total_tokens = sum(m.token_count for m in self.messages)

        return compacted

    def _auto_compact(self, preserve_recent: int = None) -> bool:
        """
        层2: AutoCompact - 模型摘要模式

        保留最近 N 条消息，对早期消息进行总结

        Args:
            preserve_recent: 保留最近多少条消息

        Returns:
            是否执行了压缩
        """
        preserve_recent = preserve_recent or self.PRESERVE_RECENT_AUTO

        if self.last_compression_level == "auto":
            return False

        if len(self.messages) <= preserve_recent:
            return False

        self.compression_count += 1
        self.last_compression_level = "auto"
        logger.info(f"[ContextWindow] AutoCompact (第 {self.compression_count} 次)")

        system_messages = [m for m in self.messages if m.role == "system"]
        recent_messages = self.messages[-preserve_recent:]
        early_messages = self.messages[:-preserve_recent]

        summary = self._summarize_messages(early_messages)

        self.messages = system_messages.copy()

        if summary:
            self.add_system_message(f"[早期对话摘要] {summary}")

        self.messages.extend(recent_messages)
        self.total_tokens = sum(m.token_count for m in self.messages)

        logger.info(f"[ContextWindow] 压缩完成，当前消息数: {len(self.messages)}, Token: {self.total_tokens}")
        return True

    def _full_compact(self, preserve_recent: int = None) -> bool:
        """
        层3: FullCompact - 完全压缩

        只保留最近 3 条消息

        Args:
            preserve_recent: 保留最近多少条消息

        Returns:
            是否执行了压缩
        """
        preserve_recent = preserve_recent or self.PRESERVE_RECENT_FULL

        if self.last_compression_level == "full":
            return False

        self.compression_count += 1
        self.last_compression_level = "full"
        logger.info(f"[ContextWindow] FullCompact (第 {self.compression_count} 次)")

        system_messages = [m for m in self.messages if m.role == "system"]
        recent_messages = self.messages[-preserve_recent:]

        summary = self._summarize_messages(self.messages[:-preserve_recent])

        self.messages = system_messages.copy()

        if summary:
            self.add_system_message(f"[对话摘要] {summary}")

        self.messages.extend(recent_messages)
        self.total_tokens = sum(m.token_count for m in self.messages)

        logger.info(f"[ContextWindow] 完全压缩完成，当前消息数: {len(self.messages)}, Token: {self.total_tokens}")
        return True

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
        """检查是否需要压缩（兼容方法）"""
        return self.total_tokens >= self.max_tokens * self.AUTO_COMPACT_THRESHOLD

    def estimate_tokens(self, text: str) -> int:
        """
        估算 Token 数量

        简单的估算：中文约 2 tokens/字符，英文约 4 tokens/词
        """
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if w.isascii()])
        other_chars = len(text) - chinese_chars - len(''.join([w for w in text.split() if w.isascii()]))

        return int(chinese_chars * 1.5 + english_words * 1.3 + other_chars * 1)

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

        user_messages = [m.content for m in messages if m.role == "user"]
        assistant_messages = [m.content for m in messages if m.role == "assistant"]

        summary_parts = []

        if user_messages:
            key_topics = f"用户询问了 {len(user_messages)} 个问题"
            if user_messages[0]:
                key_topics += f"，从 '{user_messages[0][:30]}...' 开始"
            if len(user_messages) > 1 and user_messages[-1]:
                key_topics += f" 到 '{user_messages[-1][:30]}...' 结束"
            summary_parts.append(key_topics)

        if assistant_messages:
            summary_parts.append(f"助手进行了 {len(assistant_messages)} 次回复")

        return "; ".join(summary_parts)

    def compress(self, preserve_recent: int = 10) -> bool:
        """兼容方法：调用 AutoCompact"""
        return self._auto_compact(preserve_recent=preserve_recent)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "message_count": len(self.messages),
            "total_tokens": self.total_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": self.total_tokens / self.max_tokens if self.max_tokens > 0 else 0,
            "compression_count": self.compression_count,
            "compression_level": self.last_compression_level or "none",
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
