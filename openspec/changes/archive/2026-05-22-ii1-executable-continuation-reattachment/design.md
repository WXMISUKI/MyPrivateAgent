## Context

II-1.3 把恢复协议从隐式行为推进成了正式 contract，但当前 recoverable 的前提仍然是：executable continuation 还留在当前进程内存里。

为了继续推进 II-1，下一步不该直接做“任意 callable 跨进程恢复”。更稳的切法是：

1. continuation descriptor 持久化稳定的 binding identity
2. 新进程通过 registry / resolver 解析这些 binding
3. 只有解析成功时，才把 persisted descriptor 重新提升成 executable continuation

这一步仍然保持 fail-closed 默认值，不假装通用跨进程恢复已经完成。

## Goals / Non-Goals

**Goals:**

- 新增一个窄的 continuation registry seam
- 允许 `tool_executor / reflector / reviewer / fallback_handler` 通过稳定 binding id 重挂
- 让 recovery probe 能区分：
  - `ready_in_process`
  - `ready_via_registry`
  - `missing_registered_binding`
  - `missing_executable_continuation`
- 保持未注册 callable 的当前行为不变

**Non-Goals:**

- 不实现任意 Python callable 的自动序列化/反序列化
- 不实现进程外代码装载器
- 不把 `delegate_run()` 升级为真实 child executor
- 不引入新的数据库 schema 或 durable backend 强依赖

## Decisions

### 1. 用 registry seam，而不是“序列化 callable”

Reasoning:

- 企业项目里不能把任意 callable 当成可持久化对象处理。
- registry seam 更明确，也更便于后续受控接入 child executor、tool runtime 或 worker process。

### 2. binding identity 进入 descriptor，但 descriptor 仍不是 executable continuation

Reasoning:

- descriptor 负责表达“恢复所需标识”。
- executable continuation 只在 registry 成功解析后才重新构建。

### 3. registry 解析应服务于 probe 和 actual recovery，两者共享同一逻辑

Reasoning:

- 否则 probe 说“可恢复”，真正恢复又走另一套代码，很容易漂移。

## Risks / Trade-offs

- [Risk] 需要调用方显式注册 binding。  
  Mitigation：未注册时保持旧行为，不破坏现有测试和轻量接入。

- [Risk] descriptor 中新增 binding 字段会增加结构复杂度。  
  Mitigation：只持久化稳定 id，不持久化实现细节。

- [Risk] 部分历史 descriptor 不带 binding id，仍然不可恢复。  
  Mitigation：保留 `missing_executable_continuation`，不伪装成兼容恢复。

## Migration Plan

1. 定义 continuation registry seam 与 binding-aware descriptor helper
2. 让 SDK 在登记 continuation 时写入 binding id
3. 让 recovery probe 与 recovery attempt 共用 registry resolver
4. 补 focused tests，覆盖 registered / missing binding / legacy descriptor 三类场景
5. 更新 architecture / roadmap 文档

## Open Questions

- 后续是否需要把 registry seam 暴露给 `AgentHarnessFacade` 作为默认接入模式？
- 后续 child executor 是否应该复用同一套 binding identity，而不是另起一套 protocol？

