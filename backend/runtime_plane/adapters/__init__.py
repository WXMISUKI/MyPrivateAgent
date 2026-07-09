"""
外部框架与本地运行层适配器。
"""

from .base import ExecutionAdapter
from .simple_agent import SimpleAgentAdapter

__all__ = [
    "ExecutionAdapter",
    "SimpleAgentAdapter",
]
