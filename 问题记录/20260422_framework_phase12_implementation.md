# Framework Phase 12 实施记录

## 目标

继续推进 `P0` 收口，把 `backend/routers/chat.py` 中残留的旧 LangGraph 执行链移除，让聊天主路径统一回到：

- `SimplifiedOrchestrator`
- `AgentHarness`
- `AgentEvent`

## 本次改动

### 1. 移除 `chat.py` 内的旧执行器残留

删除了旧的：

- `StateGraph`
- `tool_node`
- `create_graph`
- `graph_cache`
- `get_graph`
- 基于 `ChatOllama` / `ARK API` / LangGraph 的多分支旧非流式路径

这意味着 `chat.py` 不再同时维护两套执行框架。

### 2. 统一流式与非流式入口

新增辅助函数：

- `_get_or_create_conversation()`
- `_save_assistant_message()`
- `_record_learning_if_possible()`
- `_collect_orchestrator_response()`

现在：

- `/api/chat` 流式接口统一走 `orchestrator.process_message()`
- `/api/chat/non-stream` 非流式接口也统一走 `orchestrator.process_message()`，只是在路由层聚合最终内容

### 3. 修复新会话时的 orchestrator 传参

此前流式接口在新建会话后仍使用 `request.conversation_id` 初始化 orchestrator，可能传入 `None`。

现在统一改为使用真实的 `conversation.id`。

## 结果

Phase 12 后，聊天接口层不再分叉到旧 LangGraph 执行器，真正形成了“路由层 -> Orchestrator -> AgentHarness”的单一执行链。这比继续保留兼容分支更符合可复用 agent runtime 的最佳实践。

## 下一步建议

下一阶段不应再继续改执行器本身，而应把 `chat.py` 里的会话持久化、学习记录、SSE 转发拆成更清晰的 service 层职责。
