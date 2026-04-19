"""
简化版多智能体协调器 - 重构版
参考 Claude Code 的 Agent Harness 架构
支持单智能体和多智能体模式的自动切换
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, List, Optional
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from model_router import get_model_router
from task_evaluator import get_task_evaluator, TaskComplexityResult
from harness import AgentHarness, create_adapter, get_registry, get_context_manager, get_memory_manager
from learning_recorder import LearningRecorder

logger = logging.getLogger(__name__)


class Subtask(BaseModel):
    """子任务"""
    id: str
    description: str


class SubagentResult(BaseModel):
    """子智能体结果"""
    subtask_id: str
    content: str
    status: str  # success / failed


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
        self.model_router = get_model_router()
        self.tool_registry = get_registry()
        self.context_manager = get_context_manager()
        self.context_window = self.context_manager.get_context(conversation_id, "deepseek-r1:7b")
        self.memory_manager = get_memory_manager()
        self.session = self.memory_manager.create_session(conversation_id)
        self.learning_recorder = LearningRecorder()
        self.conversation_history = []  # 用于存储对话历史供学习分析

    async def process_message(
        self,
        user_message: str,
        selected_model: str = "doubao"
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
        self.memory_manager.update_session_activity(self.conversation_id)
        self.memory_manager.increment_message_count(self.conversation_id)

        # 1. 添加用户消息到上下文
        self.context_window.add_user_message(user_message)

        # 检查上下文状态
        stats = self.context_window.get_stats()
        if stats['usage_ratio'] > 0.7:
            logger.info(f"[Orchestrator] 上下文使用率: {stats['usage_ratio']:.1%}")

        # 1. 快速评估任务复杂度
        evaluation = await self.task_evaluator.evaluate(user_message)

        # 获取模型配置
        model_config = self.model_router.get_model_config(selected_model)
        supports_reasoning = model_config.get("supports_reasoning", False)

        # 2. 如果是复杂任务，输出评估信息
        if supports_reasoning and self.show_reasoning:
            yield json.dumps({
                "type": "reasoning",
                "content": f"\n📊 任务评估: {evaluation.reasoning}\n"
            }) + "\n"

        # 3. 获取模型
        try:
            model = self.model_router.get_model(selected_model)
        except ValueError as e:
            logger.error(f"[Orchestrator] 获取模型失败: {e}")
            yield json.dumps({
                "type": "error",
                "content": f"模型不可用: {selected_model}"
            }) + "\n"
            return

        # 4. 获取工具
        tools = self.tool_registry.list_all()

        # 5. 使用 AgentHarness 处理
        harness = AgentHarness(
            model=model,
            tools=tools,
            model_name=selected_model
        )

        # 6. 构建消息列表
        messages = [HumanMessage(content=user_message)]

        # 7. 创建模型适配器
        adapter = create_adapter(selected_model)

        # 8. 运行 Agent 循环
        last_content = ""  # 用于去重
        last_reasoning = ""  # 累积推理内容

        async for chunk_str in harness.run(messages):
            try:
                chunk_data = json.loads(chunk_str)
                chunk_type = chunk_data.get('type')

                if chunk_type == 'reasoning':
                    # 推理内容
                    reasoning = chunk_data.get('content', '')
                    last_reasoning += reasoning
                    if supports_reasoning and self.show_reasoning:
                        yield chunk_str

                elif chunk_type == 'content':
                    # 内容，进行去重
                    content = chunk_data.get('content', '')

                    # 简单的去重：如果内容和上次一样，跳过
                    if content == last_content:
                        continue

                    last_content += content
                    yield chunk_str

                elif chunk_type == 'done':
                    # 完成信号
                    reasoning_content = chunk_data.get('reasoning') or last_reasoning
                    full_answer = last_content

                    # 添加助手消息到上下文
                    if full_answer:
                        self.context_window.add_assistant_message(full_answer)

                    # 更新内存管理器
                    self.memory_manager.update_tokens(self.conversation_id, stats['total_tokens'])

                    # 输出上下文统计（调试用）
                    stats = self.context_window.get_stats()
                    if stats['compression_count'] > 0:
                        logger.info(f"[Orchestrator] 上下文已压缩 {stats['compression_count']} 次")

                    yield json.dumps({
                        "type": "done",
                        "content": full_answer,
                        "reasoning_content": reasoning_content if reasoning_content else None,
                        "context_stats": {
                            "tokens": stats['total_tokens'],
                            "messages": stats['message_count'],
                            "compression_count": stats['compression_count']
                        }
                    }) + "\n"

                elif chunk_type == 'error':
                    yield chunk_str

            except json.JSONDecodeError:
                # 非 JSON 格式，直接作为内容
                if chunk_str.strip():
                    yield f"data: {json.dumps({'content': chunk_str})}\n\n"

    async def _process_single_agent_simple(
        self,
        user_message: str,
        model_name: str
    ) -> AsyncGenerator[str, None]:
        """简化版单智能体模式"""
        try:
            model = self.model_router.get_model(model_name)

            async for chunk in model.astream([HumanMessage(content=user_message)]):
                if hasattr(chunk, 'content') and chunk.content:
                    yield json.dumps({
                        "type": "content",
                        "content": chunk.content
                    }) + "\n"

            yield json.dumps({
                "type": "done",
                "content": "",
                "reasoning_content": None
            }) + "\n"

        except Exception as e:
            logger.error(f"[单智能体] 错误: {e}")
            yield json.dumps({
                "type": "error",
                "content": f"错误: {str(e)}"
            }) + "\n"

    async def _process_multi_agent_simple(
        self,
        user_message: str,
        num_subagents: int = 1
    ) -> AsyncGenerator[str, None]:
        """简化版多智能体模式 - 只使用主智能体"""
        try:
            # 使用豆包或其他可用模型
            try:
                model = self.model_router.get_model("doubao")
            except ValueError:
                try:
                    model = self.model_router.get_model("llama3.1")
                except ValueError:
                    model = self.model_router.get_model("deepseek-r1:7b")

            async for chunk in model.astream([HumanMessage(content=user_message)]):
                if hasattr(chunk, 'content') and chunk.content:
                    yield json.dumps({
                        "type": "content",
                        "content": chunk.content
                    }) + "\n"

            yield json.dumps({
                "type": "done",
                "content": "",
                "reasoning_content": None
            }) + "\n"

        except Exception as e:
            logger.error(f"[多智能体] 错误: {e}")
            yield json.dumps({
                "type": "error",
                "content": f"错误: {str(e)}"
            }) + "\n"


_orchestrator_instance = None


def get_orchestrator(conversation_id: int, show_reasoning: bool = False) -> SimplifiedOrchestrator:
    """获取协调器实例"""
    global _orchestrator_instance
    _orchestrator_instance = SimplifiedOrchestrator(
        conversation_id=conversation_id,
        show_reasoning=show_reasoning
    )
    return _orchestrator_instance
