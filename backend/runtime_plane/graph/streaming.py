"""
Streaming - 流式输出

对标 LangGraph 的 7 种 stream_mode。
支持 updates / values / messages / events / interrupt 五种模式。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator


class StreamMode(str, Enum):
    """流式输出模式。"""
    UPDATES = "updates"      # 节点级状态增量
    VALUES = "values"        # 完整状态快照
    MESSAGES = "messages"    # token 级 LLM 输出
    EVENTS = "events"        # 治理事件流
    INTERRUPT = "interrupt"  # 中断事件
    ERROR = "error"          # 错误事件


@dataclass(frozen=True)
class StreamChunk:
    """流式输出的一个 chunk。"""
    mode: StreamMode
    node_name: str
    data: dict[str, Any]
    step: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "type": self.mode.value,
            "node": self.node_name,
            "data": self.data,
            "step": self.step,
            "timestamp": self.timestamp,
        }

    def to_sse(self) -> str:
        """转换为 SSE 格式。"""
        import json
        return f"data: {json.dumps(self.to_dict(), ensure_ascii=False)}\n\n"


class EventStream:
    """事件流包装器，支持同步迭代和异步迭代。"""

    def __init__(self, chunks: Iterator[StreamChunk] | None = None):
        self._chunks = chunks or iter([])
        self._buffer: list[StreamChunk] = []
        self._interrupts: list[dict] = []

    def __iter__(self) -> Iterator[StreamChunk]:
        for chunk in self._chunks:
            self._buffer.append(chunk)
            if chunk.mode == StreamMode.INTERRUPT:
                self._interrupts.append(chunk.data.get("interrupt", {}))
            yield chunk

    async def __aiter__(self):
        for chunk in self:
            yield chunk

    @property
    def interrupts(self) -> list[dict]:
        """获取所有中断事件。"""
        return list(self._interrupts)

    @property
    def events(self) -> list[StreamChunk]:
        """获取所有已缓存的事件。"""
        return list(self._buffer)

    def collect(self) -> dict:
        """收集所有事件，返回最终状态。"""
        final_state = None
        for chunk in self:
            if chunk.mode == StreamMode.VALUES:
                final_state = chunk.data.get("final_state")
        return final_state or {}
