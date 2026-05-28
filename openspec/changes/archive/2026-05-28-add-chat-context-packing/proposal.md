## Why

当前主聊天链路会持久化会话消息，但模型请求只包含当前用户输入和运行时系统上下文；同一 `conversation_id` 的历史没有进入推理上下文。长会话因此缺少连续性，同时已有 `ContextWindow` / `ContextCompactionService` 没有形成企业级可验证的上下文预算边界。

收口对象：主聊天请求的会话上下文打包、token 预算裁剪、摘要注入边界。非目标：不引入外部 agent 框架，不改前端消息展示协议，不实现完整长期记忆检索系统，不改变 Runtime Surface / Governance Timeline payload shape。

## What Changes

- Add a backend chat context packing boundary that builds model-ready history from persisted conversation messages.
- Include compact summary text for older messages when history exceeds the recent-message window.
- Preserve recent conversation turns and current user message while respecting a configurable token budget.
- Wire the packed context into the existing orchestrator message construction before `AgentHarness.run()`.
- Keep runtime knowledge, runtime skills, agent memory, and subagent prompts as system context layers ahead of packed conversation history.
- Add focused backend tests for summary creation, recent-history preservation, and orchestrator wiring.

## Capabilities

### New Capabilities
- `chat-context-packing`: Defines how main chat assembles persisted conversation history, compact summary, recent turns, and the current user message into a bounded model input.

### Modified Capabilities

## Impact

- Backend code:
  - `backend/services/chat_context_service.py` or equivalent new service boundary.
  - `backend/services/chat_service.py` to pass persisted history into the orchestrator.
  - `backend/orchestrator.py` to accept packed history and build model messages from it.
  - Focused tests under `tests/agent_framework/`.
- Runtime contracts:
  - No Runtime Surface payload change.
  - No Governance Timeline payload change.
  - Main chat execution semantics change: same-conversation history becomes part of the model input through a bounded backend read/packing boundary.
- Frontend:
  - No direct UI contract change.
- Dependencies:
  - Reuse existing LangChain message classes and `tiktoken` fallback approach already present in the backend.
