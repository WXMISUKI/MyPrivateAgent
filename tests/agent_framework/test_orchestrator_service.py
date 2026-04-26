import json
import unittest

from backend.agent_framework.adapters import InMemoryArtifactStore
from backend.services.orchestrator_service import (
    OrchestratorStreamState,
    build_done_payload,
    persist_runtime_knowledge_effect_artifact,
    persist_runtime_knowledge_artifact,
    persist_runtime_skill_artifact,
    persist_runtime_skill_effect_artifact,
    persist_tool_artifact,
    should_retry_without_tools,
)
from backend.services.runtime_learning_service import RuntimeKnowledgeContext
from backend.services.skill_runtime_service import RuntimeSkillContext


class OrchestratorServiceTests(unittest.TestCase):
    def test_persist_tool_artifact_stores_schema_metadata(self):
        store = InMemoryArtifactStore()
        event = {
            "name": "search",
            "result": "关于'OpenAI'的信息：一家人工智能公司。",
            "tool_call_id": "call_1",
            "tool_spec": {"name": "search"},
            "tool_execution": {
                "cache_hit": True,
                "duration_ms": 0.42,
                "result_source": "runtime_cache",
                "status": "cached",
            },
            "render_mode": "structured_card",
            "card_schema": "search_summary.v1",
            "card": {
                "kind": "search_summary",
                "schema": "search_summary.v1",
                "source": "knowledge_base",
                "source_label": "知识库",
                "source_count": 1,
            },
        }

        persist_tool_artifact(
            artifact_store=store,
            conversation_id=7,
            event_data=event,
            selected_model="doubao",
        )

        artifacts = store.list_artifacts(conversation_id=7, kind="tool_result")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].card_schema, "search_summary.v1")
        self.assertEqual(artifacts[0].metadata["source_label"], "知识库")
        self.assertTrue(artifacts[0].metadata["cache_hit"])
        self.assertEqual(artifacts[0].metadata["result_source"], "runtime_cache")

    def test_build_done_payload_includes_rendering_metadata(self):
        payload = build_done_payload(
            chunk_data={
                "render_mode": "structured_card",
                "card_schema": "weather.v1",
                "card": {"schema": "weather.v1", "kind": "weather"},
                "tool_name": "search",
                "tool_call_id": "call_weather",
                "tool_execution": {
                    "cache_hit": False,
                    "duration_ms": 88.6,
                    "result_source": "tool",
                    "status": "ok",
                },
                "cache_hit": False,
                "duration_ms": 88.6,
                "result_source": "tool",
            },
            full_answer="天气查询结果",
            reasoning_content="推理",
            context_stats={
                "total_tokens": 123,
                "message_count": 4,
                "compression_count": 1,
            },
        )

        data = json.loads(payload)
        self.assertEqual(data["content"], "天气查询结果")
        self.assertEqual(data["card_schema"], "weather.v1")
        self.assertEqual(data["context_stats"]["tokens"], 123)
        self.assertEqual(data["tool_name"], "search")
        self.assertEqual(data["tool_execution"]["result_source"], "tool")

    def test_persist_runtime_knowledge_artifact_stores_snapshot(self):
        store = InMemoryArtifactStore()
        knowledge_context = RuntimeKnowledgeContext(
            system_prompt="请遵循以下运行时系统指导：\n- [behavior:demo] 优先返回确定性结果。",
            prompt_keys=["demo"],
            practice_ids=["BP-001"],
            prompt_count=1,
            practice_count=1,
            metadata={"source": "runtime_learning_service"},
        )

        persist_runtime_knowledge_artifact(
            artifact_store=store,
            conversation_id=9,
            knowledge_context=knowledge_context,
            selected_model="doubao",
        )

        artifacts = store.list_artifacts(conversation_id=9, kind="runtime_knowledge")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].metadata["prompt_count"], 1)
        self.assertEqual(artifacts[0].metadata["practice_ids"], ["BP-001"])

    def test_persist_runtime_knowledge_effect_artifact_tracks_selected_items(self):
        store = InMemoryArtifactStore()
        knowledge_context = RuntimeKnowledgeContext(
            system_prompt="请严格遵循以下运行时规则：\n- [tool_usage:demo] 天气查询只调用一次。",
            metadata={
                "scope": "chat",
                "selected_items": [
                    {"type": "prompt", "id": "demo", "level": "enforced", "scope": "chat"}
                ],
                "prompt_keys": ["demo"],
                "practice_ids": [],
            },
        )

        persist_runtime_knowledge_effect_artifact(
            artifact_store=store,
            conversation_id=11,
            knowledge_context=knowledge_context,
            selected_model="doubao",
            stop_reason="tool_passthrough",
            output_text="天气查询结果（舟山）",
        )

        artifacts = store.list_artifacts(conversation_id=11, kind="runtime_knowledge_effect")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].metadata["scope"], "chat")
        self.assertEqual(artifacts[0].metadata["selected_count"], 1)
        self.assertEqual(artifacts[0].metadata["stop_reason"], "tool_passthrough")

    def test_should_retry_without_tools_matches_known_error(self):
        self.assertTrue(should_retry_without_tools("Model does not support tools"))
        self.assertTrue(should_retry_without_tools("status code: 400"))
        self.assertFalse(should_retry_without_tools("timeout"))

    def test_persist_runtime_skill_artifact_stores_snapshot(self):
        store = InMemoryArtifactStore()
        skill_context = RuntimeSkillContext(
            system_prompt="请将以下运行时 Skills 作为当前任务的可执行约束与参考。",
            metadata={
                "source": "skill_runtime_service",
                "selected_skill_ids": [1],
                "selected_skill_names": ["Frontend UI Review"],
                "selected_count": 1,
            },
        )

        persist_runtime_skill_artifact(
            artifact_store=store,
            conversation_id=13,
            skill_context=skill_context,
            selected_model="doubao",
        )

        artifacts = store.list_artifacts(conversation_id=13, kind="runtime_skill")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].metadata["selected_count"], 1)
        self.assertEqual(artifacts[0].metadata["selected_skill_names"], ["Frontend UI Review"])

    def test_persist_runtime_skill_effect_artifact_tracks_selected_skills(self):
        store = InMemoryArtifactStore()
        skill_context = RuntimeSkillContext(
            system_prompt="runtime skill",
            metadata={
                "selected_items": [{"type": "skill", "id": 1, "name": "Frontend UI Review"}],
                "selected_skill_ids": [1],
                "selected_skill_names": ["Frontend UI Review"],
                "agent_role": "frontend",
            },
        )

        persist_runtime_skill_effect_artifact(
            artifact_store=store,
            conversation_id=15,
            skill_context=skill_context,
            selected_model="doubao",
            stop_reason="completed",
            output_text="前端页面已完成优化",
        )

        artifacts = store.list_artifacts(conversation_id=15, kind="runtime_skill_effect")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].metadata["selected_count"], 1)
        self.assertEqual(artifacts[0].metadata["agent_role"], "frontend")

    def test_stream_state_defaults_are_empty(self):
        state = OrchestratorStreamState()
        self.assertEqual(state.full_content, "")
        self.assertEqual(state.last_content_chunk, "")
        self.assertEqual(state.last_reasoning, "")


if __name__ == "__main__":
    unittest.main()
