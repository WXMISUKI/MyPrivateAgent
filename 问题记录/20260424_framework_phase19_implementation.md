# Framework Phase 19 实施记录

## 主题
`agent_server.create_app()` 改造成可配置装配器

## 背景
Phase 18 之后，`agent_server` 已经有了独立入口、依赖导出和 HTTP helper，但 `create_app()` 仍然是硬编码装配：

- 固定加载全部路由
- 固定挂载 legacy UI
- 固定使用当前鉴权依赖
- 无法按场景裁剪 admin 路由

这会限制后续把它做成真正可复用的 server package。

## 本次改动

### 1. 新增配置对象
新增 `backend/agent_server/config.py`：

- `AgentServerConfig`
- `AgentServerBootstrapConfig`
- `AgentServerUIConfig`
- `AgentServerAuthConfig`
- `DEFAULT_ROUTE_GROUPS`

支持配置：

- `route_groups`
- `route_names`
- `load_environment`
- `init_database`
- `legacy UI` 是否启用
- CORS 参数
- 通用 `dependency_overrides`
- 鉴权依赖覆盖

### 2. 路由注册表升级
更新 `backend/agent_server/router_registry.py`：

- 增加 `RouterRegistration`
- 路由与 group 显式绑定
- 新增 `get_api_router_registrations()`
- 新增 `get_route_group_names()`
- `get_api_routers()` 支持按 `route_groups/route_names` 过滤

当前分组：

- `auth`
- `core`
- `skills`
- `learning`
- `permissions`
- `admin`

### 3. App Factory 可配置化
更新 `backend/agent_server/app.py`：

- `create_app(config: AgentServerConfig | None = None)`
- 启动逻辑按 `bootstrap` 配置执行
- 路由按 registry 和配置动态装配
- `legacy UI` 按配置决定是否挂载
- `get_current_user/get_current_user_optional/get_db` 支持通过 `auth` 配置覆盖

### 4. 对外导出补齐
更新 `backend/agent_server/__init__.py`，统一导出：

- 配置对象
- 路由分组常量
- 路由注册查询接口

## 使用示例

### API Only
```python
from backend.agent_server import (
    AgentServerBootstrapConfig,
    AgentServerConfig,
    AgentServerUIConfig,
    create_app,
)

app = create_app(
    AgentServerConfig(
        route_groups=("core", "skills"),
        bootstrap=AgentServerBootstrapConfig(
            load_environment=False,
            init_database=False,
        ),
        ui=AgentServerUIConfig(enabled=False),
    )
)
```

### 替换鉴权依赖
```python
from backend.agent_server import AgentServerAuthConfig, AgentServerConfig, create_app

def fake_current_user():
    return {"id": "demo-user"}

app = create_app(
    AgentServerConfig(
        auth=AgentServerAuthConfig(current_user_dependency=fake_current_user)
    )
)
```

## 验证

- `py_compile` 通过
- `tests.agent_framework.test_agent_server_app` 通过
- `tests.agent_framework.test_agent_server_dependencies` 通过
- 完整后端测试集共 `40` 项，通过

## 收益

- `agent_server` 不再是“固定写死的项目入口”
- 可以按场景构建 API-only、无 admin、无 legacy UI 的变体
- 替换鉴权方式时不需要改业务路由文件
- 更接近后续拆成独立 `agent-server` 安装包的目标

## 下一步建议

1. 给 `create_app()` 增加 router preset，例如 `api_only`、`full_stack`、`embedded`
2. 把 admin 路由进一步拆组，而不是只有一个 `memory`
3. 把鉴权方案抽成真正的 strategy/provider 接口，而不仅是 dependency override
