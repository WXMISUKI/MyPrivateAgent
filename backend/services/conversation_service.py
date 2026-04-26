"""Conversation service helpers for route-level CRUD, search, and feedback."""

from __future__ import annotations

import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session


class ConversationService:
    """Thin service around conversation persistence and search concerns."""

    def __init__(self, db: Session):
        self.db = db

    def _models(self):
        try:
            from models import Conversation, Message
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import Conversation, Message
        return Conversation, Message

    def _feedback_models(self):
        try:
            from models import ArtifactRecord, Learning, LearningCategory, LearningStatus, MessageFeedbackRecord, Priority
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.models import (
                ArtifactRecord,
                Learning,
                LearningCategory,
                LearningStatus,
                MessageFeedbackRecord,
                Priority,
            )
        return ArtifactRecord, Learning, LearningCategory, LearningStatus, MessageFeedbackRecord, Priority

    def list_user_conversations(self, user_id: int) -> List[Any]:
        Conversation, _ = self._models()
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).all()

    def get_owned_conversation(self, conversation_id: int, user_id: int) -> Optional[Any]:
        Conversation, _ = self._models()
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        ).first()

    def search_conversations(self, *, user_id: int, query: str) -> List[Any]:
        Conversation, Message = self._models()
        search_term = f"%{query}%"

        title_matches = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.title.ilike(search_term),
        ).all()

        message_matches = self.db.query(Conversation).join(Message).filter(
            Conversation.user_id == user_id,
            Message.content.ilike(search_term),
        ).distinct().all()

        result = {conversation.id: conversation for conversation in title_matches + message_matches}
        return list(result.values())

    def search_messages(self, *, user_id: int, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        Conversation, Message = self._models()
        search_term = f"%{query}%"

        messages = self.db.query(Message).join(Conversation).filter(
            Conversation.user_id == user_id,
            Message.content.ilike(search_term),
        ).order_by(Message.created_at.desc()).limit(limit).all()

        return [
            {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "role": message.role,
                "content": message.content[:500] if len(message.content) > 500 else message.content,
                "created_at": message.created_at,
                "conversation_title": message.conversation.title if message.conversation else None,
            }
            for message in messages
        ]

    def create_conversation(self, *, user_id: int, title: str, model_name: str) -> Any:
        Conversation, _ = self._models()
        conversation = Conversation(
            user_id=user_id,
            title=title,
            model_name=model_name,
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def update_conversation(
        self,
        *,
        conversation: Any,
        title: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Any:
        if title is not None:
            conversation.title = title
        if model_name is not None:
            conversation.model_name = model_name

        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation: Any) -> None:
        self.db.delete(conversation)
        self.db.commit()

    def _build_learning_id(self, prefix: str = "LRN") -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
        return f"{prefix}-{date_str}-{random_str}"

    def _get_latest_assistant_message(self, conversation_id: int) -> Optional[Any]:
        _, Message = self._models()
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "assistant",
        ).order_by(Message.created_at.desc()).first()

    def _get_latest_runtime_effect(self, conversation_id: int) -> Optional[Any]:
        ArtifactRecord, _, _, _, _, _ = self._feedback_models()
        return self.db.query(ArtifactRecord).filter(
            ArtifactRecord.conversation_id == conversation_id,
            ArtifactRecord.kind == "runtime_knowledge_effect",
        ).order_by(ArtifactRecord.created_at.desc()).first()

    def create_feedback(
        self,
        *,
        conversation: Any,
        user_id: int,
        feedback_type: str,
        score: Optional[int] = None,
        comment: Optional[str] = None,
        message_id: Optional[int] = None,
        selected_reasons: Optional[List[str]] = None,
    ) -> Any:
        _, Message = self._models()
        ArtifactRecord, Learning, LearningCategory, LearningStatus, MessageFeedbackRecord, Priority = self._feedback_models()

        assistant_message = None
        if message_id is not None:
            assistant_message = self.db.query(Message).filter(
                Message.id == message_id,
                Message.conversation_id == conversation.id,
                Message.role == "assistant",
            ).first()
        else:
            assistant_message = self._get_latest_assistant_message(conversation.id)

        if assistant_message is None:
            raise ValueError("未找到可关联的助手消息，请在助手回复完成后再提交反馈。")

        runtime_effect = self._get_latest_runtime_effect(conversation.id)
        runtime_metadata = dict(getattr(runtime_effect, "artifact_metadata", {}) or {})
        normalized_comment = comment.strip() if isinstance(comment, str) and comment.strip() else None
        normalized_selected_reasons = [str(item) for item in (selected_reasons or []) if str(item).strip()]
        feedback_metadata = {
            "selected_count": runtime_metadata.get("selected_count", 0),
            "practice_ids": runtime_metadata.get("practice_ids", []),
            "prompt_keys": runtime_metadata.get("prompt_keys", []),
            "selected_reasons": normalized_selected_reasons,
        }

        existing_feedback = self.db.query(MessageFeedbackRecord).filter(
            MessageFeedbackRecord.conversation_id == conversation.id,
            MessageFeedbackRecord.message_id == assistant_message.id,
            MessageFeedbackRecord.user_id == user_id,
        ).first()

        feedback = existing_feedback
        if feedback is None:
            feedback = MessageFeedbackRecord(
                conversation_id=conversation.id,
                message_id=assistant_message.id,
                user_id=user_id,
            )
            self.db.add(feedback)

        feedback.feedback_type = feedback_type
        feedback.score = score
        feedback.comment = normalized_comment
        feedback.runtime_artifact_id = getattr(runtime_effect, "artifact_id", None)
        feedback.runtime_scope = runtime_metadata.get("scope")
        feedback.selected_items = list(runtime_metadata.get("selected_items", []) or [])
        feedback.stop_reason = runtime_metadata.get("stop_reason")
        feedback.feedback_metadata = feedback_metadata

        should_create_learning = feedback_type == "negative" and not getattr(feedback, "created_learning_id", None)
        if should_create_learning:
            assistant_preview = getattr(assistant_message, "content", "") or ""
            learning = Learning(
                learning_id=self._build_learning_id(),
                category=LearningCategory.CORRECTION,
                priority=Priority.HIGH if score is not None and score <= 2 else Priority.MEDIUM,
                status=LearningStatus.PENDING,
                area=None,
                summary=f"用户对会话 {conversation.id} 的助手回复给出负反馈",
                details=(
                    f"反馈说明: {feedback.comment or '未提供'}\n"
                    f"助手回复摘录: {assistant_preview[:500]}"
                ),
                suggested_action="检查本次运行命中的 runtime knowledge 与工具输出，确认是否需要回滚或调整知识注入。",
                source="user_feedback",
                related_files=[],
                tags=["user-feedback", "runtime-evaluation", f"scope:{feedback.runtime_scope or 'chat'}"],
                pattern_key=f"user_feedback:conversation:{conversation.id}",
                recurrence_count=1,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                see_also=[feedback.runtime_artifact_id] if feedback.runtime_artifact_id else [],
            )
            self.db.add(learning)
            self.db.flush()
            feedback.created_learning_id = learning.learning_id

        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def list_feedback(self, *, conversation_id: int, limit: int = 50) -> List[Any]:
        _, _, _, _, MessageFeedbackRecord, _ = self._feedback_models()
        return self.db.query(MessageFeedbackRecord).filter(
            MessageFeedbackRecord.conversation_id == conversation_id
        ).order_by(MessageFeedbackRecord.created_at.desc()).limit(limit).all()

    def get_feedback_analytics(
        self,
        *,
        user_id: int,
        days: int = 30,
        min_samples_for_candidate: int = 2,
    ) -> Dict[str, Any]:
        Conversation, _ = self._models()
        _, _, _, _, MessageFeedbackRecord, _ = self._feedback_models()

        safe_days = max(1, min(int(days), 365))
        since = datetime.now() - timedelta(days=safe_days)

        records = self.db.query(MessageFeedbackRecord).join(
            Conversation,
            Conversation.id == MessageFeedbackRecord.conversation_id,
        ).filter(
            Conversation.user_id == user_id,
            MessageFeedbackRecord.created_at >= since,
        ).all()

        positive_count = 0
        negative_count = 0
        neutral_count = 0

        scope_stats: Dict[str, Dict[str, int]] = {}
        prompt_stats: Dict[str, Dict[str, int]] = {}
        practice_stats: Dict[str, Dict[str, int]] = {}

        def _update_stat(container: Dict[str, Dict[str, int]], key: str, is_negative: bool):
            stat = container.setdefault(key, {"total": 0, "negative": 0})
            stat["total"] += 1
            if is_negative:
                stat["negative"] += 1

        for record in records:
            feedback_value = (record.feedback_type or "").lower()
            is_negative = feedback_value == "negative"
            if feedback_value == "positive":
                positive_count += 1
            elif feedback_value == "negative":
                negative_count += 1
            else:
                neutral_count += 1

            _update_stat(scope_stats, record.runtime_scope or "unknown", is_negative)
            metadata = dict(record.feedback_metadata or {})

            for prompt_key in metadata.get("prompt_keys", []) or []:
                key = str(prompt_key).strip()
                if key:
                    _update_stat(prompt_stats, key, is_negative)

            for practice_id in metadata.get("practice_ids", []) or []:
                key = str(practice_id).strip()
                if key:
                    _update_stat(practice_stats, key, is_negative)

        def _serialize_stats(container: Dict[str, Dict[str, int]]) -> List[Dict[str, Any]]:
            rows: List[Dict[str, Any]] = []
            for key, stat in container.items():
                total = stat["total"]
                negative = stat["negative"]
                rows.append(
                    {
                        "key": key,
                        "total": total,
                        "negative": negative,
                        "negative_rate": round((negative / total), 4) if total > 0 else 0.0,
                    }
                )
            rows.sort(key=lambda row: (-row["negative_rate"], -row["total"], row["key"]))
            return rows

        prompt_rows = _serialize_stats(prompt_stats)
        practice_rows = _serialize_stats(practice_stats)
        scope_rows = _serialize_stats(scope_stats)

        rollback_candidates: List[Dict[str, Any]] = []
        for row in prompt_rows:
            if row["total"] >= min_samples_for_candidate and row["negative_rate"] >= 0.6:
                rollback_candidates.append({"kind": "prompt", **row})
        for row in practice_rows:
            if row["total"] >= min_samples_for_candidate and row["negative_rate"] >= 0.6:
                rollback_candidates.append({"kind": "practice", **row})
        rollback_candidates.sort(key=lambda row: (-row["negative_rate"], -row["negative"], -row["total"], row["kind"], row["key"]))

        total_feedback = len(records)
        negative_rate = round((negative_count / total_feedback), 4) if total_feedback > 0 else 0.0
        return {
            "window_days": safe_days,
            "generated_at": datetime.now(),
            "total_feedback": total_feedback,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "negative_rate": negative_rate,
            "scope_stats": scope_rows,
            "prompt_stats": prompt_rows,
            "practice_stats": practice_rows,
            "rollback_candidates": rollback_candidates,
        }
