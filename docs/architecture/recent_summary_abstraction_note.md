# Recent Summary 抽象判断

## 1. 目的

本说明用于回答当前 `Phase I` 中一个非常具体的问题：

**`recent summary` 这一层，当前要不要抽成通用 assembler / service？**

这里的 `recent summary` 指：

- 最近若干条 query 摘要
- 不进入 dedicated detail
- 不进入 query history 分页
- 不进入 workspace 交互壳

## 2. 当前事实样本

### 2.1 `main_chat`

当前事实来源：

- `main_chat_trace_overview.recent_queries`
- `main_chat_query_history`

当前稳定字段：

- `query_id`
- `latest_stage`
- `latest_summary`
- `latest_timestamp`
- `latest_snapshot_id`
- `recording_state`

### 2.2 `subagent_lane`

当前事实来源：

- `subagent_lane_recent_summary`

当前稳定字段：

- `query_id`
- `latest_stage`
- `latest_summary`
- `latest_timestamp`
- `recording_state`

### 2.3 `external_adapter`

当前状态：

- 已完成 readiness 判断
- 已新增 `external_adapter_recent_summary` 真实实现样本，来源为 Query Control trace 中 `channel = external_adapter` 的 compact lifecycle evidence

这意味着我们当前只有：

- 一个完整样本：`main_chat`
- 一个轻量样本：`subagent_lane`
- 第二个轻量样本：`external_adapter`

## 3. 当前判断标准

要决定是否抽成通用 assembler，至少要看三件事：

1. 字段集合是否足够同构
2. 抽象后是否会压缩掉 channel-specific 语义
3. 复用收益是否已经高于抽象成本

## 4. 当前结论

当前**不建议**把 `recent summary` 立即抽成通用 assembler / service。

原因：

1. `main_chat` 与 `subagent_lane` 虽然已有最小共享字段，但层级成熟度明显不同。
2. `subagent_lane` 与 `external_adapter` 都只在 recent summary 层形成轻量样本，还没有共同进入 detail/history/workspace。
3. 当前最重要的是先把共享字段集合写死，而不是为了“看起来优雅”提前抽象。

因此当前推荐策略是：

- 先保持 channel-specific builder：
  - `main_chat recent summary`
  - `subagent_lane recent summary`
  - `external_adapter recent summary`
- 但明确共享字段集合：
  - `query_id`
  - `latest_stage`
  - `latest_summary`
  - `latest_timestamp`
  - `recording_state`

可选共享字段：

- `latest_snapshot_id`
- `last_success_stage`
- `last_warning_stage`

## 5. 什么时候再复评

当以下任一条件满足时，再重新评估是否抽象：

1. 新增第三个以上非 `main_chat` channel 进入 recent summary 层
2. 当前多个 builder 已经出现明显重复且维护成本上升
3. `subagent_lane` 与 `external_adapter` 的后续 detail readiness 都稳定后，仍证明 recent summary 字段完全同构

在这之前，默认继续保持：

- 共享字段集合
- channel-specific builder

## 6. 对 Phase I 的作用

这份判断直接支持：

- `I-3 Generic Recent Summary Abstraction`

并给出当前阶段的稳定口径：

**先写死共享字段集合，不急着抽象成通用 assembler。**
