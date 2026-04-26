import unittest
from types import SimpleNamespace

from backend.services.conversation_service import ConversationService


class _Field:
    def ilike(self, value):
        return ("ilike", value)

    def __eq__(self, other):
        return ("eq", other)

    def __ge__(self, other):
        return ("ge", other)

    def desc(self):
        return self


class _ConversationModel:
    id = _Field()
    user_id = _Field()
    title = _Field()
    updated_at = _Field()


class _MessageModel:
    id = _Field()
    conversation_id = _Field()
    role = _Field()
    content = _Field()
    created_at = _Field()


class _ArtifactModel:
    conversation_id = _Field()
    kind = _Field()
    created_at = _Field()


class _FeedbackRecord:
    user_id = _Field()
    conversation_id = _Field()
    message_id = _Field()
    feedback_type = _Field()
    created_at = _Field()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.id = kwargs.get("id", 101)
        self.created_at = kwargs.get("created_at", "2026-04-24T00:00:00")


class _LearningRecord:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class _LearningCategory:
    CORRECTION = "correction"


class _LearningStatus:
    PENDING = "pending"


class _Priority:
    HIGH = "high"
    MEDIUM = "medium"


class _FakeQuery:
    def __init__(self, results):
        self._results = results

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def distinct(self):
        return self

    def limit(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._results)

    def first(self):
        return self._results[0] if self._results else None

    def __iter__(self):
        return iter(self._results)


class _FakeSession:
    def __init__(self, query_results=None):
        self.query_results = list(query_results or [])
        self.added = []
        self.committed = 0
        self.refreshed = 0
        self.flushed = 0
        self.deleted = []

    def query(self, *args, **kwargs):
        result = self.query_results.pop(0) if self.query_results else []
        return _FakeQuery(result)

    def add(self, item):
        self.added.append(item)

    def commit(self):
        self.committed += 1

    def refresh(self, item):
        self.refreshed += 1

    def flush(self):
        self.flushed += 1

    def delete(self, item):
        self.deleted.append(item)


