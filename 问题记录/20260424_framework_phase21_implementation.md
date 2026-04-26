# Framework Phase 21 实施记录

## 主题
`agent_server` 引入 `auth provider` 抽象

## 背景
Phase 20 之后，`agent_server` 已支持 preset 和配置化装配，但认证策略仍然主要依赖：

- `AgentServerAuthConfig.current_user_dependency`
- `AgentServerAuthConfig.optional_user_dependency`
- `AgentServerAuthConfig.database_dependency`

这能工作，但还不是一个清晰的“认证提供者”模型。对于后续的匿名嵌入、宿主系统透传用户、企业 SSO 适配，这种形式不够稳定。

## 本次改动

### 1. 新增 `auth_provider` 模块
新增 `backend/agent_server/auth_provider.py`，定义：

- `AgentServerAuthProvider`
- `get_default_auth_provider()`
- `create_auth_provider()`
- `create_anonymous_auth_provider()`

### 2. `AgentServerAuthConfig` 支持 provider
更新 `backend/agent_server/config.py`：

- `AgentServerAuthConfig.provider`
- 默认 provider 为 `get_default_auth_provider()`

这意味着不传任何配置时，仍然保持当前 JWT/Bearer 鉴权行为不变。

### 3. App Factory 使用 provider
更新 `backend/agent_server/app.py`：

- `create_app()` 在构建 `dependency_overrides` 时，先应用 `auth.provider`
- 如果同时配置了 `current_user_dependency` 等显式覆盖项，则显式覆盖优先

优先级：

1. `auth.provider`
2. `auth.current_user_dependency / optional_user_dependency / database_dependency`
3. 默认 JWT provider

### 4. 对外导出
更新 `backend/agent_server/__init__.py`，统一导出：

- `AgentServerAuthProvider`
- `create_auth_provider()`
- `create_anonymous_auth_provider()`
- `get_default_auth_provider()`

## 使用示例

### 使用默认 JWT provider
```python
from backend.agent_server import create_app

app = create_app()
```

### 使用匿名 provider
```python
from backend.agent_server import (
    AgentServerAuthConfig,
    AgentServerConfig,
    create_anonymous_auth_provider,
    create_app,
)

app = create_app(
    AgentServerConfig(
        auth=AgentServerAuthConfig(
            provider=create_anonymous_auth_provider(
                user={"id": "embedded-user", "username": "embedded-user"}
            )
        )
    )
)
```

### 使用宿主系统自定义 provider
```python
from backend.agent_server import (
    AgentServerAuthConfig,
    AgentServerConfig,
    create_auth_provider,
    create_app,
)

def get_host_user():
    return {"id": "host-user"}

app = create_app(
    AgentServerConfig(
        auth=AgentServerAuthConfig(
            provider=create_auth_provider(
                name="host_auth",
                current_user_dependency=get_host_user,
            )
        )
    )
)
```

## 验证

- `py_compile` 通过
- `tests.agent_framework.test_agent_server_app` 通过
- `tests.agent_framework.test_agent_server_dependencies` 通过
- 完整后端测试集共 `46` 项，通过

## 收益

- 认证不再只是“散落的 dependency override”
- 可以用一个 provider 对象表达整套认证策略
- 后续接 SSO、匿名嵌入、宿主透传用户时更稳定

## 下一步建议

1. 把 `auth provider` 再分成更明确的模式，例如 `bearer`、`anonymous`、`host_passthrough`
2. 为 `auth provider` 增加文档和 starter 示例
3. 如果后续要做真正的插件化 server 包，可以让 route preset 和 auth provider 组成标准发行配置
