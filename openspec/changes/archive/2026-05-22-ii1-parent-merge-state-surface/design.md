## Context

我们已经完成了：

- stable child intent taxonomy
- sectioned merged semantics read model
- Runtime Surface 对 merged semantics 的只读专题消费

但 parent merge 结果还没有真正进入 parent overview。现在最合适的切口是先做最小 state surface，而不是继续扩 section 种类。

## Goals / Non-Goals

**Goals**

- 给 merged semantics read model 增加最小 parent overview surface
- 在 Runtime Surface 的 `Governance Overview -> Run Overview` 中展示 parent merge 状态

**Non-Goals**

- 不改 runtime profile 后端主 contract
- 不新增新的 child executor intent
- 不在这一步改 Governance Timeline

## Decisions

### 1. 先在 dedicated merged semantics contract 里表达 `parent_state_surface`

Reasoning:

- 不需要反向侵入 runtime profile 主 contract
- 先从现有独立 read model 聚合一层 parent overview，更符合当前分层

### 2. Runtime Surface 用 composition 方式把它挂到 parent overview

Reasoning:

- 现有 `RuntimeSurfacePanel` 已经单独加载 merged semantics
- 直接在前端 overview 中组合能最小改动落地

## Parent State Surface Shape

新增：

- `parent_state_surface.intent_label`
- `parent_state_surface.entity_count`
- `parent_state_surface.focus_count`
- `parent_state_surface.action_count`
- `parent_state_surface.latest_conclusion`
- `parent_state_surface.primary_entities`

