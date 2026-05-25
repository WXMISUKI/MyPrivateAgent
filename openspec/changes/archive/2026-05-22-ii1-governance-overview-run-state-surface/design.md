## Context

我们已经有：

- stable child intent taxonomy
- sectioned merged semantics read model
- dedicated parent merge state surface
- runtime surface 对 child merged semantics 的只读展示

但 parent overview 还没有真正收口到后端 `governance_overview.run`。现在最合适的切口不是再拆新的 child summary，而是把稳定的 run scope 和 parent-facing merge 概览合并成后端真源。

## Goals / Non-Goals

**Goals**

- 允许 runtime profile 接收显式 run scope
- 在 `governance_overview.run` 里稳定暴露当前 run identity
- 让 `governance_overview.run` 直接承载 child merge state surface
- 保持 child merged semantics 专题 read model 可单独消费

**Non-Goals**

- 不改 child executor replay / summary endpoint 语义
- 不新增 child intent 类型
- 不改 Governance Timeline 的结构
- 不把 parent overview 再拆成多层前端推导链

## Decisions

### 1. 显式 run scope 优先，调度态兜底

Reasoning:

- 如果上游已经知道当前 `run_id / parent_run_id / child_run_id / scheduler_run_id`，后端应直接采信
- 如果没有显式输入，则从当前 item 的 scheduler runtime state 兜底，保证 profile 在现有页面里仍然可用

### 2. `governance_overview.run` 成为 parent overview 真源

Reasoning:

- parent overview 应由后端 contract 直接提供
- 前端只做展示映射，不再把专题 child merge read model 反向拼到 run overview

### 3. 只下沉稳定字段

Reasoning:

- 这一步不追求把 child merged semantics 复制一份
- 只下沉最稳定的 parent-facing 字段：
  - run identity
  - latest trace summary
  - child merge intent
  - child merge primary entities
  - child merge conclusion

## Run State Surface Shape

`governance_overview.run` 新增：

- `run_id`
- `parent_run_id`
- `child_run_id`
- `scheduler_run_id`
- `run_kind`
- `status`
- `trace_count`
- `latest_trace_event`
- `child_merge_intent`
- `child_merge_entities`
- `child_merge_conclusion`

## Data Flow

1. API 接收可选 run scope 参数
2. `RuntimeSurfaceService` 先解析显式 scope
3. 若显式 scope 缺失，则由当前计划项的 scheduler runtime state 兜底
4. 后端读取 child merged semantics read model
5. 组合出 `governance_overview.run`
6. 前端只消费该 contract

