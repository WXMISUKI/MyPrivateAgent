"""
Harness 模块 - 参考 Claude Code 的 Agent Harness 架构
"""
from .agent_harness import AgentHarness, StreamChunk
from .tool_registry import (
    ToolRegistry, BaseTool, PermissionLevel,
    global_tool_registry, get_registry,
    register_default_tools, register_langchain_tools
)
from .model_adapter import ModelAdapter, OllamaAdapter, create_adapter
from .permission_service import PermissionService, permission_service, get_permission_service
from .context_manager import ContextManager, ContextWindow, Message, global_context_manager, get_context_manager
from .memory_manager import MemoryManager, SessionState, SessionInfo, memory_manager, get_memory_manager

__all__ = [
    'AgentHarness',
    'StreamChunk',
    'ToolRegistry',
    'BaseTool',
    'PermissionLevel',
    'global_tool_registry',
    'get_registry',
    'register_default_tools',
    'register_langchain_tools',
    'ModelAdapter',
    'OllamaAdapter',
    'create_adapter',
    'PermissionService',
    'permission_service',
    'get_permission_service',
    'ContextManager',
    'ContextWindow',
    'Message',
    'global_context_manager',
    'get_context_manager',
    'MemoryManager',
    'SessionState',
    'SessionInfo',
    'memory_manager',
    'get_memory_manager',
]
