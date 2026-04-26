"""
AgentHarness - 参考 Claude Code 的核心 Agent 循环
支持真正的 bind_tools 工具调用
"""
import json
import re
import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, Any, List, Optional, Union
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.messages.tool import tool_call as create_tool_call
from langchain_core.tools import BaseTool

try:
    from agent_framework.events import AgentEventFactory, AgentEventType
    from agent_framework.runtime import AgentRunContext, AgentState
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.events import AgentEventFactory, AgentEventType
    from backend.agent_framework.runtime import AgentRunContext, AgentState

try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False
    logger = logging.getLogger(__name__)
    logger.warning("[AgentHarness] json_repair 库未安装，JSON 修复功能将不可用")

logger = logging.getLogger(__name__)


class StreamChunk:
    """流式输出块"""
    def __init__(self, type: str, content: str = "", reasoning: str = "", tool_calls: List[Dict] = None):
        self.type = type
        self.content = content
        self.reasoning = reasoning
        self.tool_calls = tool_calls or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "reasoning": self.reasoning,
            "tool_calls": self.tool_calls
        }


class StreamingToolCallTracker:
    """
    流式工具调用追踪器

    参考豆包文档：流式输出时，tool_calls 会分块返回
    需要通过 index 追踪并组装完整的工具调用
    """

    def __init__(self):
        self.pending_tool_calls: Dict[int, Dict] = {}
        self.accumulated_args: Dict[int, str] = {}

    def _ensure_slot(self, index: int, tool_id: Optional[str] = None) -> None:
        """确保指定 index 的工具调用槽位存在。"""
        if index not in self.pending_tool_calls:
            self.pending_tool_calls[index] = {
                "name": "",
                "arguments": "",
                "id": tool_id or f"call_{index}"
            }
            self.accumulated_args[index] = ""

    def _extract_chunk_fields(self, tool_call_chunk) -> tuple[int, str, str, Optional[str]]:
        """从 dict 或对象型 chunk 中提取 index、name、arguments、id。"""
        if isinstance(tool_call_chunk, dict):
            function_payload = tool_call_chunk.get("function") or {}
            index = tool_call_chunk.get("index", 0)
            name = (
                tool_call_chunk.get("name")
                or function_payload.get("name")
                or ""
            )
            args = (
                tool_call_chunk.get("args")
                or tool_call_chunk.get("arguments")
                or function_payload.get("arguments")
                or ""
            )
            tool_id = tool_call_chunk.get("id") or function_payload.get("id")
            return index, name, args, tool_id

        function_payload = getattr(tool_call_chunk, "function", None)
        index = getattr(tool_call_chunk, "index", 0)
        name = (
            getattr(tool_call_chunk, "name", "")
            or getattr(function_payload, "name", "")
            or ""
        )
        args = (
            getattr(tool_call_chunk, "args", "")
            or getattr(tool_call_chunk, "arguments", "")
            or getattr(function_payload, "arguments", "")
            or ""
        )
        tool_id = getattr(tool_call_chunk, "id", None) or getattr(function_payload, "id", None)
        return index, name, args, tool_id

    def parse_arguments(self, raw: Union[str, Dict[str, Any], None]) -> Union[Dict[str, Any], str]:
        """尽量将工具参数解析成 dict；失败时保留原始字符串。"""
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return raw

        raw = str(raw).strip()
        if not raw:
            return {}
        if raw == "}":
            return {}

        if HAS_JSON_REPAIR:
            try:
                repaired = repair_json(raw, return_objects=True)
                if isinstance(repaired, dict):
                    return repaired
                if isinstance(repaired, str):
                    return json.loads(repaired)
            except Exception as e:
                logger.debug(f"[StreamingToolCallTracker] json_repair 未能解析参数: {e}")

        if raw.startswith("{") and raw.endswith("}"):
            try:
                return json.loads(raw)
            except Exception:
                pass

        parsed = self._parse_fragments_to_json(raw)
        return parsed if parsed else raw

    def add_chunk(self, tool_call_chunk) -> Optional[List[Dict]]:
        """
        添加一个工具调用分块

        Returns:
            如果有完整的工具调用完成，返回列表；否则返回 None
        """
        index, name, args_str, tool_id = self._extract_chunk_fields(tool_call_chunk)
        self._ensure_slot(index, tool_id)

        if name and not self.pending_tool_calls[index]["name"]:
            self.pending_tool_calls[index]["name"] = name
        if tool_id:
            self.pending_tool_calls[index]["id"] = tool_id

        if args_str:
            self.accumulated_args[index] += args_str
            self.pending_tool_calls[index]["arguments"] = self.accumulated_args[index]

        return None

    def add_from_invalid_tool_calls(self, tool_calls_or_invalid: List[Dict]) -> None:
        """
        从 tool_calls 或 invalid_tool_calls 添加参数片段（豆包模型流式传输时使用）

        参考豆包文档：流式输出时，tool_calls 会分块返回
        格式如：{'name': None, 'args': 'query', 'id': None}

        Args:
            tool_calls_or_invalid: tool_calls 或 invalid_tool_calls 列表
        """
        for tc in tool_calls_or_invalid:
            index, tc_name, tc_args, tc_id = self._extract_chunk_fields(tc)
            self._ensure_slot(index, tc_id)

            if tc_name and not self.pending_tool_calls[index]["name"]:
                self.pending_tool_calls[index]["name"] = tc_name
            if tc_id:
                self.pending_tool_calls[index]["id"] = tc_id

            if tc_args:
                self.accumulated_args[index] += tc_args
                parsed_args = self.parse_arguments(self.accumulated_args[index])
                self.pending_tool_calls[index]["arguments"] = parsed_args

    def _parse_fragments_to_json(self, raw: str) -> Optional[Dict]:
        """
        从片段解析 JSON

        豆包模型分块返回如：query": "舟山今日天气"}
        需要智能解析为 {"query": "舟山今日天气"}
        """
        if not raw:
            return None

        raw = raw.strip()
        if raw.startswith('{') and raw.endswith('}'):
            try:
                return json.loads(raw)
            except:
                pass

        key_match = re.match(r'^"?(\w+)"?\s*:\s*"?(.+?)"?\s*}$', raw)
        if key_match:
            key, value = key_match.groups()
            value = value.strip().strip('"')
            if key and value:
                return {key: value}

        if '"' in raw and ':' in raw:
            parts = raw.split(':')
            if len(parts) >= 2:
                key = parts[0].strip().strip('"')
                value = ':'.join(parts[1:]).strip().strip('"}').strip('"')
                if key and value:
                    return {key: value}

        return None

    def get_completed_tool_calls(self) -> List[Dict]:
        """获取所有完成的工具调用"""
        completed = []
        for index in sorted(self.pending_tool_calls.keys()):
            tool_call = dict(self.pending_tool_calls[index])
            if not tool_call.get("name"):
                continue
            arguments = tool_call.get("arguments", {})
            if isinstance(arguments, str):
                tool_call["arguments"] = self.parse_arguments(arguments)
            completed.append(tool_call)
        return completed

    def normalize_tool_calls(self, raw_tool_calls: List[Dict]) -> List[Dict[str, Any]]:
        """
        规范化工具调用格式

        Args:
            raw_tool_calls: 原始工具调用列表

        Returns:
            规范化后的工具调用列表
        """
        normalized = []
        for tc in raw_tool_calls:
            name = tc.get('name', '')
            arguments = tc.get('arguments', '')

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            normalized.append({
                "name": name,
                "arguments": arguments,
                "id": tc.get('id') or tc.get('Id', None)
            })
        return normalized

    def reset(self):
        """重置追踪器"""
        self.pending_tool_calls.clear()
        self.accumulated_args.clear()


