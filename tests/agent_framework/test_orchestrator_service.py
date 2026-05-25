import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.agent_framework.adapters import InMemoryArtifactStore
from backend.orchestrator import SimplifiedOrchestrator
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


class _EmptyRuntimeContext:
    is_empty = True
    system_prompt = ""
    metadata = {}
    prompt_count = 0
    practice_count = 0
    prompt_keys = []
    practice_ids = []


class _ContextWindow:
    def __init__(self):
        self.assistant_messages = []

    def add_user_message(self, _message):
        return None

    def add_assistant_message(self, message):
        self.assistant_messages.append(message)

    def get_stats(self):
        return {
            "usage_ratio": 0.1,
            "total_tokens": 12,
            "message_count": 2,
            "compression_count": 0,
        }


class _ContextStore:
    def __init__(self):
        self.window = _ContextWindow()

    def get_context(self, _conversation_id, _model):
        return self.window


class _MemoryStore:
    def create_session(self, _conversation_id):
        return object()

    def update_session_activity(self, _conversation_id):
        return None

    def increment_message_count(self, _conversation_id):
        return None

    def update_tokens(self, _conversation_id, _tokens):
        return None


class _ArtifactStore:
    def create_artifact(self, **_kwargs):
        return None


class _RuntimeLearningService:
    def get_runtime_context(self, **_kwargs):
        return _EmptyRuntimeContext()


class _SkillRuntimeService:
    def get_runtime_context(self, **_kwargs):
        return _EmptyRuntimeContext()


class _McpRuntimeService:
    def sync_registry_tools(self, _tool_registry):
        return None

    def validate_required_capabilities(self, _capabilities):
        return {"ready": True, "missing_capabilities": [], "unavailable_capabilities": []}


class _SubagentRuntimeService:
    def normalize_context(self, _execution_context):
        return None


class _CapabilityProfileService:
    def build_profile(self, **_kwargs):
        return SimpleNamespace(
            system_prompt="你是测试智能体。",
            tool_summaries=[],
            enabled_mcp_capabilities=[],
        )


class _AgentMemoryService:
    def build_context(self):
        return SimpleNamespace(is_empty=True, system_prompt="", loaded_layers=[])


class _TaskEvaluator:
    async def evaluate(self, _message):
        return SimpleNamespace(reasoning="")


class _ModelProvider:
    def get_model_config(self, _selected_model):
        return {"supports_reasoning": False}

    def get_model(self, _selected_model):
        return object()


class _ToolRegistry:
    def list_all(self):
        return []


class _CompletionEvaluator:
    def build_synthesis_instruction(self, _user_message):
        return ""


