# Framework Phase 13 实施记录

## 目标

继续把 `chat.py` 从“大路由文件”收口成更像 server adapter 的薄层，并修复框架化过程中暴露出来的导入边界问题。

## 本次改动

### 1. 抽出 Chat Service

新增 `backend/services/chat_service.py`，承接原先写在 `chat.py` 中的路由辅助逻辑：

- `extract_event_field()`
- `get_or_create_conversation()`
- `save_assistant_message()`
- `record_learning_if_possible()`
- `collect_orchestrator_response()`
- `stream_orchestrator_events()`

这样 `chat.py` 现在更接近真正的接口层，只负责：

- 鉴权
- 入参
- 调用 orchestrator
- 返回 HTTP/SSE 响应

### 2. 修复 services 包过重的问题

此前 `backend/services/__init__.py` 会在导入包时立刻连带导入 `chat_service`，而 `chat_service` 又会继续加载 `LearningRecorder / models`，导致：

- 测试导入路径变重
- 非聊天场景导入 `backend.services.weather_service` 时也会被迫加载一堆无关依赖

现在 `backend/services/__init__.py` 改回轻量包文件，不再做重型聚合导入。

### 3. Provider Backend 改成惰性导入

`backend/agent_framework/provider_backends.py` 不再在模块顶层就导入：

- `langchain_openai`
- `langchain_ollama`

而是改成在真正创建模型实例时才导入。  
这让：

- 单元测试不再因为可选依赖缺失而失败
- 框架拆包时更容易处理 optional dependencies

### 4. 补充最小测试

新增 `tests/agent_framework/test_chat_service.py`，覆盖：

- `extract_event_field()`
- `collect_orchestrator_response()`

同时更新 CI，把该测试纳入默认回归集合。

## 验证

- `py_compile` 通过
- `python -m unittest ... test_chat_service` 通过
- 当前 runtime 测试共 17 项，全部通过

## 结果

Phase 13 后，聊天路由层和服务层的边界更清晰，导入图也更轻。这一步对“把当前项目继续抽成可复用框架包”是必要前置，因为它减少了隐式耦合和非必要依赖传播。
