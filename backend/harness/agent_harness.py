"""
AgentHarness - 参考 Claude Code 的核心 Agent 循环
"""
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StreamChunk:
    """流式输出块"""
    def __init__(self, type: str, content: str = "", reasoning: str = ""):
        self.type = type  # 'reasoning', 'content', 'done', 'error'
        self.content = content
        self.reasoning = reasoning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "reasoning": self.reasoning
        }


class AgentHarness:
    """
    Agent 核心循环 - 参考 Claude Code 架构

    简单的 while 循环 + 工具调用模式：
    1. 生成响应
    2. 检查是否需要工具调用
    3. 执行工具
    4. 继续循环或返回结果
    """

    def __init__(
        self,
        model,
        tools: List[Any],
        model_name: str = "unknown"
    ):
        self.model = model
        self.tools = tools or []
        self.model_name = model_name
        self.max_iterations = 10  # 防止无限循环

        # 创建工具名称到工具的映射
        self.tool_map = {}
        for tool in self.tools:
            if hasattr(tool, 'name'):
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

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"[AgentHarness] 第 {iteration} 次迭代")

            # 1. 生成响应
            response_content = ""
            reasoning_content = ""

            try:
                # 检查模型是否支持流式
                if hasattr(self.model, 'astream'):
                    async for chunk in self.model.astream(messages):
                        # 处理流式输出
                        if hasattr(chunk, 'content') and chunk.content:
                            response_content += chunk.content
                            yield json.dumps({
                                "type": "content",
                                "content": chunk.content
                            }) + "\n"

                        # 处理推理内容（对于支持推理的模型）
                        reasoning = self._extract_reasoning(chunk)
                        if reasoning:
                            reasoning_content += reasoning
                            yield json.dumps({
                                "type": "reasoning",
                                "content": reasoning
                            }) + "\n"
                else:
                    # 非流式模型
                    response = await self.model.ainvoke(messages)
                    response_content = response.content if hasattr(response, 'content') else str(response)
                    yield json.dumps({
                        "type": "content",
                        "content": response_content
                    }) + "\n"

                # 2. 检查是否有工具调用
                tool_calls = self._extract_tool_calls(response_content)

                if not tool_calls:
                    # 没有工具调用，返回结果
                    full_response += response_content
                    break

                # 3. 执行工具调用
                logger.info(f"[AgentHarness] 检测到 {len(tool_calls)} 个工具调用")
                tool_results = []

                for tool_call in tool_calls:
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('arguments', {})

                    # 查找工具
                    tool = self.tool_map.get(tool_name)
                    if not tool:
                        tool_results.append({
                            "name": tool_name,
                            "result": f"工具 '{tool_name}' 不存在"
                        })
                        continue

                    # 执行工具
                    try:
                        if hasattr(tool, 'invoke'):
                            result = await tool.invoke(tool_args)
                        elif hasattr(tool, 'execute'):
                            result = await tool.execute(**tool_args)
                        else:
                            result = str(tool(**tool_args) if callable(tool) else "工具不可调用")

                        tool_results.append({
                            "name": tool_name,
                            "result": result
                        })

                        logger.info(f"[AgentHarness] 工具 {tool_name} 执行成功")

                    except Exception as e:
                        logger.error(f"[AgentHarness] 工具 {tool_name} 执行失败: {e}")
                        tool_results.append({
                            "name": tool_name,
                            "result": f"执行错误: {str(e)}"
                        })

                # 4. 添加工具结果到消息
                for tool_result in tool_results:
                    from langchain_core.messages import HumanMessage, AIMessage
                    messages.append(AIMessage(content=f"工具调用: {tool_result['name']}\n结果: {tool_result['result']}"))

            except Exception as e:
                logger.error(f"[AgentHarness] 生成响应时出错: {e}")
                yield json.dumps({
                    "type": "error",
                    "content": f"处理错误: {str(e)}"
                }) + "\n"
                break

        # 发送完成信号
        yield json.dumps({
            "type": "done",
            "content": full_response,
            "reasoning": reasoning_content if reasoning_content else None
        }) + "\n"

    def _extract_reasoning(self, chunk) -> str:
        """从 chunk 中提取推理内容"""
        reasoning = ""

        # 方法1: 从 response_metadata 提取
        if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
            metadata = chunk.response_metadata
            reasoning = metadata.get('reasoning_content', '') or metadata.get('reasoning', '')

        # 方法2: 从 raw 响应提取
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

    def _extract_tool_calls(self, text: str) -> List[Dict]:
        """从文本中提取工具调用（兼容多种格式）"""
        tool_calls = []

        # 尝试 JSON 格式
        try:
            # 检查是否包含 JSON 格式的工具调用
            if '```json' in text:
                json_start = text.find('```json') + 7
                json_end = text.find('```', json_start)
                if json_end > json_start:
                    json_str = text[json_start:json_end].strip()
                    data = json.loads(json_str)
                    if isinstance(data, dict) and 'tool_calls' in data:
                        tool_calls = data['tool_calls']
                    elif isinstance(data, list):
                        tool_calls = data
        except Exception as e:
            logger.debug(f"[AgentHarness] JSON 解析工具调用失败: {e}")

        # 尝试 markdown 格式
        if not tool_calls and '```' in text:
            try:
                code_start = text.find('```') + 3
                code_end = text.find('```', code_start)
                if code_end > code_start:
                    code = text[code_start:code_end].strip()
                    if code.startswith('{') or code.startswith('['):
                        data = json.loads(code)
                        if isinstance(data, dict) and 'tool_calls' in data:
                            tool_calls = data['tool_calls']
            except Exception:
                pass

        return tool_calls
