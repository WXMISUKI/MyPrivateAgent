"""
简化版多智能体协调器 - 重构版
参考 Claude Code 的 Agent Harness 架构
"""
import json
import logging
from typing import Any, AsyncGenerator, Optional

from langchain_core.messages import HumanMessage, SystemMessage

try:
    from agent_framework import (
        get_artifact_store,
        get_context_store,
        get_memory_store,
        get_model_provider,
    )
    from task_evaluator import get_task_evaluator
    from harness import AgentHarness, get_registry
    from harness.tool_registry import register_default_tools, register_langchain_tools
    from services.orchestrator_service import (
        OrchestratorStreamState,
        build_done_payload,
        persist_runtime_knowledge_artifact,
        persist_runtime_knowledge_effect_artifact,
        persist_runtime_skill_artifact,
        persist_runtime_skill_effect_artifact,
        persist_tool_artifact,
        should_retry_without_tools,
    )
    from services.mcp_runtime_service import get_mcp_runtime_service
    from services.runtime_learning_service import get_runtime_learning_service
    from services.skill_runtime_service import get_skill_runtime_service
    from services.subagent_service import get_subagent_runtime_service
    from services.capability_profile_service import get_capability_profile_service
    from services.agent_memory_service import get_agent_memory_service
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework import (
        get_artifact_store,
        get_context_store,
        get_memory_store,
        get_model_provider,
    )
    from backend.task_evaluator import get_task_evaluator
    from backend.harness import AgentHarness, get_registry
    from backend.harness.tool_registry import register_default_tools, register_langchain_tools
    from backend.services.orchestrator_service import (
        OrchestratorStreamState,
        build_done_payload,
        persist_runtime_knowledge_artifact,
        persist_runtime_knowledge_effect_artifact,
        persist_runtime_skill_artifact,
        persist_runtime_skill_effect_artifact,
        persist_tool_artifact,
        should_retry_without_tools,
    )
    from backend.services.mcp_runtime_service import get_mcp_runtime_service
    from backend.services.runtime_learning_service import get_runtime_learning_service
    from backend.services.skill_runtime_service import get_skill_runtime_service
    from backend.services.subagent_service import get_subagent_runtime_service
    from backend.services.capability_profile_service import get_capability_profile_service
    from backend.services.agent_memory_service import get_agent_memory_service

register_default_tools()
register_langchain_tools()

logger = logging.getLogger(__name__)