class ErrorResult:
    """错误结果"""
    def __init__(self, success: bool, message: str, recoverable: bool = False, suggestion: str = None):
        self.success = success
        self.message = message
        self.recoverable = recoverable
        self.suggestion = suggestion


class ErrorHandler:
    """
    错误处理器

    提供：
    - 指数退避重试
    - 错误分类
    - 友好错误信息
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def get_delay(self, attempt: int) -> float:
        """计算指数退避延迟"""
        return min(self.base_delay * (2 ** attempt), 60.0)

    def should_retry(self, error: Exception) -> bool:
        """判断错误是否应该重试"""
        error_msg = str(error).lower()

        retryable_patterns = [
            "connection",
            "timeout",
            "network",
            "rate limit",
            "429",
            "503",
            "502",
            "504",
        ]

        for pattern in retryable_patterns:
            if pattern in error_msg:
                return True

        return False

    async def execute_with_retry(
        self,
        func,
        *args,
        **kwargs
    ) -> ErrorResult:
        """带重试的执行"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                return ErrorResult(success=True, message=str(result))
            except Exception as e:
                last_error = e
                logger.warning(f"[ErrorHandler] 第 {attempt + 1} 次尝试失败: {e}")

                if not self.should_retry(e):
                    logger.info(f"[ErrorHandler] 错误不可恢复: {e}")
                    return ErrorResult(
                        success=False,
                        message=f"操作失败: {str(e)}",
                        recoverable=False,
                        suggestion="请稍后重试或联系管理员"
                    )

                if attempt < self.max_retries - 1:
                    delay = self.get_delay(attempt)
                    logger.info(f"[ErrorHandler] {delay} 秒后重试...")
                    await asyncio.sleep(delay)

        return ErrorResult(
            success=False,
            message=str(last_error),
            recoverable=True,
            suggestion="请稍后重试或尝试其他方式"
        )


