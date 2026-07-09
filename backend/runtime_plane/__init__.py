"""
Runtime Plane（运行层面）

MyPrivateAgent 的运行层集成能力，参照 LangGraph + AgentRun 设计。

核心组件：
- graph/: 状态图执行引擎（StateGraph, CompiledGraph, Checkpoint, Streaming）
- tools/: 工具注册与管理（@tool, ToolRegistry）
- agents/: 智能体定义与编排（Agent, AgentOrchestrator）
- governance_bridge.py: 运行层→治理层桥接
- adapters/: 外部框架适配器
- gateway/: Intent Router, Agent Registry
"""

from .agents import Agent, AgentOrchestrator
from .adapters import ExecutionAdapter, SimpleAgentAdapter
from .contracts import AgentManifest, ExecutionEvent, ExecutionRequest, ExecutionResult
from .governance_bridge import GovernanceBridge
from .tools import ToolDef, ToolRegistry, tool

__all__ = [
    "Agent", "AgentOrchestrator",
    "ExecutionAdapter", "SimpleAgentAdapter",
    "ExecutionRequest", "ExecutionEvent", "ExecutionResult", "AgentManifest",
    "ToolDef", "ToolRegistry", "tool",
    "GovernanceBridge",
]
