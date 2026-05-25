import unittest

from backend.services.main_chat_query_control_service import MainChatQueryControlService


class _StubQueryControlTimelineService:
    def __init__(self):
        self.calls = []

    def record_stage(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "trace_written": True,
            "audit_written": True,
            "conversation_id": kwargs.get("conversation_id"),
            "snapshot_ref": {"source": "query_control", "event_type": f"query_control_{kwargs.get('stage')}"},
            "dedupe_key": f"query_control:{kwargs.get('channel')}:{kwargs.get('stage')}:{kwargs.get('conversation_id')}:{kwargs.get('query_id')}",
        }


class _FailingQueryControlTimelineService:
    def record_stage(self, **_kwargs):
        raise RuntimeError("query control recorder unavailable")


class MainChatQueryControlServiceTests(unittest.TestCase):
    def test_record_query_control_events_records_mapped_main_chat_lifecycle(self):
        timeline = _StubQueryControlTimelineService()
        service = MainChatQueryControlService(query_control_timeline_service=timeline)

        result = service.record_query_control_events(
            db=object(),
            conversation_id=99,
            query_id="handoff-p10-i23",
            events=[
                {"type": "status", "status_kind": "main_chat_input_received", "content": "开始处理"},
                {"type": "reasoning", "content": "先拆解任务"},
                {"type": "content", "content": "阶段性输出"},
                {"type": "done", "content": "最终结果"},
            ],
        )

        self.assertEqual([call["stage"] for call in timeline.calls], ["input_received", "planning", "model_stream", "final_output"])
        self.assertEqual(timeline.calls[0]["channel"], "main_chat")
        self.assertEqual(timeline.calls[0]["query_id"], "handoff-p10-i23")
        self.assertEqual(timeline.calls[0]["payload"]["source_status_kind"], "main_chat_input_received")
        self.assertEqual(len(result["recordings"]), 4)

    def test_record_query_control_events_is_fail_open(self):
        service = MainChatQueryControlService(query_control_timeline_service=_FailingQueryControlTimelineService())

        result = service.record_query_control_events(
            db=object(),
            conversation_id=99,
            query_id="handoff-p10-i23",
            events=[{"type": "status", "status_kind": "main_chat_input_received", "content": "开始处理"}],
        )

        self.assertEqual(result["recordings"], [])
        self.assertEqual(result["failures"][0]["error"], "query control recorder unavailable")

    def test_record_query_control_events_returns_empty_when_query_id_missing(self):
        timeline = _StubQueryControlTimelineService()
        service = MainChatQueryControlService(query_control_timeline_service=timeline)

        result = service.record_query_control_events(
            db=object(),
            conversation_id=99,
            query_id="",
            events=[{"type": "status", "status_kind": "main_chat_input_received", "content": "开始处理"}],
        )

        self.assertEqual(result["recordings"], [])
        self.assertEqual(result["failures"], [])
        self.assertEqual(timeline.calls, [])


if __name__ == "__main__":
    unittest.main()
