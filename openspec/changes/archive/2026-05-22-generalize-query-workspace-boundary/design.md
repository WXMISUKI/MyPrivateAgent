# Design: 通用 Query Workspace / Query History 边界

## Overview

本次设计不是做新功能，而是把当前 `main_chat` 已经跑通的 query 能力上升成更清晰的边界模型。

建议把能力拆成四层：

1. `recent summary`
2. `query detail`
3. `query history`
4. `query workspace`

## Four-Layer Model

### 1. recent summary

职责：

- 展示最近几次 query 的轻摘要
- 适合 overview / top card / quick jump

当前对应：

- `main_chat_trace_overview.recent_queries`

通用性判断：

- **可推广**
- 任何具备稳定 `query_id` 的 channel，理论上都能有这一层

### 2. query detail

职责：

- 展示单个 query 的阶段链、最近事件、告警、快照等

当前对应：

- `main_chat_query_detail`

通用性判断：

- **可推广**
- 但前提是该 channel 已经具备稳定 query lifecycle 和 dedicated detail contract

### 3. query history

职责：

- 展示超出 recent summary 的长历史摘要
- 支持分页/游标扩展

当前对应：

- `main_chat_query_history`

通用性判断：

- **部分可推广**
- query history 的 contract 模式可以推广
- 但当前 history 的字段和 UX 仍带有明显 `main_chat` 语义，因此不能直接复制到所有 channel

### 4. query workspace

职责：

- 把 history、detail、focus、search、page restore、view snapshot 放在同一治理工作区

当前对应：

- `Main Chat Query Workspace`

通用性判断：

- **暂不直接推广**
- 当前它仍然高度依赖 `main_chat` 的前端体验和使用频率
- 未来如要推广，应先推广 contract/read model，再推广 workspace 壳

## Current Channel Assessment

### main_chat

当前状态：

- 已具备 `recent summary`
- 已具备 `query detail`
- 已具备 `query history`
- 已具备 `query workspace` 雏形

判断：

- 当前是最完整的一条线
- 可作为通用 query 模式的候选基准

### subagent_lane

当前状态：

- 已进入 Query Control lifecycle 语言
- 已有 `subagent_spawned / collected / merged` 的治理事件
- 但当前更接近“治理事件带 query 语义”，而不是完整 query detail/history/workspace

判断：

- **可优先评估是否进入 `recent summary` 层**
- **可中期评估是否进入 `query detail` 层**
- 当前**不建议直接进入 `query history` 或 `query workspace`**

原因：

- 生命周期粒度、事件丰富度、前端使用频率都还不足以支撑完整 workspace 壳

#### subagent_lane readiness checklist

进入 `recent summary` 层前，至少满足：

1. `subagent_lane` 事件里已稳定携带可追踪 `query_id`
2. `spawned / collected / merged` 之外，已有足够稳定的 latest-stage 归纳语义
3. 可以为单个 subagent query 给出清晰 summary，而不是只暴露原始事件名
4. 前端不需要从原始 timeline 本地猜测 query 身份

进入 `query detail` 层前，至少再满足：

1. 已有 dedicated detail contract，而不是继续只靠 timeline 局部聚合
2. 已有稳定 stage chain 或等价 lifecycle 明细
3. 可以区分“单 query detail”与“子运行事件流”两个视角
4. 不会把 scheduler fan-out 内部实现细节直接暴露成 query detail 主体

当前结论：

- `subagent_lane` 已通过当前阶段的 `recent summary readiness` 评估
- 当前不进入 `query history / query workspace`

#### 评估依据

- 代码层已存在稳定 query lifecycle 映射：
  - `child_run_created -> input_received`
  - `subagent_spawned -> planning`
  - `subagent_collected -> observation`
  - `subagent_merged -> final_output`
- recorder 已稳定把 `run_id / child_run_id` 作为 query 识别主位之一写入 Query Control timeline
- `build_spawn_event / build_collect_event / build_merge_event` 已提供清晰 summary 文本与 excerpt
- 测试已覆盖 `subagent_lane` 的 stage mapping 与 fail-open recorder 行为

#### readiness 评估结果

`recent summary`：

- `query_id` 稳定性：通过
- latest-stage 归纳语义：通过
- summary 清晰度：通过
- 前端无需本地猜 query 身份：通过

`query detail`：

- dedicated detail contract：未通过
- 稳定 stage chain contract：未通过
- 单 query detail 与子运行事件流视角分离：未通过
- fan-out 内部细节隔离：部分通过，但未形成正式 detail 边界

因此当前判断：

- **允许把 `subagent_lane` 提升为 `recent summary` 候选模式**
- **不允许进入 `query detail / query history / query workspace`**

### external_adapter

当前状态：

- 已进入 Query Control lifecycle 语言
- 已有 external pilot 与 error/diagnostic 治理链路
- 但当前 query 语义仍高度依赖 pilot / diagnostic 上下文

判断：

- **可优先评估是否进入 `recent summary` 层**
- `query detail` 需要先确认 external adapter query 是否具备稳定 dedicated contract
- 当前**不建议直接进入 `query history` 或 `query workspace`**

原因：

- 目前更像“受控执行与治理诊断事件流”，还不是稳定的 query workspace 使用场景

