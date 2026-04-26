# Framework Phase 18 实施记录

## 背景
Phase 17 已经把 `agent-server` 做成了独立的 app factory，但路由层仍然直接依赖 `backend.auth`、`backend.database` 和 `services.server_service`。这会导致：

- `agent_server` 只是应用入口，不是完整的 server 边界
- 路由复用时仍需知道旧模块布局
- 后续拆包成独立 server package 时，迁移成本仍然偏高

## 本次改动

### 1. 新增 server 依赖入口
- 新增 `backend/agent_server/dependencies.py`
- 统一暴露：
  - `get_db`
  - `get_current_user`
  - `get_current_user_optional`
  - `oauth2_scheme`

### 2. 新增 server HTTP 入口
- 新增 `backend/agent_server/http.py`
- 统一暴露：
  - `build_sse_event`
  - `build_error_event`
  - `ensure_exists`
  - `success_response`
  - `permission_request_to_dict`

### 3. 更新 agent_server 公共导出
- `backend/agent_server/__init__.py` 现在直接导出 dependencies/http 能力
- 使 `agent_server` 更接近真正可复用的 server package 外观

### 4. 路由层切换到 server 边界
以下路由已优先改为从 `agent_server` 取依赖或 HTTP helper：

- `backend/routers/auth.py`
- `backend/routers/chat.py`
- `backend/routers/conversations.py`
- `backend/routers/permissions.py`
- `backend/routers/skills.py`
- `backend/routers/learnings.py`

其中 `chat.py` 顺手收口了 SSE 输出，统一通过 `build_sse_event()` 编码事件。

## 验证
- 新增 `tests/agent_framework/test_agent_server_dependencies.py`
- 验证 `backend.agent_server` 的公共导出与 `dependencies/http` 子模块一致
- 配合既有 `test_agent_server_app.py`、`test_router_imports.py`，确保导入链未回退

## 当前收益
- 路由层对 `backend.auth/database/services.server_service` 的直接耦合进一步下降
- `agent_server` 从“app factory 包”向“真正的 server adapter 包”更进一步
- 为后续把鉴权、依赖注入、admin router 注册做成可配置插件打下基础

## 下一步建议
- 继续把 admin 路由和鉴权策略做成可配置注册项
- 为 `agent_server.create_app()` 增加可选配置对象，支持按场景裁剪路由集
- 把 `backend/routers` 中剩余通用模式继续迁移到 `agent_server` 命名空间
