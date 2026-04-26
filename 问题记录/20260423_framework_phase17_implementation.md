# Framework Phase 17 实施记录

## 目标

把前面已经逐步抽出的 server-side helper 真正提升成一个明确的 `agent-server` 包入口，而不是继续让 `main.py` 承担应用装配职责。

## 本次改动

### 1. 新增 `backend/agent_server/` 包

新增：

- `backend/agent_server/__init__.py`
- `backend/agent_server/bootstrap.py`
- `backend/agent_server/router_registry.py`
- `backend/agent_server/app.py`

职责划分：

- `bootstrap.py`
  - 环境变量加载
  - 数据库初始化
- `router_registry.py`
  - 集中注册 API routers
- `app.py`
  - FastAPI app factory
  - 静态资源、模板、CORS、路由装配

### 2. `main.py` 降级为薄启动入口

`backend/main.py` 现在不再自己装配 FastAPI 应用，而是只做：

- 配置 logging
- 调用 `create_app()`
- 启动 uvicorn

这让应用入口和 server 包入口分离，更接近真正可复用的 server package 结构。

### 3. app 生命周期升级为 lifespan

`backend/agent_server/app.py` 使用 FastAPI 的 `lifespan`，替代旧的 `@app.on_event("startup")`。

这让新的 server 包不会建立在已弃用的启动 API 上。

### 4. 增加 app factory 测试

新增 `tests/agent_framework/test_agent_server_app.py`，覆盖：

- `router_registry` 返回的 router 数量
- `create_app()` 是否注册了核心路由

并纳入 CI。

## 验证

- `backend.agent_server` 包导入通过
- `create_app()` 测试通过
- 当前 runtime/server 测试共 31 项，全部通过

## 结果

Phase 17 后，项目已经具备一个清晰的 server package 入口。虽然它还没有单独发布为 pip 包，但从架构边界上看，`agent-server` 这一层已经真正开始成型了。
