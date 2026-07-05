"""
Human-in-the-Loop - 中断与恢复

对标 LangGraph 的 interrupt() + Command(resume=) 模式。
节点函数中调用 interrupt() 暂停执行，外部通过 Command(resume=...) 恢复。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class InterruptError(Exception):
    """中断执行，等待人工输入。由 interrupt() 抛出。"""
    def __init__(self, value: Any = None):
        self.value = value
        super().__init__(f"Interrupted: {value}")


def interrupt(value: Any = None) -> Any:
    """在节点函数中调用，暂停执行并等待人工输入。

    Usage:
        def approval_node(state):
            approved = interrupt("Do you approve this action?")
            return {"approved": approved}
    """
    raise InterruptError(value)


@dataclass
class Command:
    """恢复执行的命令。

    Usage:
        graph.invoke(Command(resume=True), config=config)
        graph.invoke(Command(resume="approved"), config=config)
    """
    resume: Any = None
    update: dict | None = None
    goto: str | None = None

    def to_dict(self) -> dict:
        result = {}
        if self.resume is not None:
            result["resume"] = self.resume
        if self.update is not None:
            result["update"] = self.update
        if self.goto is not None:
            result["goto"] = self.goto
        return result
