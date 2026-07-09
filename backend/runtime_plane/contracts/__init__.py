"""ExecutionAdapter 标准合同定义。"""

from .execution import AgentManifest, ExecutionEvent, ExecutionRequest, ExecutionResult

__all__ = [
    "ExecutionRequest",
    "ExecutionEvent",
    "ExecutionResult",
    "AgentManifest",
]
