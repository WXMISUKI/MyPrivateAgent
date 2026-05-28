"""Durable compact summaries for main chat conversations."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session


class ChatContextCompactService:
    SUMMARY_EXCERPT_CHARS = 180

    def __init__(self, db: Session):
        self.db = db
        self._ensure_table()

    def compact(
        self,
        *,
        conversation_id: int,
        trigger: str = "manual",
        instructions: Optional[str] = None,
    ) -> Any:
        ConversationSummary = self._summary_model()
        messages = self._load_messages(conversation_id)
        summary_text = self._build_summary(messages=messages, instructions=instructions)
        last_message_id = getattr(messages[-1], "id", None) if messages else None
        record = ConversationSummary(
            conversation_id=conversation_id,
            summary=summary_text,
            message_count=len(messages),
            last_message_id=last_message_id,
            trigger=trigger,
            instructions=(instructions or None),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def latest_summary(self, *, conversation_id: int) -> Optional[Any]:
        ConversationSummary = self._summary_model()
        return (
            self.db.query(ConversationSummary)
            .filter(ConversationSummary.conversation_id == conversation_id)
            .order_by(ConversationSummary.created_at.desc(), ConversationSummary.id.desc())
            .first()
        )

    def messages_after_summary(self, *, conversation_id: int, summary: Optional[Any]) -> list[Any]:
        Message = self._message_model()
        query = self.db.query(Message).filter(Message.conversation_id == conversation_id)
        last_message_id = getattr(summary, "last_message_id", None) if summary is not None else None
        if last_message_id is not None:
            query = query.filter(Message.id > last_message_id)
        return query.order_by(Message.created_at.asc(), Message.id.asc()).all()

    def _load_messages(self, conversation_id: int) -> list[Any]:
        Message = self._message_model()
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc(), Message.id.asc())
            .all()
        )

    def _build_summary(self, *, messages: list[Any], instructions: Optional[str]) -> str:
        if not messages:
            base = "当前会话暂无可压缩的历史消息。"
        else:
            user_count = sum(1 for message in messages if str(getattr(message, "role", "")).lower() == "user")
            assistant_count = sum(1 for message in messages if str(getattr(message, "role", "")).lower() == "assistant")
            first_user = self._first_excerpt(messages, "user")
            latest_user = self._last_excerpt(messages, "user")
            latest_assistant = self._last_excerpt(messages, "assistant")
            parts = [
                f"已压缩当前会话 {len(messages)} 条消息，其中用户消息 {user_count} 条、助手消息 {assistant_count} 条。",
            ]
            if first_user:
                parts.append(f"起始用户问题：{first_user}")
            if latest_user and latest_user != first_user:
                parts.append(f"最近用户问题：{latest_user}")
            if latest_assistant:
                parts.append(f"最近助手结论：{latest_assistant}")
            base = " ".join(parts)

        normalized_instructions = str(instructions or "").strip()
        if normalized_instructions:
            base += f" 压缩指令：{self._excerpt(normalized_instructions)}"
        return base

    def _first_excerpt(self, messages: list[Any], role: str) -> str:
        for message in messages:
            if str(getattr(message, "role", "")).lower() == role:
                return self._excerpt(getattr(message, "content", ""))
        return ""

    def _last_excerpt(self, messages: list[Any], role: str) -> str:
        for message in reversed(messages):
            if str(getattr(message, "role", "")).lower() == role:
                return self._excerpt(getattr(message, "content", ""))
        return ""

    def _excerpt(self, value: Any) -> str:
        text = " ".join(str(value or "").split())
        if len(text) <= self.SUMMARY_EXCERPT_CHARS:
            return text
        return text[: self.SUMMARY_EXCERPT_CHARS - 3].rstrip() + "..."

    def _ensure_table(self) -> None:
        try:
            from database import Base, engine
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.database import Base, engine

        Base.metadata.create_all(bind=engine)

    def _summary_model(self):
        try:
            from models import ConversationSummary
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import ConversationSummary
        return ConversationSummary

    def _message_model(self):
        try:
            from models import Message
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import Message
        return Message