#### external_adapter readiness checklist

进入 `recent summary` 层前，至少满足：

1. external adapter query 已具备稳定 `query_id`
2. pilot / error / output 语义可稳定压缩成 summary，而不是只剩诊断片段
3. 不同 adapter 框架不会导致 summary 字段语义漂移
4. 前端不需要额外拼接 framework-specific 解释逻辑

进入 `query detail` 层前，至少再满足：

1. 已有 dedicated detail contract
2. external query 的 stage chain 不再强依赖特定 pilot / diagnostic 模式
3. 错误、输出、推理、审计之间边界已稳定
4. 可以区分“单 query detail”与“某次 pilot 执行日志”两个视角

当前结论：

- `external_adapter` 已通过当前阶段的 `recent summary readiness` 评估
- 当前不进入 `query history / query workspace`

#### 评估依据

- external adapter 已进入 Query Control lifecycle 映射：
  - `framework_adapter_status -> model_stream`
  - `framework_adapter_reasoning -> planning`
  - `framework_adapter_output -> final_output`
  - `framework_adapter_external_error -> final_output`
- runtime service 在写入 Query Control timeline 时，已稳定用 `run_id` 作为当前 external query 的 `query_id`
- external pilot 现有事件已具备清晰 summary / detail 字段，而不是只保留原始诊断对象
- 当前前端对 external adapter 治理链路已有统一展示与错误分类，不需要额外拼装 framework-specific 解释才能读懂核心结果

#### readiness 评估结果

`recent summary`：

- `query_id` 稳定性：通过
- summary 清晰度：通过
- latest-stage 归纳语义：通过
- 前端无需额外拼 framework-specific 解释逻辑：通过

`query detail`：

- dedicated detail contract：未通过
- 稳定 stage chain contract：未通过
- 单 query detail 与 pilot/diagnostic 执行日志视角分离：未通过
- output / error / reasoning / audit 边界固化为正式 detail 模型：未通过

因此当前判断：

- **允许把 `external_adapter` 提升为 `recent summary` 候选模式**
- **不允许进入 `query detail / query history / query workspace`**

## Promotion Rules

当前推荐的判断规则：

### 可直接视为通用模式

- `query_id` 是治理生命周期主键
- `recent summary / query detail / query history` 的分层
- dedicated endpoint 优先于继续扩 `runtime-profile`
- history 的分页/游标兼容思路

### 暂时仍保留 `main_chat` 专用

- 当前 `Main Chat Query Workspace` 前端交互壳
- `main_chat` 专用的 history/workspace 文案
- `main_chat` 相关的专家模式入口联动

## Preconditions for Multi-Channel Expansion

未来若要把 query workspace/history 扩到其他 channel，必须先满足：

1. 该 channel 已有稳定 `query_id`
2. 已有 dedicated query detail contract
3. 已有统一 lifecycle stage 映射
4. 已能区分 recent summary 与 long history 的边界
5. 不需要前端再从通用 timeline 本地重建 query 模型

## Recommended Next Step

在继续做任何新的 channel 扩展前，先在 canonical spec 中把：

- 四层模型
- 推广规则
- 前置条件

写成正式 requirement。

推荐扩展顺序：

1. 先把 `main_chat` 当前模式写死为 canonical boundary
2. 先以 `subagent_lane` 作为第一个非 `main_chat` 的 `recent summary` 候选评估对象
3. 再以 `external_adapter` 作为第二个非 `main_chat` 的 `recent summary` 候选评估对象
4. 只有在 dedicated query detail contract 稳定后，才考虑让它们进入 `query detail`
5. `query history / query workspace` 暂时仍以 `main_chat` 为唯一完整实现

推荐停止条件：

- 在 `subagent_lane` 或 `external_adapter` 还没有通过 readiness checklist 前，不继续讨论它们的 `query history / query workspace` 形态
- 在 canonical spec 没有补齐前，不直接开多 channel query workspace 实现票

当前默认建议：

- `subagent_lane recent summary` 既然已经完成第一刀试点，下一步优先回到高层边界收口
- `external_adapter recent summary` 不作为默认立即推进项
- 只有在后续出现明确“需要对称验证 recent summary 模式是否跨 channel 成立”的需求时，才单独开启 `external_adapter` 试点

## Generic Recent Summary Abstraction

当前阶段推荐结论：

- **先不抽通用 assembler / service**
- **先写死共享字段集合**
- **等 `external_adapter recent summary` 真正进入实现后，再复评**

当前共享字段集合建议固定为：

- `query_id`
- `latest_stage`
- `latest_summary`
- `latest_timestamp`
- `recording_state`

当前可选共享字段：

- `latest_snapshot_id`
- `last_success_stage`
- `last_warning_stage`

为什么现在先不抽：

1. `main_chat` 与 `subagent_lane` 的成熟度还不对称
2. `external_adapter` 还没有 recent summary 的真实实现样本
3. 现在过早抽象，容易把 channel-specific 语义压平

## Exit Criteria

本次设计完成时，应能明确：

1. 当前哪些能力已经是通用 query 模式
2. 哪些能力仍然是 `main_chat` 专用
3. `subagent_lane` 与 `external_adapter` 当前分别停留在哪一层
4. 后续若扩到其他 channel，优先顺序是什么
