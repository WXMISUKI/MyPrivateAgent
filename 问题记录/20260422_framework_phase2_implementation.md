# MyPrivateAgent 框架抽离 Phase 2 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：让应用层开始依赖抽象接口，而不是直接绑定 `ModelRouter`、`ContextManager`、`MemoryManager`

---

## 本次实施范围

本轮在 `backend/agent_framework/` 中继续补齐了第二层抽象，重点是：

1. `provider` 接口
2. `context` 接口
3. `memory` 接口
4. `artifact` 接口
5. 旧实现到新接口的适配器

本轮不是替换旧实现，而是先建立一层桥接层，确保当前应用还能稳定运行。

---

## 新增内容

### 1. Context 抽象

新增：

- `backend/agent_framework/context.py`

定义了：

- `ContextMessage`
- `ConversationContext`
- `ContextStore`

这样后续不同垂域 Agent 可以替换上下文实现，而不是被当前 `ContextWindow` 绑死。

### 2. Session Memory 抽象

新增：

- `backend/agent_framework/memory.py`

定义了：

- `SessionRecord`
- `SessionStore`

这样会话状态、活跃时间、消息计数、token 统计可以统一通过接口访问。

### 3. Artifact 抽象

新增：

- `backend/agent_framework/artifacts.py`

定义了：

- `Artifact`
- `ArtifactStore`

当前先提供内存版 artifact store，后续可以平滑切换到数据库或对象存储。

### 4. Adapter 桥接层

新增：

- `backend/agent_framework/adapters.py`

提供：

- `ModelRouterProviderAdapter`
- `ContextManagerAdapter`
- `ContextWindowAdapter`
- `MemoryManagerAdapter`
- `InMemoryArtifactStore`

以及统一入口：

- `get_model_provider()`
- `get_context_store()`
- `get_memory_store()`
- `get_artifact_store()`

---

## 业务层接入变化

`backend/orchestrator.py` 已从直接依赖：

- `get_model_router`
- `get_context_manager`
- `get_memory_manager`

切换为优先依赖：

- `get_model_provider`
- `get_context_store`
- `get_memory_store`
- `get_artifact_store`

这意味着 `Orchestrator` 已开始变成“面向接口编程”。

---

## 本轮收益

1. 当前业务层与底层实现之间多了一层明确隔离
2. 后续可以单独替换模型提供者，而不需要改 Orchestrator
3. 后续可以把 context/memory/artifact 独立成可安装 runtime 包
4. 不同垂域 Agent 可以共享统一接口，只替换适配器实现

---

## 当前限制

本轮仍属于“桥接式抽离”，还没有完全做到独立框架：

1. adapter 仍然桥接到现有 `backend/` 里的旧实现
2. artifact store 目前是内存版，尚未持久化
3. Context 压缩策略仍是当前项目自带实现，没有完全模块化
4. `ModelRouter` 还没有拆成多 provider 插件目录

---

## 下一阶段建议

建议第三步优先做：

1. 将 `ModelRouter` 拆为 provider registry
2. 将 context 压缩、artifact 管理、长期记忆彻底分层
3. 增加 `tests/agent_framework/`，覆盖 adapter 层和接口契约
4. 开始设计真正的包结构：`agent-core / agent-server / apps/*`
