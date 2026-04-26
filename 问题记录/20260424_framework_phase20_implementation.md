# Framework Phase 20 实施记录

## 主题
`agent_server` 增加 preset 装配层

## 背景
Phase 19 之后，`create_app(config)` 已经支持按配置裁剪路由和替换依赖，但每个接入方仍然要手动拼装 `AgentServerConfig`。这对于“通用 server 包”还不够友好。

需要一个更直接的入口，让常见场景可以直接按 preset 装配：

- `full_stack`
- `api_only`
- `embedded`

## 本次改动

### 1. 新增 preset 常量和配置工厂
更新 `backend/agent_server/config.py`：

- `AgentServerPreset`
- `PRESET_FULL_STACK`
- `PRESET_API_ONLY`
- `PRESET_EMBEDDED`
- `DEFAULT_SERVER_PRESET`
- `API_ONLY_ROUTE_GROUPS`
- `EMBEDDED_ROUTE_GROUPS`
- `get_server_config_for_preset()`
- `get_available_server_presets()`

### 2. App Factory 支持 preset
更新 `backend/agent_server/app.py`：

```python
create_app(config: AgentServerConfig | None = None, *, preset: AgentServerPreset = DEFAULT_SERVER_PRESET)
```

行为规则：

- 传入 `config` 时优先使用 `config`
- 未传入 `config` 时按 `preset` 生成标准装配配置

### 3. 新增的 preset 语义

#### `full_stack`
- 默认模式
- 全量路由
- 启用 legacy UI
- 加载环境变量
- 初始化数据库

#### `api_only`
- 关闭 legacy UI
- 保留 `auth/core/skills/learning/permissions`
- 不包含 `admin`

#### `embedded`
- 关闭 legacy UI
- 仅保留 `core/skills`
- 默认不加载 `.env`
- 默认不初始化数据库
- 适合嵌入到已有宿主应用

### 4. 对外导出补齐
更新 `backend/agent_server/__init__.py`，统一导出 preset 常量和工厂函数。

## 示例

### 默认全量服务
```python
from backend.agent_server import create_app

app = create_app()
```

### API Only
```python
from backend.agent_server import PRESET_API_ONLY, create_app

app = create_app(preset=PRESET_API_ONLY)
```

### Embedded
```python
from backend.agent_server import PRESET_EMBEDDED, create_app

app = create_app(preset=PRESET_EMBEDDED)
```

## 验证

- `py_compile` 通过
- `tests.agent_framework.test_agent_server_app` 通过
- `tests.agent_framework.test_agent_server_dependencies` 通过
- 完整后端测试集共 `43` 项，通过

## 收益

- 复用方不需要自己手拼基础配置
- 常见部署模式有统一命名和默认行为
- `agent-server` 更接近真实可安装包，而不是项目内 helper

## 下一步建议

1. 继续把鉴权从 dependency override 升级为 `auth provider`
2. 给 `preset` 增加文档页或 starter 示例
3. 把 `admin` 再拆成更细粒度 group，例如 `ops`、`memory_admin`
