"""
内存管理 - 管理会话状态和内存
参考 Claude Code 的会话管理机制
"""
import logging
import time
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """会话状态"""
    ACTIVE = "active"      # 正在处理
    IDLE = "idle"          # 空闲等待
    COMPLETED = "completed" # 已完成
    ABANDONED = "abandoned" # 被遗弃（超时未响应）


@dataclass
class SessionInfo:
    """会话信息"""
    conversation_id: int
    state: SessionState = SessionState.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    total_tokens: int = 0
    user_id: Optional[int] = None
    model_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_idle(self, idle_threshold_seconds: int = 3600) -> bool:
        """检查是否空闲"""
        return (datetime.now() - self.last_active).total_seconds() > idle_threshold_seconds

    def update_activity(self):
        """更新活动状态"""
        self.last_active = datetime.now()
        if self.state == SessionState.IDLE:
            self.state = SessionState.ACTIVE


class MemoryManager:
    """
    内存管理器

    管理会话状态，防止内存泄漏，清理不活跃会话
    """

    # 会话超时时间（秒）
    SESSION_TIMEOUT = 3600  # 1小时

    # 清理间隔（秒）
    CLEANUP_INTERVAL = 300  # 5分钟

    # 最大活跃会话数
    MAX_ACTIVE_SESSIONS = 100

    def __init__(self):
        self._sessions: Dict[int, SessionInfo] = {}
        self._active_conversation_id: Optional[int] = None
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()

    def create_session(
        self,
        conversation_id: int,
        user_id: int = None,
        model_name: str = None
    ) -> SessionInfo:
        """
        创建会话

        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            model_name: 模型名称

        Returns:
            会话信息
        """
        with self._lock:
            # 如果会话已存在，返回现有会话
            if conversation_id in self._sessions:
                session = self._sessions[conversation_id]
                session.update_activity()
                return session

            # 检查是否达到最大会话数
            if len(self._sessions) >= self.MAX_ACTIVE_SESSIONS:
                self._cleanup_idle_sessions()

            session = SessionInfo(
                conversation_id=conversation_id,
                user_id=user_id,
                model_name=model_name,
                state=SessionState.ACTIVE
            )
            self._sessions[conversation_id] = session
            logger.info(f"[MemoryManager] 创建会话 {conversation_id}")

            return session

    def get_session(self, conversation_id: int) -> Optional[SessionInfo]:
        """获取会话"""
        with self._lock:
            return self._sessions.get(conversation_id)

    def update_session_activity(self, conversation_id: int):
        """更新会话活动状态"""
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session:
                session.update_activity()
                self._active_conversation_id = conversation_id

    def set_session_state(self, conversation_id: int, state: SessionState):
        """设置会话状态"""
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session:
                session.state = state
                logger.info(f"[MemoryManager] 会话 {conversation_id} 状态: {state.value}")

    def increment_message_count(self, conversation_id: int):
        """增加消息计数"""
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session:
                session.message_count += 1
                session.last_active = datetime.now()

    def update_tokens(self, conversation_id: int, tokens: int):
        """更新 Token 计数"""
        with self._lock:
            session = self._sessions.get(conversation_id)
            if session:
                session.total_tokens = tokens

    def delete_session(self, conversation_id: int):
        """删除会话"""
        with self._lock:
            if conversation_id in self._sessions:
                del self._sessions[conversation_id]
                logger.info(f"[MemoryManager] 删除会话 {conversation_id}")

            if self._active_conversation_id == conversation_id:
                self._active_conversation_id = None

    def _cleanup_idle_sessions(self, idle_threshold_seconds: int = None):
        """清理空闲会话"""
        threshold = idle_threshold_seconds or self.SESSION_TIMEOUT
        idle_sessions = []

        for conv_id, session in self._sessions.items():
            if session.is_idle(threshold):
                idle_sessions.append(conv_id)

        for conv_id in idle_sessions:
            self._sessions[conv_id].state = SessionState.ABANDONED
            logger.info(f"[MemoryManager] 标记空闲会话 {conv_id} 为已遗弃")

        return len(idle_sessions)

    def get_active_sessions(self) -> list:
        """获取所有活跃会话"""
        with self._lock:
            return [
                {
                    "conversation_id": s.conversation_id,
                    "state": s.state.value,
                    "message_count": s.message_count,
                    "total_tokens": s.total_tokens,
                    "last_active": s.last_active.isoformat(),
                    "idle_seconds": (datetime.now() - s.last_active).total_seconds()
                }
                for s in self._sessions.values()
                if s.state in (SessionState.ACTIVE, SessionState.IDLE)
            ]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total_sessions = len(self._sessions)
            active_count = sum(1 for s in self._sessions.values() if s.state == SessionState.ACTIVE)
            idle_count = sum(1 for s in self._sessions.values() if s.state == SessionState.IDLE)
            abandoned_count = sum(1 for s in self._sessions.values() if s.state == SessionState.ABANDONED)

            total_tokens = sum(s.total_tokens for s in self._sessions.values())
            total_messages = sum(s.message_count for s in self._sessions.values())

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_count,
                "idle_sessions": idle_count,
                "abandoned_sessions": abandoned_count,
                "total_tokens": total_tokens,
                "total_messages": total_messages,
                "memory_usage_mb": self._estimate_memory_usage(),
                "active_conversation_id": self._active_conversation_id
            }

    def _estimate_memory_usage(self) -> float:
        """估算内存使用（MB）"""
        # 粗略估算：每个会话约 1-5 MB
        return len(self._sessions) * 2.5

    def start_auto_cleanup(self):
        """启动自动清理线程"""
        if self._running:
            return

        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("[MemoryManager] 启动自动清理线程")

    def stop_auto_cleanup(self):
        """停止自动清理线程"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
            self._cleanup_thread = None
        logger.info("[MemoryManager] 停止自动清理线程")

    def _cleanup_loop(self):
        """清理循环"""
        while self._running:
            try:
                time.sleep(self.CLEANUP_INTERVAL)
                if not self._running:
                    break

                # 标记空闲会话
                idle_count = self._cleanup_idle_sessions()
                if idle_count > 0:
                    logger.info(f"[MemoryManager] 标记了 {idle_count} 个空闲会话")

            except Exception as e:
                logger.error(f"[MemoryManager] 清理循环错误: {e}")

    def clear_all_sessions(self):
        """清空所有会话（谨慎使用）"""
        with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            self._active_conversation_id = None
            logger.warning(f"[MemoryManager] 清空了 {count} 个会话")


# 全局内存管理器实例
memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    """获取全局内存管理器"""
    return memory_manager
