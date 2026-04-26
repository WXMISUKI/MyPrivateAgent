# Framework Phase 15 实施记录

## 目标

继续推进 `agent-server` 方向的可复用性，重点解决两类问题：

1. 会话路由仍然直接承载 CRUD / 搜索逻辑
2. `backend` 包在 package import 场景下仍存在大量脚本式绝对导入

## 本次改动

### 1. 抽出 Conversation Service

新增 `backend/services/conversation_service.py`，收口会话相关逻辑：

- `list_user_conversations()`
- `get_owned_conversation()`
- `search_conversations()`
- `search_messages()`
- `create_conversation()`
- `update_conversation()`
- `delete_conversation()`

`backend/routers/conversations.py` 现在只负责：

- HTTP 参数
- 鉴权
- 404 语义
- 调用 service

同时移除了已经失效的 `clear_graph_cache` 依赖。

### 2. 补齐 package import 兼容

对以下模块补充了“双路径导入”兼容：

- `backend/database.py`
- `backend/auth.py`
- `backend/models.py`
- `backend/model_router.py`
- `backend/task_evaluator.py`
- `backend/orchestrator.py`
- `backend/harness/agent_harness.py`
- `backend/harness/tool_registry.py`
- `backend/harness/tools/langchain_tools.py`
- `backend/harness/tools/search_tool.py`
- `backend/routers/*`

这让 `backend.routers` 可以作为 package 被稳定导入，而不再要求必须从 `backend/` 目录脚本式启动。

### 3. 补充测试

新增：

- `tests/agent_framework/test_conversation_service.py`
- `tests/agent_framework/test_router_imports.py`

覆盖：

- 会话服务更新与搜索结果格式
- `backend.routers` 包导入稳定性

### 4. 顺手清理基础 warning

`backend/database.py` 改为使用 `sqlalchemy.orm.declarative_base()`，消除 SQLAlchemy 2.x 的弃用 warning。

## 验证

- `backend.routers` 包导入通过
- 当前 runtime 测试共 24 项，全部通过

## 结果

Phase 15 后，server 侧已经不只是“能运行”，而是开始具备真正的 package 复用能力。对后续抽出 `agent-server` 这一层，这是一个关键分水岭。
