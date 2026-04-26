# Framework Phase 16 实施记录

## 目标

继续推进 `agent-server` 层抽象，先把路由层最常见的 HTTP/SSE 辅助模式收口到统一 helper，减少每个 router 自己拼接响应、自己处理 404、自己序列化对象。

## 本次改动

### 1. 新增 Server Service

新增 `backend/services/server_service.py`，提供可复用的 server adapter 辅助函数：

- `build_sse_event()`
- `build_error_event()`
- `ensure_exists()`
- `success_response()`
- `permission_request_to_dict()`

这些函数不绑定具体业务域，可以在未来抽成 `agent-server` 包的基础工具。

### 2. Chat SSE 响应收口

`backend/routers/chat.py` 不再手写：

```python
f"data: {json.dumps(...)}\n\n"
```

而是改用：

- `build_sse_event()`
- `build_error_event()`

这能避免 SSE 格式在不同路由或后续功能中漂移。

### 3. Conversations 路由收口

`backend/routers/conversations.py` 改用：

- `ensure_exists()`
- `success_response()`

删除、查询、更新的 404 和成功响应语义开始统一。

### 4. Permissions 路由收口

`backend/routers/permissions.py` 改用：

- `permission_request_to_dict()`
- `ensure_exists()`
- `success_response()`

权限请求的 API 输出结构不再散落在多个接口里手写。

### 5. 增加回归测试

新增 `tests/agent_framework/test_server_service.py`，覆盖：

- SSE 格式
- 错误事件格式
- 404 helper
- 成功响应
- 权限请求序列化

并纳入 CI。

## 验证

- `py_compile` 通过
- 当前 runtime/server 测试共 29 项，全部通过

## 结果

Phase 16 后，项目具备了更清晰的 server adapter 辅助层。它还不是独立 package，但已经把可复用的 HTTP/SSE 模式从具体业务路由中抽出来了。
