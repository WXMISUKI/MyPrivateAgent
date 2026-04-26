# Framework Phase 11 实施记录

## 目标

继续推进 `P0` 稳定性收口，优先解决两类“重启即丢”的运行时状态：

1. 工具权限请求
2. 结构化 artifact

同时补一条最小 CI，把已经存在的运行时回归测试和前端构建固化下来。

## 本次改动

### 1. 新增数据库表

在 `backend/models.py` 新增：

- `PermissionRequestRecord`
- `ArtifactRecord`

用途：

- 权限请求支持落库、查询、批准、拒绝、超时后恢复
- artifact 支持运行时审计、调试复盘、后续 UI 面板扩展

### 2. ArtifactStore 改为数据库优先

在 `backend/agent_framework/adapters.py` 中新增 `SQLAlchemyArtifactStore`。

行为：

- 默认优先使用数据库存储 artifact
- 如果数据库不可用，仍回退到 `InMemoryArtifactStore`

这保证了：

- 正常部署环境具备持久化
- 测试和无数据库环境仍能运行

### 3. PermissionService 改为数据库优先

在 `backend/harness/permission_service.py` 中新增：

- `_save_request()`
- `_load_record()`
- `_to_request()`

现在权限请求在以下动作都会同步落库：

- 创建
- 批准
- 拒绝
- 超时清理

并且 `get_request()`、`get_result()`、`list_pending_requests()` 会优先读取数据库，内存态只作为运行期缓存。

### 4. 新增最小 CI

新增 `.github/workflows/ci.yml`

包含两项检查：

- Python runtime 单元测试
- Vue 前端生产构建

## 结果

Phase 11 后，框架最核心的两类运行时状态不再完全依赖进程内内存，这使它更接近成熟 agent runtime 对“可恢复、可审计、可复盘”的要求。

## 尚未收口

这一步还没有彻底移除 `backend/routers/chat.py` 中的旧 LangGraph 执行残留。下一阶段应继续统一执行入口，让 `AgentHarness + Orchestrator` 成为唯一主链路。
