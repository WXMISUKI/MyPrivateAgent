# MyPrivateAgent 框架抽离 Phase 3 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：把模型层从单体 `ModelRouter` 进一步拆成 provider registry，并补齐最小自动化测试

---

## 本次实施范围

本轮聚焦两件事：

1. 将模型路由能力升级为 provider registry
2. 给 `agent_framework` 增加最小测试，确保后续持续重构时有回归保护

---

## 新增内容

### 1. Provider Registry

`backend/agent_framework/providers.py`

新增：

- `ProviderBackend`
- `ProviderSelection`
- `ModelProviderRegistry`

这意味着模型选择不再依赖一个写死分支的 `ModelRouter`，而是通过 registry 去解析具体 provider。

### 2. Concrete Provider Backends

`backend/agent_framework/provider_backends.py`

新增：

- `DoubaoProviderBackend`
- `OllamaProviderBackend`
- `create_default_provider_registry()`

当前支持的 provider 已开始具备明确边界：

- 豆包 provider
- 本地 Ollama provider

后续再接 OpenAI、Anthropic、Azure、其他私有模型时，可以直接新增 backend，不需要继续改主路由逻辑。

---

## 现有代码接入方式

### 1. ModelRouter 保留外观，内部改为委托 registry

`backend/model_router.py`

当前仍然保留 `ModelRouter` 这个外观类，以保证现有业务代码兼容，但内部已经改为委托：

- `registry.get_model(...)`
- `registry.get_model_config(...)`
- `registry.is_model_available(...)`
- `registry.list_available_models(...)`

这样做的好处是：

1. 不打断现有调用方
2. 新旧架构可平滑过渡
3. 后续可以逐步让更多代码直接依赖 provider registry

### 2. Orchestrator 兼容旧属性名

`backend/orchestrator.py`

为避免旧逻辑里某些 fallback 分支仍使用 `self.model_router`，当前保留：

- `self.model_provider`
- `self.model_router`

两者暂时指向同一层 provider 接口。

---

## 测试补充

本轮新增：

- `tests/agent_framework/test_provider_registry.py`
- `tests/agent_framework/test_adapters.py`

使用 `unittest`，避免额外引入 pytest 依赖。

当前覆盖内容：

1. provider registry 可正确解析匹配 provider
2. provider registry 可合并 provider 模型列表
3. 未知模型会抛出错误
4. artifact store 可按会话和类型过滤

---

## 本轮收益

1. 模型层真正开始从“写死 if/else”转向“可扩展 provider backend”
2. 后续增加模型供应商时，不需要继续污染主路由逻辑
3. `agent_framework` 已经有了最小自动化回归基线
4. 框架抽离开始从“结构设计”进入“可持续迭代”阶段

---

## 当前限制

1. `ModelRouter` 仍然存在，尚未完全退场
2. provider registry 目前只有两个 backend
3. 还没有 provider 级别的超时、熔断、健康检查
4. 测试数量仍然偏少，只覆盖了最小核心链路

---

## 下一阶段建议

建议第四步优先做：

1. 将 `tests/agent_framework/` 扩展到事件协议、状态机和 tool metadata
2. 让前后端 SSE 更彻底依赖统一 `AgentEvent`
3. 将 context 压缩和 artifact 持久化继续拆分
4. 开始准备 monorepo/package 化目录迁移