class SimplifiedOrchestrator:
    """
    简化版多智能体协调器 - 重构版

    使用新的 AgentHarness 架构：
    1. 简化的任务评估
    2. AgentHarness 核心循环
    3. 统一的模型适配器
    """

    def __init__(
        self,
        conversation_id: int,
        show_reasoning: bool = False
    ):
        self.conversation_id = conversation_id
        self.show_reasoning = show_reasoning
        self.task_evaluator = get_task_evaluator()
        self.model_provider = get_model_provider()
        self.model_router = self.model_provider
        self.tool_registry = get_registry()
        self.context_store = get_context_store()
        try:
            from config import DEFAULT_MODEL
        except ModuleNotFoundError:
            from backend.config import DEFAULT_MODEL
        self.context_window = self.context_store.get_context(conversation_id, DEFAULT_MODEL)
        self.memory_store = get_memory_store()
        self.session = self.memory_store.create_session(conversation_id)
        self.artifact_store = get_artifact_store()
        self.mcp_runtime_service = get_mcp_runtime_service()
        self.runtime_learning_service = get_runtime_learning_service()
        self.skill_runtime_service = get_skill_runtime_service()
        self.subagent_runtime_service = get_subagent_runtime_service()
        self.capability_profile_service = get_capability_profile_service()
        self.agent_memory_service = get_agent_memory_service()
        try:
            from services.completion_evaluator_service import get_completion_evaluator_service
        except ModuleNotFoundError:  # pragma: no cover - package import compatibility
            from backend.services.completion_evaluator_service import get_completion_evaluator_service
        self.completion_evaluator = get_completion_evaluator_service()

    def _prepare_runtime_context(
        self,
        user_message: str,
        execution_context: dict[str, Any] | None,
    ) -> tuple[Any, Any, Any, Any, Any]:
        runtime_knowledge = self.runtime_learning_service.get_runtime_context(
            user_message=user_message, scope="chat",
        )
        subagent_context = self.subagent_runtime_service.normalize_context(execution_context)
        runtime_skills = self.skill_runtime_service.get_runtime_context(
            user_message=user_message, execution_context=execution_context,
        )
        self.mcp_runtime_service.sync_registry_tools(self.tool_registry)
        capability_profile = self.capability_profile_service.build_profile(
            tool_registry=self.tool_registry,
            runtime_skills=runtime_skills,
            runtime_knowledge=runtime_knowledge,
            execution_context=execution_context,
        )
        agent_memory = self.agent_memory_service.build_context()
        return runtime_knowledge, runtime_skills, subagent_context, capability_profile, agent_memory

    def _build_messages(
        self,
        user_message: str,
        capability_profile: Any,
        agent_memory: Any,
        runtime_knowledge: Any,
        runtime_skills: Any,
        subagent_context: Any,
    ) -> list:
        messages = [SystemMessage(content=capability_profile.system_prompt)]
        if not agent_memory.is_empty and agent_memory.system_prompt:
            messages.append(SystemMessage(content=agent_memory.system_prompt))
        intent_prompt = self.completion_evaluator.build_synthesis_instruction(user_message)
        if intent_prompt:
            messages.append(SystemMessage(content=intent_prompt))
        if not runtime_knowledge.is_empty:
            messages.append(SystemMessage(content=runtime_knowledge.system_prompt))
        if not runtime_skills.is_empty:
            messages.append(SystemMessage(content=runtime_skills.system_prompt))
        if subagent_context is not None:
            messages.append(SystemMessage(content=self.subagent_runtime_service.build_role_system_prompt(subagent_context)))
        messages.append(HumanMessage(content=user_message))
        return messages

    def _process_stream_chunk(
        self,
        chunk_data: dict,
        stream_state: OrchestratorStreamState,
        selected_model: str,
        supports_reasoning: bool,
    ) -> str | None:
        chunk_type = chunk_data.get("type")

        if chunk_type == "reasoning":
            stream_state.last_reasoning += chunk_data.get("content", "")
            if supports_reasoning and self.show_reasoning:
                return json.dumps(chunk_data, ensure_ascii=False) + "\n"
            return None

        if chunk_type == "content":
            content = chunk_data.get("content", "")
            if content == stream_state.last_content_chunk:
                return None
            stream_state.last_content_chunk = content
            stream_state.full_content += content
            return json.dumps(chunk_data, ensure_ascii=False) + "\n"

        if chunk_type == "tool_result":
            persist_tool_artifact(
                artifact_store=self.artifact_store,
                conversation_id=self.conversation_id,
                event_data=chunk_data,
                selected_model=selected_model,
            )
            return json.dumps(chunk_data, ensure_ascii=False) + "\n"

        return json.dumps(chunk_data, ensure_ascii=False) + "\n"

    async def process_message(
        self,
        user_message: str,
        selected_model: str = "doubao",
        execution_context: Optional[dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        处理用户消息（流式输出）

        Args:
            user_message: 用户消息
            selected_model: 用户选择的模型

        Yields:
            流式输出内容
        """
        # 0. 更新会话状态
        self.memory_store.update_session_activity(self.conversation_id)
        self.memory_store.increment_message_count(self.conversation_id)

        runtime_knowledge, runtime_skills, subagent_context, capability_profile, agent_memory = \
            self._prepare_runtime_context(user_message, execution_context)

        if subagent_context is not None:
            yield json.dumps(
                self.subagent_runtime_service.build_spawn_event(subagent_context),
                ensure_ascii=False,
            ) + "\n"
            yield json.dumps({
                "type": "status",
                "status_kind": "agent_mode",
                "agent_role": subagent_context.agent_role,
                "agent_id": subagent_context.agent_id,
                "plan_id": subagent_context.plan_id,
                "plan_item_id": subagent_context.plan_item_id,
                "plan_item_title": subagent_context.plan_item_title,
                "required_capabilities": list(subagent_context.required_capabilities),
                "content": f"当前步骤由 {subagent_context.agent_role} 子智能体模式处理",
            }, ensure_ascii=False) + "\n"
            capability_state = self.mcp_runtime_service.validate_required_capabilities(
                list(subagent_context.required_capabilities)
            )
            if not capability_state["ready"]:
                message = self._build_capability_guard_message(
                    missing_capabilities=capability_state["missing_capabilities"],
                    unavailable_capabilities=capability_state["unavailable_capabilities"],
                )
                yield json.dumps({
                    "type": "status",
                    "status_kind": "capability_blocked",
                    "agent_role": subagent_context.agent_role,
                    "agent_id": subagent_context.agent_id,
                    "plan_id": subagent_context.plan_id,
                    "plan_item_id": subagent_context.plan_item_id,
                    "plan_item_title": subagent_context.plan_item_title,
                    "required_capabilities": list(subagent_context.required_capabilities),
                    "missing_capabilities": capability_state["missing_capabilities"],
                    "unavailable_capabilities": capability_state["unavailable_capabilities"],
                    "content": message,
                }, ensure_ascii=False) + "\n"
                yield json.dumps({
                    "type": "error",
                    "content": message,
                }, ensure_ascii=False) + "\n"
                return

        if not runtime_knowledge.is_empty:
            persist_runtime_knowledge_artifact(
                artifact_store=self.artifact_store,
                conversation_id=self.conversation_id,
                knowledge_context=runtime_knowledge,
                selected_model=selected_model,
            )
            yield json.dumps({
                "type": "status",
                "status_kind": "runtime_knowledge",
                "scope": runtime_knowledge.metadata.get("scope", "global"),
                "prompt_count": runtime_knowledge.prompt_count,
                "practice_count": runtime_knowledge.practice_count,
                "selected_items": runtime_knowledge.metadata.get("selected_items", []),
                "skipped_items": runtime_knowledge.metadata.get("skipped_items", []),
            }) + "\n"

        if not runtime_skills.is_empty:
            persist_runtime_skill_artifact(
                artifact_store=self.artifact_store,
                conversation_id=self.conversation_id,
                skill_context=runtime_skills,
                selected_model=selected_model,
            )
            yield json.dumps({
                "type": "status",
                "status_kind": "runtime_skills",
                "selected_count": runtime_skills.metadata.get("selected_count", 0),
                "selected_items": runtime_skills.metadata.get("selected_items", []),
                "skipped_items": runtime_skills.metadata.get("skipped_items", []),
                "agent_role": runtime_skills.metadata.get("agent_role"),
            }, ensure_ascii=False) + "\n"

        # 1. 添加用户消息到上下文
        self.context_window.add_user_message(user_message)

        # 检查上下文状态
        stats = self.context_window.get_stats()
        if stats['usage_ratio'] > 0.7:
            logger.info(f"[Orchestrator] 上下文使用率: {stats['usage_ratio']:.1%}")

        # 1. 快速评估任务复杂度
        evaluation = await self.task_evaluator.evaluate(user_message)

        # 获取模型配置
        model_config = self.model_provider.get_model_config(selected_model)
        supports_reasoning = model_config.get("supports_reasoning", False)

        # 2. 如果是复杂任务，输出评估信息
        if supports_reasoning and self.show_reasoning:
            yield json.dumps({
                "type": "reasoning",
                "content": f"\n📊 任务评估: {evaluation.reasoning}\n"
            }) + "\n"

        # 3. 获取模型
        try:
            model = self.model_provider.get_model(selected_model)
        except ValueError as e:
            logger.error(f"[Orchestrator] 获取模型失败: {e}")
            yield json.dumps({
                "type": "error",
                "content": f"模型不可用: {selected_model}"
            }) + "\n"
            return

        # 4. 获取工具
        tools = self.tool_registry.list_all()
        yield json.dumps({
            "type": "status",
            "status_kind": "execution_progress",
            "phase": "capability_profile",
            "content": f"当前已识别 {len(capability_profile.tool_summaries)} 个工具、{len(capability_profile.enabled_mcp_capabilities)} 个 MCP capability，正在按现有能力规划执行。",
        }, ensure_ascii=False) + "\n"
        if not agent_memory.is_empty:
            yield json.dumps({
                "type": "status",
                "status_kind": "execution_progress",
                "phase": "memory_layers",
                "content": f"已加载 {len(agent_memory.loaded_layers)} 层记忆 / 指令规则，当前按项目规则继续执行。",
            }, ensure_ascii=False) + "\n"

        # 检测是否为豆包模型（豆包模型不支持 tool_choice="auto"）
        try:
            from config import DOUBAO_SUPPORTS_TOOL_CHOICE
        except ModuleNotFoundError:
            from backend.config import DOUBAO_SUPPORTS_TOOL_CHOICE
        is_doubao = "doubao" in selected_model.lower()
        use_tool_choice = DOUBAO_SUPPORTS_TOOL_CHOICE if is_doubao else True

        # 5. 使用 AgentHarness 处理
        harness = AgentHarness(
            model=model,
            tools=tools,
            model_name=selected_model,
            conversation_id=self.conversation_id,
            use_tool_choice=use_tool_choice,
            parallel_tool_calls=not is_doubao,
            runtime_scope=execution_context,
        )

        # 6. 构建消息列表
        messages = self._build_messages(
            user_message, capability_profile, agent_memory,
            runtime_knowledge, runtime_skills, subagent_context,
        )

        # 8. 运行 Agent 循环
        stream_state = OrchestratorStreamState()

        async for chunk_str in harness.run(messages):
            try:
                chunk_data = json.loads(chunk_str)
                chunk_type = chunk_data.get('type')

                if chunk_type in ('reasoning', 'content', 'tool_result'):
                    output = self._process_stream_chunk(
                        chunk_data, stream_state, selected_model, supports_reasoning,
                    )
                    if output:
                        yield output

                elif chunk_type == 'done':
                    # 完成信号
                    reasoning_content = chunk_data.get('reasoning') or stream_state.last_reasoning
                    full_answer = stream_state.full_content or chunk_data.get('content', '')

                    if subagent_context is not None and full_answer:
                        yield json.dumps(
                            self.subagent_runtime_service.build_collect_event(
                                subagent_context,
                                output_text=full_answer,
                            ),
                            ensure_ascii=False,
                        ) + "\n"

                    # 添加助手消息到上下文
                    if full_answer:
                        self.context_window.add_assistant_message(full_answer)

                    # 更新内存管理器
                    self.memory_store.update_tokens(self.conversation_id, stats['total_tokens'])

                    if reasoning_content:
                        self.artifact_store.create_artifact(
                            conversation_id=self.conversation_id,
                            kind="reasoning_trace",
                            content=reasoning_content,
                            render_mode="plain_text",
                            metadata={"model_name": selected_model},
                        )

                    persist_runtime_knowledge_effect_artifact(
                        artifact_store=self.artifact_store,
                        conversation_id=self.conversation_id,
                        knowledge_context=runtime_knowledge,
                        selected_model=selected_model,
                        stop_reason=chunk_data.get("stop_reason"),
                        output_text=full_answer,
                    )
                    persist_runtime_skill_effect_artifact(
                        artifact_store=self.artifact_store,
                        conversation_id=self.conversation_id,
                        skill_context=runtime_skills,
                        selected_model=selected_model,
                        stop_reason=chunk_data.get("stop_reason"),
                        output_text=full_answer,
                    )

                    # 输出上下文统计（调试用）
                    stats = self.context_window.get_stats()
                    if stats['compression_count'] > 0:
                        logger.info(f"[Orchestrator] 上下文已压缩 {stats['compression_count']} 次")

                    if subagent_context is not None and full_answer:
                        yield json.dumps(
                            self.subagent_runtime_service.build_merge_event(subagent_context),
                            ensure_ascii=False,
                        ) + "\n"

                    yield build_done_payload(
                        chunk_data=chunk_data,
                        full_answer=full_answer,
                        reasoning_content=reasoning_content,
                        context_stats=stats,
                    )

                elif chunk_type == 'error':
                    # 检查是否是工具调用不支持的错误，如果是则重新创建 AgentHarness 不使用工具
                    error_content = chunk_data.get('content', '')
                    if should_retry_without_tools(error_content):
                        logger.info("[Orchestrator] 收到工具不支持错误，重新创建 AgentHarness（不使用工具）")
                        harness = AgentHarness(
                            model=self.model_provider.get_model(selected_model),
                            tools=[],
                            model_name=selected_model,
                            use_bind_tools=False,
                            use_tool_choice=False,
                            parallel_tool_calls=False,
                            runtime_scope=execution_context,
                        )
                        stream_state = OrchestratorStreamState()
                        async for retry_chunk in harness.run(messages):
                            yield retry_chunk
                        break
                    yield chunk_str

            except json.JSONDecodeError:
                # 非 JSON 格式，直接作为内容
                if chunk_str.strip():
                    yield f"data: {json.dumps({'content': chunk_str})}\n\n"

    def _build_capability_guard_message(
        self,
        *,
        missing_capabilities: list[str],
        unavailable_capabilities: list[str],
    ) -> str:
        parts = ["当前执行步骤依赖的 MCP capability 不满足，已停止执行。"]
        if missing_capabilities:
            parts.append(f"未配置能力：{', '.join(missing_capabilities)}。")
        if unavailable_capabilities:
            parts.append(f"已配置但不可用：{', '.join(unavailable_capabilities)}。")
        return "".join(parts)


_orchestrator_instance = None


def get_orchestrator(conversation_id: int, show_reasoning: bool = False) -> SimplifiedOrchestrator:
    """获取协调器实例"""
    global _orchestrator_instance
    _orchestrator_instance = SimplifiedOrchestrator(
        conversation_id=conversation_id,
        show_reasoning=show_reasoning
    )
    return _orchestrator_instance
