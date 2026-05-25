## Context

当前 registry 已经能做两件事：

1. `identify(handler)`：把当前内存里的 callable 反查成 binding id
2. `resolve(binding_id)`：把 persisted descriptor 里的 binding id 重新解析回 callable

这已经足够支撑受控恢复，但还不够支撑“可运营、可观测、可协作”的 continuation binding 面。我们还需要一层稳定 catalog，让 SDK、治理面和后续执行器都能围绕同一份 binding 目录工作。

## Goals / Non-Goals

**Goals:**

- 给 binding 增加标准元数据：`binding_kind / handler_name / metadata`
- 给 registry 增加 catalog 输出
- 给 SDK 增加窄的 catalog 查询接口
- 保持现有 reattach 语义兼容

**Non-Goals:**

- 不做新的 durable schema
- 不把 registry 变成执行器
- 不改现有 approval / loop 恢复路径

## Decisions

### 1. catalog 只暴露描述信息，不暴露 handler 本身

Reasoning:

- catalog 是治理和排障面，不应该暴露可执行对象。
- 这样也方便未来把它同步到 worker/child executor 前置校验。

### 2. SDK 提供只读 catalog 接口，而不是把 registry 直接泄漏给上层

Reasoning:

- 维持 SDK 作为稳定 runtime seam。
- 避免调用方直接依赖 registry 内部结构。

## Risks / Trade-offs

- [Risk] registry 接口变宽。  
  Mitigation：只增加只读描述能力，不增加复杂生命周期。

- [Risk] catalog 元数据被调用方误当成执行保证。  
  Mitigation：文档里明确它只表示“已注册 binding 目录”，不是执行成功承诺。

## Migration Plan

1. 为 registry 增加 binding metadata 和 catalog 输出
2. 为 SDK 增加 catalog 查询方法
3. 补 focused tests 和文档