class _WaitingApprovalHarness:
    def __init__(self, **_kwargs):
        return None

    async def run(self, _messages):
        approval_request_id = "apr_001"
        yield json.dumps({
            "type": "status",
            "status_kind": "approval_created",
            "approval_request_id": approval_request_id,
            "approval_request": {"request_id": approval_request_id, "status": "pending"},
        }) + "\n"
        yield json.dumps({
            "type": "state",
            "state": "waiting_approval",
            "stop_reason": "approval_required",
            "approval_request_id": approval_request_id,
        }) + "\n"
        yield json.dumps({
            "type": "done",
            "content": "工具治理策略要求人工审批，已创建审批请求。",
            "state": "waiting_approval",
            "stop_reason": "approval_required",
            "approval_request_id": approval_request_id,
            "error_category": "tool_governance",
        }) + "\n"


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

    def test_persist_tool_artifact_accepts_tool_execution_envelope(self):
        store = InMemoryArtifactStore()
        event = {
            "tool_execution_envelope": {
                "tool_name": "search",
                "tool_call_id": "call_envelope",
                "status": "ok",
                "result_text": "统一 envelope 查询结果",
                "render_mode": "structured_card",
                "card_schema": "search_summary.v1",
                "card": {
                    "kind": "search_summary",
                    "schema": "search_summary.v1",
                    "source": "knowledge_base",
                    "source_label": "知识库",
                    "source_count": 2,
                },
                "artifact_ref": {
                    "artifact_id": "art_pending",
                    "kind": "tool_result",
                    "uri": "artifact://tool_result/art_pending",
                },
                "execution_metadata": {
                    "cache_hit": False,
                    "duration_ms": 18.5,
                    "result_source": "tool",
                    "status": "ok",
                },
                "tool_spec": {"name": "search", "render_mode": "structured_card"},
            }
        }

        persist_tool_artifact(
            artifact_store=store,
            conversation_id=17,
            event_data=event,
            selected_model="doubao",
        )

        artifacts = store.list_artifacts(conversation_id=17, kind="tool_result")
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0].content, "统一 envelope 查询结果")
        self.assertEqual(artifacts[0].render_mode, "structured_card")
        self.assertEqual(artifacts[0].card_schema, "search_summary.v1")
        self.assertEqual(artifacts[0].metadata["tool_name"], "search")
        self.assertEqual(artifacts[0].metadata["tool_call_id"], "call_envelope")
        self.assertEqual(artifacts[0].metadata["artifact_ref"]["artifact_id"], "art_pending")
        self.assertEqual(artifacts[0].metadata["tool_execution"]["duration_ms"], 18.5)

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

    def test_build_done_payload_preserves_runtime_governance_markers(self):
        payload = build_done_payload(
            chunk_data={
                "run_id": "run_001",
                "state": "waiting_approval",
                "stop_reason": "approval_required",
                "approval_request_id": "apr_001",
                "payload": {
                    "content": "等待审批",
                    "state": "waiting_approval",
                    "stop_reason": "approval_required",
                },
            },
            full_answer="等待审批",
            reasoning_content=None,
            context_stats={
                "total_tokens": 10,
                "message_count": 2,
                "compression_count": 0,
            },
        )

        data = json.loads(payload)
        self.assertEqual(data["run_id"], "run_001")
        self.assertEqual(data["state"], "waiting_approval")
        self.assertEqual(data["stop_reason"], "approval_required")
        self.assertEqual(data["approval_request_id"], "apr_001")
        self.assertEqual(data["payload"]["state"], "waiting_approval")

    async def _collect_waiting_approval_orchestrator_chunks(self):
        context_store = _ContextStore()
        with (
            patch("backend.orchestrator.get_task_evaluator", return_value=_TaskEvaluator()),
            patch("backend.orchestrator.get_model_provider", return_value=_ModelProvider()),
            patch("backend.orchestrator.get_context_store", return_value=context_store),
            patch("backend.orchestrator.get_memory_store", return_value=_MemoryStore()),
            patch("backend.orchestrator.get_artifact_store", return_value=_ArtifactStore()),
            patch("backend.orchestrator.get_registry", return_value=_ToolRegistry()),
            patch("backend.orchestrator.get_mcp_runtime_service", return_value=_McpRuntimeService()),
            patch("backend.orchestrator.get_runtime_learning_service", return_value=_RuntimeLearningService()),
            patch("backend.orchestrator.get_skill_runtime_service", return_value=_SkillRuntimeService()),
            patch("backend.orchestrator.get_subagent_runtime_service", return_value=_SubagentRuntimeService()),
            patch("backend.orchestrator.get_capability_profile_service", return_value=_CapabilityProfileService()),
            patch("backend.orchestrator.get_agent_memory_service", return_value=_AgentMemoryService()),
            patch(
                "backend.services.completion_evaluator_service.get_completion_evaluator_service",
                return_value=_CompletionEvaluator(),
            ),
            patch("backend.orchestrator.AgentHarness", _WaitingApprovalHarness),
        ):
            orchestrator = SimplifiedOrchestrator(conversation_id=21)
            chunks = []
            async for chunk in orchestrator.process_message("请写入文件", selected_model="doubao"):
                chunks.append(json.loads(chunk))
            return chunks

    def test_orchestrator_forwards_approval_status_state_and_done_markers(self):
        chunks = asyncio.run(self._collect_waiting_approval_orchestrator_chunks())

        approval_status = next(item for item in chunks if item.get("status_kind") == "approval_created")
        state_event = next(item for item in chunks if item.get("type") == "state")
        done_event = chunks[-1]

        self.assertEqual(approval_status["approval_request_id"], "apr_001")
        self.assertEqual(state_event["state"], "waiting_approval")
        self.assertEqual(done_event["type"], "done")
        self.assertEqual(done_event["state"], "waiting_approval")
        self.assertEqual(done_event["stop_reason"], "approval_required")
        self.assertEqual(done_event["approval_request_id"], "apr_001")
        self.assertEqual(done_event["error_category"], "tool_governance")

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
