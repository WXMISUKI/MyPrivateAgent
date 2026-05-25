## Context

II-1 第二刀已经把 `EmbeddedRunWorkspaceStore` seam、descriptor persistence、hydration 和 fail-closed 基线立住了。当前系统能明确区分：

- executable continuation 仍只在进程内
- persisted continuation descriptor 只代表“恢复信息存在”

但缺少正式 recovery protocol，导致调用方只能依赖异常和内部实现来判断恢复状态。这会让后续 durable backend、child executor 和多进程恢复都缺统一语义基础。

## Goals / Non-Goals

**Goals:**

- 为 `tool_approval_continuation` 与 `loop_continuation` 增加正式 recovery status / reason contract
- 为 `resume_run(..., continue_loop=True)` 增加标准 recovery gate，先 probe 再恢复
- 让 recovery 失败进入 machine-readable、event-visible 的 fail-closed 路径
- 保持当前 store seam、SQLAlchemy fallback 和 in-process continuation 行为兼容

**Non-Goals:**

- 不实现跨进程可执行 continuation 装载器
- 不实现真正 child executor 或多实例 orchestrator
- 不引入新的 durable backend 依赖或数据库迁移
- 不改 Query/Run Read Model 或前端治理视图布局

## Decisions

### 1. 先定义 recovery protocol，再定义 executable continuation loader

Reasoning:

- 现在真正缺的是恢复语义，而不是存储载体。
- 没有 protocol，就算默认改成 durable backend，也只是把“不知道能不能恢复”搬进数据库。

Alternatives considered:

- 先做默认 SQLAlchemy durable backend：能提升持久化，但不能回答恢复语义。
- 直接做 child executor：依赖更强恢复协议，顺序不对。

### 2. recovery probe 与 recovery attempt 分离

Reasoning:

- 调用方需要先知道“能不能恢复”，而不是只能靠尝试失败。
- probe 结果也应成为治理与排障信息的一部分。

Alternatives considered:

- 只有 `resume_run()` 一个入口：简单，但把诊断与执行耦合在一起。

### 3. fail-closed 结果必须结构化

Reasoning:

- persisted descriptor 但缺 executable continuation 是预期状态，不应只表现为字符串异常。
- 结构化结果便于 harness、治理台和后续恢复协调器复用。

Alternatives considered:

- 继续只抛异常：短期快，但无法形成稳定 contract。

### 4. descriptor 只记录恢复事实，不伪装成 executable continuation

Reasoning:

- 这能保持当前“descriptor != executable continuation”边界不被冲掉。
- 也避免让调用方误读成已经完成跨进程恢复。

## Risks / Trade-offs

- [Risk] protocol 先行会让接口数量增加。 → Mitigation：保持 API 很窄，只引入 probe/result/reason。
- [Risk] 结果结构与未来真实 loader 不完全一致。 → Mitigation：先固定最小字段，预留扩展位，不引入实现细节。
- [Risk] 现有调用方仍依赖异常路径。 → Mitigation：保留 fail-closed 异常，但同时补结构化 metadata 与事件。

## Migration Plan

1. 定义 recovery result / reason helper。
2. 在 SDK 内新增 probe seam，并让 `resume_run(..., continue_loop=True)` 走统一 gate。
3. 为 `tool_approval_continuation` 和 `loop_continuation` 写入 recovery status / reason。
4. 补 focused tests。
5. 更新 architecture / roadmap 文档，把 II-1 从“仅有 persistence seam”推进到“有正式 recovery protocol”。

Rollback strategy:

- 如果新 recovery contract 引起调用方耦合问题，可回退 probe 入口，但保留 descriptor/status 结构化字段。
- 不回退当前 fail-closed 边界。

## Open Questions

- 后续真实 executable continuation loader 应该挂在 SDK 层还是独立 recovery coordinator？
- recovery reason 是否需要进一步分层成 stable code + debug detail 两套字段？