class AgentHarness:
    """
    Agent 核心循环 - 参考 Claude Code 架构

    支持两种工具调用模式：
    1. bind_tools 模式（推荐）：使用 LangChain 的 bind_tools 绑定工具
    2. 文本解析模式（兼容）：从文本中解析工具调用

    参考豆包函数调用文档：
    - 支持 strict 模式
    - 支持流式工具调用
    - 支持 parallel_tool_calls 并行调用
    """

    def __init__(
        self,
        model,
        tools: List[Any],
        model_name: str = "unknown",
        use_bind_tools: bool = True,
        user_id: int = None,
        conversation_id: int = None,
        max_retries: int = 3,
        use_tool_choice: bool = True,
        parallel_tool_calls: bool = True
    ):
        self.original_model = model
        self.model = model
        self.tools = tools or []
        self.model_name = model_name
        self.use_bind_tools = use_bind_tools
        self.max_iterations = 10
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.error_handler = ErrorHandler(max_retries=max_retries)
        self.use_tool_choice = use_tool_choice
        self.parallel_tool_calls = parallel_tool_calls
        self.tool_call_tracker = StreamingToolCallTracker()

        self._setup_tools()

    def _setup_tools(self):
        """设置工具映射"""
        self.tool_map: Dict[str, Any] = {}
        self.bind_tools_failed = False
        self.model = self.original_model
        self._is_doubao_model = "doubao" in self.model_name.lower()

        if self.use_bind_tools:
            try:
                from .tool_registry import get_registry
                registry = get_registry()
                lc_tools = registry.get_langchain_tools()
                doubao_tool_defs = registry.get_doubao_tool_definitions()

                if lc_tools:
                    for tool in lc_tools:
                        self.tool_map[tool.name] = tool

                    if hasattr(self.model, 'bind_tools'):
                        if self._is_doubao_model and doubao_tool_defs:
                            logger.info(f"[AgentHarness] 豆包模型检测到，使用豆包格式工具定义 ({len(doubao_tool_defs)} 个工具)")
                            bound_model = self.model.bind_tools(
                                doubao_tool_defs,
                                strict=True,
                                parallel_tool_calls=self.parallel_tool_calls
                            )
                            self.model = bound_model
                        else:
                            tool_choice = "auto" if self.use_tool_choice else None
                            if tool_choice:
                                bound_model = self.model.bind_tools(
                                    lc_tools,
                                    tool_choice=tool_choice,
                                    parallel_tool_calls=self.parallel_tool_calls
                                )
                            else:
                                bound_model = self.model.bind_tools(
                                    lc_tools,
                                    parallel_tool_calls=self.parallel_tool_calls
                                )
                            self.model = bound_model
                            logger.info(f"[AgentHarness] 已绑定 {len(lc_tools)} 个 LangChain 工具 (tool_choice={tool_choice}, parallel={self.parallel_tool_calls})")
            except Exception as e:
                error_msg = str(e)
                if "does not support tools" in error_msg or "status code: 400" in error_msg:
                    logger.warning(f"[AgentHarness] 模型不支持 bind_tools，降级为纯文本模式")
                    self.bind_tools_failed = True
                    self.use_bind_tools = False
                    self.model = self.original_model
                else:
                    logger.warning(f"[AgentHarness] bind_tools 设置失败: {e}，降级为文本解析模式")
                    self.use_bind_tools = False

        if not self.use_bind_tools:
            from .tool_registry import get_registry
            registry = get_registry()
            for tool in registry.list_all():
                self.tool_map[tool.name] = tool

    async def run(self, messages: List[Any]) -> AsyncGenerator[str, None]:
        """
        运行 Agent 循环

        Args:
            messages: 消息列表

        Yields:
            流式输出块
        """
        iteration = 0
        full_response = ""
        full_reasoning = ""
        model_to_use = self.model
        use_bind_tools_this_run = self.use_bind_tools
        consecutive_invalid_tools = 0
        final_response_metadata: Dict[str, Any] = {}
        run_context = AgentRunContext(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            model_name=self.model_name,
        )
        event_factory = AgentEventFactory(
            run_id=run_context.run_id,
            conversation_id=self.conversation_id,
        )

        while iteration < self.max_iterations:
            iteration = run_context.begin_iteration()
            logger.info(f"[AgentHarness] 第 {iteration} 次迭代")

            response_content = ""
            reasoning_content = ""
            tool_calls_from_response = []
            response = None
            emitted_content_this_iteration = False
            self.tool_call_tracker.reset()

            try:
                current_model = model_to_use
                if hasattr(current_model, 'astream'):
                    async for chunk in current_model.astream(messages):
                        parsed = self._parse_chunk(chunk)
                        if parsed['type'] == 'reasoning':
                            reasoning_content += parsed['content']
                            yield event_factory.build(
                                AgentEventType.REASONING,
                                {"content": parsed['content']},
                                iteration=iteration,
                            ).to_json()
                        elif parsed['type'] == 'content':
                            response_content += parsed['content']
                            emitted_content_this_iteration = True
                            yield event_factory.build(
                                AgentEventType.CONTENT,
                                {"content": parsed['content']},
                                iteration=iteration,
                            ).to_json()
                        elif parsed['type'] == 'tool_calls':
                            tool_calls_from_response = parsed['tool_calls']

                    accumulated_tool_calls = self.tool_call_tracker.get_completed_tool_calls()
                    logger.info(f"[AgentHarness] 流式结束，累积工具调用: {len(accumulated_tool_calls)}")
                    logger.info(f"[AgentHarness] pending_tool_calls 内容: {self.tool_call_tracker.pending_tool_calls}")

                    if accumulated_tool_calls and not tool_calls_from_response:
                        logger.info(f"[AgentHarness] 从流式追踪器获取 {len(accumulated_tool_calls)} 个累积的工具调用")
                        tool_calls_from_response = accumulated_tool_calls

                    if not tool_calls_from_response and not response_content.strip():
                        logger.warning(f"[AgentHarness] 流式处理未获取到工具调用，尝试使用 ainvoke")
                        response = await current_model.ainvoke(messages)
                        response_content = response.content if hasattr(response, 'content') else str(response)
                        if hasattr(response, 'tool_calls') and response.tool_calls:
                            tool_calls_from_response = response.tool_calls
                            logger.info(f"[AgentHarness] 从 ainvoke 获取到 tool_calls: {response.tool_calls}")
                else:
                    response = await current_model.ainvoke(messages)
                    response_content = response.content if hasattr(response, 'content') else str(response)

                if not tool_calls_from_response and response is not None:
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        tool_calls_from_response = response.tool_calls
                    elif hasattr(response, 'additional_kwargs') and response.additional_kwargs:
                        tool_calls_from_response = response.additional_kwargs.get('tool_calls', [])

                if tool_calls_from_response:
                    tool_calls_from_response = self._normalize_tool_calls(tool_calls_from_response)
                    logger.info(f"[AgentHarness] 原始工具调用数据: {json.dumps(tool_calls_from_response, ensure_ascii=False)[:500]}")

                    first_tool = tool_calls_from_response[0] if tool_calls_from_response else {}
                    tool_name_raw = first_tool.get('Name') or first_tool.get('name', '')

                    if not tool_name_raw and use_bind_tools_this_run and iteration == 1:
                        logger.warning(f"[AgentHarness] 豆包模型返回无效工具调用，降级为纯文本模式")
                        use_bind_tools_this_run = False
                        model_to_use = self.original_model
                        full_response = response_content
                        break

                if not tool_calls_from_response:
                    if response_content and not emitted_content_this_iteration:
                        yield event_factory.build(
                            AgentEventType.CONTENT,
                            {"content": response_content},
                            iteration=iteration,
                        ).to_json()
                    full_response += response_content
                    full_reasoning += reasoning_content
                    run_context.set_state(AgentState.FINALIZING, stop_reason="model_completed")
                    break

                logger.info(f"[AgentHarness] 检测到 {len(tool_calls_from_response)} 个工具调用")
                run_context.set_state(AgentState.TOOL_CALLING)
                yield event_factory.build(
                    AgentEventType.TOOL_CALL_START,
                    {"count": len(tool_calls_from_response)},
                    iteration=iteration,
                ).to_json()
                full_reasoning += reasoning_content

                valid_tool_calls = [
                    create_tool_call(
                        name=tool_data["name"],
                        args=tool_data["arguments"] if isinstance(tool_data.get("arguments"), dict) else {},
                        id=tool_data.get("id")
                    )
                    for tool_data in tool_calls_from_response
                    if tool_data.get("name")
                ]
                if valid_tool_calls:
                    messages.append(
                        AIMessage(
                            content=response_content or "",
                            tool_calls=valid_tool_calls
                        )
                    )

                tool_results = []
                for tool_call in tool_calls_from_response:
                    tool_name = tool_call.get('name') or tool_call.get('function', {}).get('name', '')
                    tool_args = tool_call.get('arguments') or tool_call.get('args') or tool_call.get('function', {}).get('arguments', {})
                    tool_call_id = tool_call.get('id') or f"call_{id(tool_call)}_{iteration}"

                    if isinstance(tool_args, str):
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError:
                            tool_args = {}

                    if not tool_name:
                        logger.warning(f"[AgentHarness] 工具名称为空，将工具调用作为普通文本处理")
                        consecutive_invalid_tools += 1
                        if consecutive_invalid_tools >= 2:
                            logger.warning(f"[AgentHarness] 连续 {consecutive_invalid_tools} 次无效工具调用，强制退出")
                            full_response = f"抱歉，AI 在处理您的请求时遇到了技术问题（工具调用格式错误），请稍后再试或尝试简化您的问题。"
                            break
                        if tool_args:
                            text_content = f"[工具调用: {json.dumps(tool_args)}]"
                        else:
                            text_content = "[无法解析工具调用]"
                        full_response += text_content
                        continue

                    consecutive_invalid_tools = 0

                    permission_level = await self._check_permission(tool_name, tool_args)

                    if permission_level == 'deny':
                        logger.info(f"[AgentHarness] 工具 {tool_name} 被权限拒绝")
                        yield event_factory.build(
                            AgentEventType.TOOL_DENIED,
                            {
                                "name": tool_name,
                                "reason": "权限被拒绝",
                            },
                            iteration=iteration,
                        ).to_json()
                        tool_results.append({
                            "name": tool_name,
                            "result": "工具执行被拒绝",
                            "tool_call_id": tool_call_id
                        })
                        continue

                    if permission_level == 'ask':
                        logger.info(f"[AgentHarness] 工具 {tool_name} 需要用户确认")
                        run_context.set_state(AgentState.WAITING_PERMISSION)
                        from .permission_service import get_permission_service

                        permission_request = get_permission_service().create_request(
                            tool_name=tool_name,
                            tool_args=tool_args,
                            permission_level=permission_level,
                            user_id=self.user_id,
                            conversation_id=self.conversation_id,
                        )
                        yield event_factory.build(
                            AgentEventType.TOOL_PERMISSION_REQUIRED,
                            {
                                "name": tool_name,
                                "args": tool_args,
                                "conversation_id": self.conversation_id,
                                "request_id": permission_request.id,
                                "permission_level": permission_level,
                            },
                            iteration=iteration,
                        ).to_json()
                        result = "等待用户授权..."
                    else:
                        result, execution_metadata = await self._execute_tool_with_metadata(tool_name, tool_args)
                    if permission_level == 'ask':
                        execution_metadata = {
                            "cache_hit": False,
                            "duration_ms": 0.0,
                            "result_source": "permission_wait",
                            "status": "pending_permission",
                        }

                    run_context.record_tool_result(
                        tool_name,
                        tool_args,
                        result,
                        tool_call_id,
                        execution=execution_metadata,
                    )
                    tool_results.append({
                        "name": tool_name,
                        "result": result,
                        "tool_call_id": tool_call_id,
                        "tool_args": tool_args,
                        "tool_execution": execution_metadata,
                    })

                    tool_event_payload = self._build_tool_event_payload(
                        tool_name=tool_name,
                        tool_result=result,
                        tool_args=tool_args,
                        tool_call_id=tool_call_id,
                        execution_metadata=execution_metadata,
                    )
                    yield event_factory.build(
                        AgentEventType.TOOL_RESULT,
                        tool_event_payload,
                        iteration=iteration,
                    ).to_json()

                for result in tool_results:
                    tool_msg = ToolMessage(
                        content=result['result'],
                        tool_call_id=result.get('tool_call_id', '')
                    )
                    messages.append(tool_msg)

                direct_response = self._maybe_use_direct_tool_result(tool_results, tool_calls_from_response)
                if direct_response:
                    full_response += direct_response
                    run_context.set_state(AgentState.FINALIZING, stop_reason="tool_passthrough")
                    final_response_metadata = self._build_content_event_metadata(
                        tool_name=tool_results[0].get("name", ""),
                        tool_result=direct_response,
                        tool_args=tool_results[0].get("tool_args", {}),
                    )
                    final_response_metadata["tool_name"] = tool_results[0].get("name", "")
                    final_response_metadata["tool_call_id"] = tool_results[0].get("tool_call_id")
                    final_response_metadata["tool_spec"] = self._get_tool_event_metadata(tool_results[0].get("name", ""))
                    tool_execution = tool_results[0].get("tool_execution")
                    if isinstance(tool_execution, dict) and tool_execution:
                        final_response_metadata["tool_execution"] = tool_execution
                        final_response_metadata["cache_hit"] = tool_execution.get("cache_hit")
                        final_response_metadata["duration_ms"] = tool_execution.get("duration_ms")
                        final_response_metadata["result_source"] = tool_execution.get("result_source")
                    yield event_factory.build(
                        AgentEventType.CONTENT,
                        {"content": direct_response, **final_response_metadata},
                        iteration=iteration,
                    ).to_json()
                    break

                run_context.set_state(AgentState.OBSERVING)
                consecutive_invalid_tools = 0

            except Exception as e:
                error_msg = str(e)
                if "does not support tools" in error_msg or "status code: 400" in error_msg:
                    if use_bind_tools_this_run and iteration == 1:
                        logger.warning(f"[AgentHarness] 模型不支持工具调用，通知 orchestrator 重试")
                        run_context.set_state(AgentState.FAILED, stop_reason="tool_binding_unsupported")
                        yield event_factory.build(
                            AgentEventType.ERROR,
                            {"content": f"Model does not support tools: {error_msg}"},
                            iteration=iteration,
                        ).to_json()
                        break
                logger.error(f"[AgentHarness] 生成响应时出错: {e}")
                run_context.set_state(AgentState.FAILED, stop_reason="runtime_exception")
                yield event_factory.build(
                    AgentEventType.ERROR,
                    {"content": f"处理错误: {str(e)}"},
                    iteration=iteration,
                ).to_json()
                break

        if run_context.state not in (AgentState.FAILED, AgentState.ABORTED):
            run_context.set_state(AgentState.DONE, stop_reason=run_context.stop_reason or "completed")

        yield event_factory.build(
            AgentEventType.DONE,
            {
                "content": full_response,
                "reasoning": full_reasoning if full_reasoning else None,
                "state": run_context.state.value,
                "stop_reason": run_context.stop_reason,
                **final_response_metadata,
            },
            iteration=run_context.iteration,
        ).to_json()

    def _parse_chunk(self, chunk) -> Dict[str, Any]:
        """
        解析 chunk

        参考豆包文档：流式输出时，tool_calls 会分块返回
        需要通过 index 追踪并组装完整的工具调用
        """
        chunk_type = type(chunk).__name__

        saw_tool_call = False

        if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
            logger.info(f"[_parse_chunk] found tool_calls with data: {chunk.tool_calls}")
            for tc in chunk.tool_calls:
                self.tool_call_tracker.add_chunk(tc)
                saw_tool_call = True

        if hasattr(chunk, 'invalid_tool_calls') and chunk.invalid_tool_calls:
            logger.info(f"[_parse_chunk] found invalid_tool_calls: {chunk.invalid_tool_calls}")
            self.tool_call_tracker.add_from_invalid_tool_calls(chunk.invalid_tool_calls)
            saw_tool_call = True

        if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
            raw_tool_calls = chunk.additional_kwargs.get('tool_calls', [])
            if raw_tool_calls:
                logger.info(f"[_parse_chunk] found tool_calls in additional_kwargs: {raw_tool_calls}")
                for tc in raw_tool_calls:
                    self.tool_call_tracker.add_chunk(tc)
                    saw_tool_call = True

        if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
            finish_reason = chunk.response_metadata.get('finish_reason')
            if finish_reason:
                logger.info(f"[_parse_chunk] finish_reason: {finish_reason}")

        if hasattr(chunk, 'content') and chunk.content:
            reasoning = self._extract_reasoning(chunk)
            if reasoning:
                return {"type": "reasoning", "content": reasoning}
            return {"type": "content", "content": chunk.content}

        if saw_tool_call:
            return {"type": "tool_calls", "tool_calls": []}

        return {"type": "content", "content": ""}

    def _normalize_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """规范化工具调用格式，兼容豆包模型的特殊格式"""
        normalized = []
        for tc in tool_calls:
            if isinstance(tc, dict):
                name = tc.get('function', {}).get('name') or tc.get('Name') or tc.get('name', '')
                arguments = tc.get('function', {}).get('arguments') or tc.get('args') or tc.get('arguments', {})
                tool_id = tc.get('id') or tc.get('Id') or None

                normalized.append({
                    "name": name,
                    "arguments": self.tool_call_tracker.parse_arguments(arguments),
                    "id": tool_id
                })
            elif hasattr(tc, 'function'):
                name = getattr(tc.function, 'name', '') if hasattr(tc, 'function') else ''
                arguments = getattr(tc.function, 'arguments', {}) if hasattr(tc, 'function') else {}
                tool_id = getattr(tc, 'id', None)
                normalized.append({
                    "name": name,
                    "arguments": self.tool_call_tracker.parse_arguments(arguments),
                    "id": tool_id
                })
        return normalized

    def _extract_reasoning(self, chunk) -> str:
        """从 chunk 中提取推理内容"""
        reasoning = ""

        if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
            metadata = chunk.response_metadata
            reasoning = metadata.get('reasoning_content', '') or metadata.get('reasoning', '')

        if not reasoning and hasattr(chunk, 'raw') and chunk.raw:
            try:
                raw = chunk.raw
                if isinstance(raw, dict):
                    choices = raw.get('choices', [{}])[0] if raw.get('choices') else {}
                    delta = choices.get('delta', {})
                    reasoning = delta.get('reasoning_content', '')
            except Exception:
                pass

        return reasoning

    async def _check_permission(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        检查工具调用权限

        Returns:
            'auto': 自动批准
            'ask': 需要用户确认
            'deny': 拒绝执行
        """
        from .tools.langchain_tools import get_tool_permission
        return get_tool_permission(tool_name)

    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """执行工具并仅返回结果字符串。"""
        result, _ = await self._execute_tool_with_metadata(tool_name, args)
        return result

    async def _execute_tool_with_metadata(self, tool_name: str, args: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """执行工具并返回结果与执行元数据。"""
        tool = self.tool_map.get(tool_name)

        if not tool:
            logger.warning(f"[AgentHarness] 工具不存在: {tool_name}")
            return (
                f"工具 '{tool_name}' 不存在",
                {
                    "cache_hit": False,
                    "duration_ms": 0.0,
                    "result_source": "missing_tool",
                    "status": "missing_tool",
                },
            )

        started_at = time.perf_counter()
        try:
            tool_spec = None
            cached_result = None
            cache_ttl = None
            try:
                from .tool_registry import get_registry
                from agent_framework.tool_cache import get_tool_result_cache
            except ModuleNotFoundError:  # pragma: no cover - package import compatibility
                from backend.harness.tool_registry import get_registry
                from backend.agent_framework.tool_cache import get_tool_result_cache

            try:
                tool_spec = get_registry().get_tool_spec(tool_name)
                if tool_spec and tool_spec.supports_cache:
                    cache_ttl = tool_spec.cache_ttl_seconds or 60.0
                    cached_result = get_tool_result_cache().get(tool_name, args)
                    if cached_result is not None:
                        logger.info(f"[AgentHarness] 工具 {tool_name} 命中通用缓存")
                        return (
                            cached_result,
                            {
                                "cache_hit": True,
                                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                                "result_source": "runtime_cache",
                                "status": "cached",
                            },
                        )
            except Exception as e:
                logger.debug(f"[AgentHarness] 读取工具缓存失败: {e}")

            if hasattr(tool, 'ainvoke'):
                result = await tool.ainvoke(args)
            elif hasattr(tool, 'invoke'):
                result = tool.invoke(args)
                if asyncio.iscoroutine(result):
                    result = await result
            elif hasattr(tool, 'execute'):
                result = tool.execute(**args)
                if asyncio.iscoroutine(result):
                    result = await result
            elif callable(tool):
                result = tool(**args)
                if asyncio.iscoroutine(result):
                    result = await result
            else:
                result = "工具不可调用"

            result = str(result)
            if (
                tool_spec
                and tool_spec.supports_cache
                and cache_ttl
                and not result.startswith("执行错误:")
            ):
                try:
                    get_tool_result_cache().set(tool_name, args, result, cache_ttl)
                except Exception as e:
                    logger.debug(f"[AgentHarness] 写入工具缓存失败: {e}")
            logger.info(f"[AgentHarness] 工具 {tool_name} 执行成功")
            return (
                result,
                {
                    "cache_hit": False,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                    "result_source": "tool",
                    "status": "ok",
                },
            )
        except Exception as e:
            logger.error(f"[AgentHarness] 工具 {tool_name} 执行失败: {e}")
            return (
                f"执行错误: {str(e)}",
                {
                    "cache_hit": False,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                    "result_source": "tool_error",
                    "status": "error",
                },
            )

    def _get_tool_event_metadata(self, tool_name: str) -> Dict[str, Any]:
        """获取面向前后端事件的工具元数据。"""
        try:
            from .tool_registry import get_registry

            tool_spec = get_registry().get_tool_spec(tool_name)
            if tool_spec:
                return tool_spec.to_dict()
        except Exception as e:
            logger.debug(f"[AgentHarness] 获取工具元数据失败: {e}")

        return {
            "name": tool_name,
            "render_mode": "plain_text",
            "permission_level": "auto",
        }

    def _build_tool_event_payload(
        self,
        *,
        tool_name: str,
        tool_result: str,
        tool_args: Dict[str, Any],
        tool_call_id: str,
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build a tool_result event payload with structured rendering metadata."""
        tool_spec = self._get_tool_event_metadata(tool_name)
        payload: Dict[str, Any] = {
            "name": tool_name,
            "result": tool_result,
            "tool_call_id": tool_call_id,
            "tool_spec": tool_spec,
            "render_mode": tool_spec.get("render_mode"),
            "card_schema": tool_spec.get("card_schema"),
        }
        if execution_metadata:
            payload["tool_execution"] = dict(execution_metadata)
            payload["cache_hit"] = execution_metadata.get("cache_hit")
            payload["duration_ms"] = execution_metadata.get("duration_ms")
            payload["result_source"] = execution_metadata.get("result_source")
            payload["status"] = execution_metadata.get("status")
        payload.update(self._build_content_event_metadata(tool_name, tool_result, tool_args))
        return payload

    def _build_content_event_metadata(
        self,
        tool_name: str,
        tool_result: str,
        tool_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build rendering metadata for assistant content events."""
        metadata: Dict[str, Any] = {}

        try:
            if tool_name == "search" and isinstance(tool_args, dict):
                query = str(tool_args.get("query", "") or "")
                if query:
                    from services.weather_service import weather_service
                    from agent_framework.card_schemas import build_datetime_card_from_text, build_search_summary_card

                    if weather_service.is_weather_query(query) and tool_result.startswith("天气查询结果（"):
                        card = weather_service.build_weather_card_from_text(tool_result)
                        if card:
                            metadata["render_mode"] = "structured_card"
                            metadata["card"] = card
                            metadata["card_schema"] = card.get("schema")
                            return metadata

                    datetime_card = build_datetime_card_from_text(tool_result)
                    if datetime_card:
                        metadata["render_mode"] = "structured_card"
                        metadata["card"] = datetime_card
                        metadata["card_schema"] = datetime_card.get("schema")
                        return metadata

                    search_card = build_search_summary_card(query, tool_result)
                    if search_card:
                        metadata["render_mode"] = "structured_card"
                        metadata["card"] = search_card
                        metadata["card_schema"] = search_card.get("schema")
                        return metadata

            if tool_name == "get_current_datetime":
                from agent_framework.card_schemas import build_datetime_card_from_text

                card = build_datetime_card_from_text(tool_result)
                if card:
                    metadata["render_mode"] = "structured_card"
                    metadata["card"] = card
                    metadata["card_schema"] = card.get("schema")
        except Exception as e:
            logger.debug(f"[AgentHarness] 构建 structured_card 元数据失败: {e}")

        return metadata

    def _maybe_use_direct_tool_result(self, tool_results: List[Dict[str, Any]], tool_calls: List[Dict[str, Any]]) -> Optional[str]:
        """对确定性强的工具结果直接返回，避免二次模型改写。"""
        if len(tool_results) != 1 or len(tool_calls) != 1:
            return None

        tool_name = tool_results[0].get("name")
        tool_result = str(tool_results[0].get("result", "") or "")
        tool_args = tool_calls[0].get("arguments", {})

        if not isinstance(tool_args, dict):
            return None

        if not tool_name or not tool_result or tool_result.startswith("执行错误:"):
            return None

        query = str(tool_args.get("query", "") or "")

        try:
            from .tool_registry import get_registry

            tool_spec = get_registry().get_tool_spec(tool_name)
            if not tool_spec:
                return None

            if tool_spec.passthrough_strategy == "always" and not tool_spec.safe_to_rephrase:
                logger.info("[AgentHarness] 工具 %s 命中 always passthrough，直接返回结果", tool_name)
                return tool_result

            if tool_spec.passthrough_strategy == "weather_query":
                from services.weather_service import weather_service

                if query and weather_service.is_weather_query(query) and tool_result.startswith("天气查询结果（"):
                    logger.info("[AgentHarness] 检测到天气查询，直接返回工具结果，跳过二次模型改写")
                    return tool_result

            if tool_spec.deterministic and not tool_spec.safe_to_rephrase and tool_spec.passthrough_strategy == "always":
                return tool_result
        except Exception as e:
            logger.debug(f"[AgentHarness] 直接返回工具结果判断失败: {e}")

        return None
