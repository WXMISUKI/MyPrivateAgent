"""
Graph Engine - StateGraph + CompiledGraph 图编排引擎

对标 LangGraph 的 StateGraph API：
- add_node: 添加节点
- add_edge: 添加边
- add_conditional_edges: 添加条件边
- compile: 编译图为可执行 CompiledGraph
- invoke/stream: 同步/流式执行

支持任意拓扑：线性、分支、循环、并行。
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Literal

from .checkpoint import Checkpoint, CheckpointStore, InMemoryCheckpointStore
from .interrupt import InterruptError, interrupt
from .nodes import NodeDef
from .state import MessagesState, merge_state
from .streaming import StreamChunk, StreamMode

logger = logging.getLogger(__name__)

START = "__start__"
END = "__end__"


# ---------------------------------------------------------------------------
# Edge definitions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Edge:
    """普通边：从 src 到 dst。"""
    src: str
    dst: str


@dataclass(frozen=True)
class ConditionalEdge:
    """条件边：从 src 出发，根据 condition 函数返回值选择目标。"""
    src: str
    condition: Callable[[dict], str]   # 返回目标节点名
    targets: list[str]                  # 可能的目标节点列表（用于编译时验证）


# ---------------------------------------------------------------------------
# StateGraph - 图构建器
# ---------------------------------------------------------------------------

class StateGraph:
    """状态图构建器。用法与 LangGraph 一致。"""

    def __init__(self, state_schema: type = MessagesState):
        self.state_schema = state_schema
        self._nodes: dict[str, NodeDef] = {}
        self._edges: list[Edge] = []
        self._conditional_edges: list[ConditionalEdge] = []

    def add_node(self, name: str, func: Callable, **kwargs) -> "StateGraph":
        """添加节点。"""
        if name in (START, END):
            raise ValueError(f"Cannot add node with reserved name '{name}'")
        if name in self._nodes:
            raise ValueError(f"Node '{name}' already exists")
        self._nodes[name] = NodeDef(
            name=name,
            func=func,
            node_type=kwargs.get("node_type", "custom"),
            metadata=kwargs.get("metadata", {}),
        )
        return self

    def add_edge(self, src: str, dst: str) -> "StateGraph":
        """添加普通边。"""
        self._edges.append(Edge(src=src, dst=dst))
        return self

    def add_conditional_edges(
        self,
        src: str,
        condition: Callable[[dict], str],
        targets: list[str] | None = None,
    ) -> "StateGraph":
        """添加条件边。condition 函数返回下一个节点名。"""
        self._conditional_edges.append(ConditionalEdge(
            src=src,
            condition=condition,
            targets=targets or [],
        ))
        return self

    def compile(self, *, checkpointer: CheckpointStore | None = None) -> "CompiledGraph":
        """编译图为可执行对象。"""
        self._validate()
        return CompiledGraph(
            state_schema=self.state_schema,
            nodes=dict(self._nodes),
            edges=list(self._edges),
            conditional_edges=list(self._conditional_edges),
            checkpointer=checkpointer or InMemoryCheckpointStore(),
        )

    def _validate(self):
        """编译时验证：检查边引用的节点是否存在。"""
        node_names = set(self._nodes.keys()) | {START, END}
        for edge in self._edges:
            if edge.src not in node_names:
                raise ValueError(f"Edge source '{edge.src}' not found in nodes")
            if edge.dst not in node_names:
                raise ValueError(f"Edge target '{edge.dst}' not found in nodes")
        for cedge in self._conditional_edges:
            if cedge.src not in node_names:
                raise ValueError(f"Conditional edge source '{cedge.src}' not found in nodes")
            for t in cedge.targets:
                if t not in node_names:
                    raise ValueError(f"Conditional edge target '{t}' not found in nodes")


# ---------------------------------------------------------------------------
# CompiledGraph - 编译后的可执行图
# ---------------------------------------------------------------------------

class CompiledGraph:
    """编译后的状态图，支持 invoke / stream / ainvoke / astream。"""

    def __init__(
        self,
        state_schema: type,
        nodes: dict[str, NodeDef],
        edges: list[Edge],
        conditional_edges: list[ConditionalEdge],
        checkpointer: CheckpointStore,
    ):
        self.state_schema = state_schema
        self.nodes = nodes
        self.edges = edges
        self.conditional_edges = conditional_edges
        self.checkpointer = checkpointer

        # 构建邻接表
        self._adjacency: dict[str, list[str]] = {}
        for edge in edges:
            self._adjacency.setdefault(edge.src, []).append(edge.dst)

    def invoke(
        self,
        input_data: dict,
        config: dict | None = None,
    ) -> dict:
        """同步执行图。"""
        thread_id = (config or {}).get("configurable", {}).get("thread_id", str(uuid.uuid4()))
        state = self._init_state(input_data)
        events: list[dict] = []

        for chunk in self._run(state, thread_id):
            events.append(chunk)

        # 返回最终状态
        return state

    def stream(
        self,
        input_data: dict,
        config: dict | None = None,
        mode: str = "updates",
    ) -> Iterator[StreamChunk]:
        """流式执行图。"""
        thread_id = (config or {}).get("configurable", {}).get("thread_id", str(uuid.uuid4()))
        state = self._init_state(input_data)

        yield from self._run(state, thread_id, stream_mode=mode)

    async def ainvoke(self, input_data: dict, config: dict | None = None) -> dict:
        """异步执行图（当前用同步实现包装）。"""
        return self.invoke(input_data, config)

    async def astream(self, input_data: dict, config: dict | None = None, mode: str = "updates"):
        """异步流式执行图。"""
        for chunk in self.stream(input_data, config, mode):
            yield chunk

    def _init_state(self, input_data: dict) -> dict:
        """初始化状态。"""
        state = {}
        # 用输入数据填充
        for key, value in input_data.items():
            state[key] = value
        # 确保 messages 是列表格式
        if "messages" in state:
            msgs = state["messages"]
            if isinstance(msgs, str):
                state["messages"] = [{"role": "user", "content": msgs}]
            elif isinstance(msgs, tuple) and len(msgs) == 2:
                state["messages"] = [{"role": msgs[0], "content": msgs[1]}]
            elif not isinstance(msgs, list):
                state["messages"] = [msgs]
        return state

    def _run(
        self,
        state: dict,
        thread_id: str,
        stream_mode: str = "updates",
    ) -> Iterator[StreamChunk]:
        """核心执行循环。"""
        current_node = START
        max_steps = 100  # 防止无限循环
        step = 0

        while current_node != END and step < max_steps:
            step += 1

            # 保存 checkpoint
            self.checkpointer.save(thread_id, Checkpoint(
                thread_id=thread_id,
                step=step,
                state=dict(state),
                current_node=current_node,
            ))

            if current_node == START:
                # 从 START 出发，找第一个目标
                next_node = self._get_next_node(START, state)
                if next_node is None:
                    break
                current_node = next_node
                continue

            # 执行当前节点
            node_def = self.nodes.get(current_node)
            if node_def is None:
                logger.error(f"Node '{current_node}' not found")
                break

            logger.info(f"Executing node '{current_node}' (step {step})")

            try:
                result = node_def.func(state)
            except InterruptError as e:
                # Human-in-the-loop 中断
                yield StreamChunk(
                    mode=StreamMode.INTERRUPT,
                    node_name=current_node,
                    data={"interrupt": {"value": e.value, "node": current_node}},
                    step=step,
                )
                return
            except Exception as e:
                logger.error(f"Node '{current_node}' error: {e}")
                state["error"] = str(e)
                yield StreamChunk(
                    mode=StreamMode.ERROR,
                    node_name=current_node,
                    data={"error": str(e)},
                    step=step,
                )
                break

            # 合并结果到状态（原地更新）
            if result:
                merged = merge_state(self.state_schema, state, result)
                state.clear()
                state.update(merged)

            # 输出流式 chunk
            yield StreamChunk(
                mode=StreamMode.UPDATES,
                node_name=current_node,
                data={"state_update": result or {}},
                step=step,
            )

            # 保存执行后的 checkpoint
            self.checkpointer.save(thread_id, Checkpoint(
                thread_id=thread_id,
                step=step,
                state=dict(state),
                current_node=current_node,
            ))

            # 确定下一个节点
            next_node = self._get_next_node(current_node, state)
            if next_node is None:
                break
            current_node = next_node

        # 执行完成
        yield StreamChunk(
            mode=StreamMode.VALUES,
            node_name=END,
            data={"final_state": dict(state)},
            step=step,
        )

    def _get_next_node(self, current: str, state: dict) -> str | None:
        """确定下一个节点。优先检查条件边，再检查普通边。"""
        # 检查条件边
        for cedge in self.conditional_edges:
            if cedge.src == current:
                try:
                    target = cedge.condition(state)
                    if target == END:
                        return END
                    if target in self.nodes:
                        return target
                    logger.warning(f"Conditional edge returned unknown target '{target}'")
                except Exception as e:
                    logger.error(f"Condition function error: {e}")

        # 检查普通边
        targets = self._adjacency.get(current, [])
        if targets:
            return targets[0]  # 取第一个（单目标边）

        # 没有出边，结束
        return END