class ConversationServiceTests(unittest.TestCase):
    def test_search_messages_truncates_long_content(self):
        long_content = "a" * 600
        message = SimpleNamespace(
            id=1,
            conversation_id=2,
            role="assistant",
            content=long_content,
            created_at="2026-04-23T00:00:00",
            conversation=SimpleNamespace(title="test conversation"),
        )
        service = ConversationService(_FakeSession(query_results=[[message]]))
        service._models = lambda: (_ConversationModel, _MessageModel)

        results = service.search_messages(user_id=1, query="hello")

        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]["content"]), 500)
        self.assertEqual(results[0]["conversation_title"], "test conversation")

    def test_update_conversation_commits_and_refreshes(self):
        session = _FakeSession()
        service = ConversationService(session)
        conversation = SimpleNamespace(title="old", model_name="llama3.1")

        updated = service.update_conversation(
            conversation=conversation,
            title="new title",
            model_name="doubao",
        )

        self.assertEqual(updated.title, "new title")
        self.assertEqual(updated.model_name, "doubao")
        self.assertEqual(session.committed, 1)
        self.assertEqual(session.refreshed, 1)

    def test_create_feedback_links_runtime_effect_and_creates_learning_on_negative(self):
        assistant_message = SimpleNamespace(
            id=9,
            conversation_id=7,
            role="assistant",
            content="天气查询结果（舟山）",
            created_at="2026-04-24T00:00:00",
        )
        runtime_effect = SimpleNamespace(
            artifact_id="artifact_runtime_1",
            artifact_metadata={
                "scope": "chat",
                "selected_items": [{"type": "practice", "id": "BP-001"}],
                "selected_count": 1,
                "stop_reason": "tool_passthrough",
                "practice_ids": ["BP-001"],
                "prompt_keys": ["tool_usage.weather"],
            },
            created_at="2026-04-24T00:00:01",
        )
        session = _FakeSession(query_results=[[assistant_message], [runtime_effect]])
        service = ConversationService(session)
        service._models = lambda: (_ConversationModel, _MessageModel)
        service._feedback_models = lambda: (
            _ArtifactModel,
            _LearningRecord,
            _LearningCategory,
            _LearningStatus,
            _FeedbackRecord,
            _Priority,
        )
        conversation = SimpleNamespace(id=7, user_id=1)

        feedback = service.create_feedback(
            conversation=conversation,
            user_id=1,
            feedback_type="negative",
            score=2,
            comment="回答还不够稳定",
            message_id=None,
            selected_reasons=["incorrect", "incomplete"],
        )

        self.assertEqual(feedback.runtime_artifact_id, "artifact_runtime_1")
        self.assertEqual(feedback.runtime_scope, "chat")
        self.assertEqual(len(feedback.selected_items), 1)
        self.assertTrue(feedback.created_learning_id.startswith("LRN-"))
        self.assertEqual(feedback.feedback_metadata["selected_reasons"], ["incorrect", "incomplete"])
        self.assertEqual(session.committed, 1)
        self.assertEqual(session.refreshed, 1)
        self.assertEqual(session.flushed, 1)
        self.assertEqual(len(session.added), 2)

    def test_list_feedback_returns_latest_records(self):
        record = _FeedbackRecord(
            conversation_id=3,
            feedback_type="positive",
            runtime_scope="chat",
            selected_items=[],
        )
        session = _FakeSession(query_results=[[record]])
        service = ConversationService(session)
        service._feedback_models = lambda: (
            _ArtifactModel,
            _LearningRecord,
            _LearningCategory,
            _LearningStatus,
            _FeedbackRecord,
            _Priority,
        )

        results = service.list_feedback(conversation_id=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].feedback_type, "positive")

    def test_create_feedback_upserts_existing_record(self):
        assistant_message = SimpleNamespace(
            id=18,
            conversation_id=7,
            role="assistant",
            content="原始回复",
            created_at="2026-04-24T00:00:00",
        )
        runtime_effect = SimpleNamespace(
            artifact_id="artifact_runtime_2",
            artifact_metadata={
                "scope": "chat",
                "selected_items": [],
                "selected_count": 0,
                "stop_reason": "completed",
                "practice_ids": [],
                "prompt_keys": [],
            },
            created_at="2026-04-24T00:00:01",
        )
        existing_feedback = _FeedbackRecord(
            id=777,
            conversation_id=7,
            message_id=18,
            user_id=1,
            feedback_type="negative",
            comment="之前反馈",
            created_learning_id="LRN-20260424-AAA",
            feedback_metadata={"selected_reasons": ["incorrect"]},
        )
        session = _FakeSession(query_results=[[assistant_message], [runtime_effect], [existing_feedback]])
        service = ConversationService(session)
        service._models = lambda: (_ConversationModel, _MessageModel)
        service._feedback_models = lambda: (
            _ArtifactModel,
            _LearningRecord,
            _LearningCategory,
            _LearningStatus,
            _FeedbackRecord,
            _Priority,
        )
        conversation = SimpleNamespace(id=7, user_id=1)

        feedback = service.create_feedback(
            conversation=conversation,
            user_id=1,
            feedback_type="positive",
            score=5,
            comment="更新后的反馈",
            message_id=18,
            selected_reasons=[],
        )

        self.assertEqual(feedback.id, 777)
        self.assertEqual(feedback.feedback_type, "positive")
        self.assertEqual(feedback.comment, "更新后的反馈")
        self.assertEqual(feedback.created_learning_id, "LRN-20260424-AAA")
        self.assertEqual(len(session.added), 0)
        self.assertEqual(session.flushed, 0)
        self.assertEqual(session.committed, 1)
        self.assertEqual(session.refreshed, 1)

    def test_create_feedback_raises_when_assistant_message_missing(self):
        runtime_effect = SimpleNamespace(
            artifact_id="artifact_runtime_2",
            artifact_metadata={},
            created_at="2026-04-24T00:00:01",
        )
        session = _FakeSession(query_results=[[], [runtime_effect]])
        service = ConversationService(session)
        service._models = lambda: (_ConversationModel, _MessageModel)
        service._feedback_models = lambda: (
            _ArtifactModel,
            _LearningRecord,
            _LearningCategory,
            _LearningStatus,
            _FeedbackRecord,
            _Priority,
        )
        conversation = SimpleNamespace(id=7, user_id=1)

        with self.assertRaises(ValueError):
            service.create_feedback(
                conversation=conversation,
                user_id=1,
                feedback_type="negative",
                score=1,
                comment="无可关联消息",
                message_id=None,
                selected_reasons=["other"],
            )

    def test_feedback_analytics_aggregates_scope_prompt_and_practice(self):
        feedback_records = [
            _FeedbackRecord(
                conversation_id=3,
                user_id=1,
                feedback_type="negative",
                runtime_scope="chat",
                feedback_metadata={
                    "prompt_keys": ["tool_usage.weather"],
                    "practice_ids": ["BP-001"],
                },
            ),
            _FeedbackRecord(
                conversation_id=3,
                user_id=1,
                feedback_type="negative",
                runtime_scope="chat",
                feedback_metadata={
                    "prompt_keys": ["tool_usage.weather"],
                    "practice_ids": ["BP-001"],
                },
            ),
            _FeedbackRecord(
                conversation_id=3,
                user_id=1,
                feedback_type="positive",
                runtime_scope="chat",
                feedback_metadata={
                    "prompt_keys": ["tool_usage.weather"],
                    "practice_ids": ["BP-001"],
                },
            ),
        ]
        session = _FakeSession(query_results=[feedback_records])
        service = ConversationService(session)
        service._models = lambda: (_ConversationModel, _MessageModel)
        service._feedback_models = lambda: (
            _ArtifactModel,
            _LearningRecord,
            _LearningCategory,
            _LearningStatus,
            _FeedbackRecord,
            _Priority,
        )

        analytics = service.get_feedback_analytics(user_id=1, days=30, min_samples_for_candidate=2)

        self.assertEqual(analytics["total_feedback"], 3)
        self.assertEqual(analytics["negative_count"], 2)
        self.assertAlmostEqual(analytics["negative_rate"], 0.6667, places=4)
        self.assertEqual(analytics["scope_stats"][0]["key"], "chat")
        self.assertEqual(analytics["prompt_stats"][0]["key"], "tool_usage.weather")
        self.assertEqual(analytics["practice_stats"][0]["key"], "BP-001")
        self.assertTrue(any(item["kind"] == "prompt" for item in analytics["rollback_candidates"]))
        self.assertTrue(any(item["kind"] == "practice" for item in analytics["rollback_candidates"]))


if __name__ == "__main__":
    unittest.main()
