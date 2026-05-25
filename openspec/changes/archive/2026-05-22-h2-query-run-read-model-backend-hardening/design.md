## Context

`main_chat_query_detail`、`main_chat_query_history`、`recent_queries` 和 `main_chat_trace_overview` 已经形成了分层 read model，但现状仍有两类风险：

1. `runtime-profile` 还承担了部分兼容和聚合压力。
2. 前端治理视图仍保留不少 fallback / local interpretation。

当前治理优先级已经从局部 history 浏览壳转向 Runtime Core 和 Read Model 收口，所以这一步的设计目标不是继续加 UI，而是把 query/detail/history 的主 contract 边界定得更稳。

## Goals / Non-Goals

**Goals:**

- 让 `main_chat_query_detail` 成为稳定的 query 级 read model 主入口。
- 让 `main_chat_query_history` 成为稳定的分页/长历史 read model 主入口。
- 保持 `recent_queries` 作为 lightweight summary，不让它承担 history 的扩展职责。
- 让 `RuntimeSurfacePanel` 和 `GovernanceTimelinePanel` 共享同一套 query/detail/history contract 解释逻辑。
- 把 `runtime-profile` 约束为兼容入口，而不是主要增长入口。

**Non-Goals:**

- 不修改 `main_chat` 的底层运行时语义。
- 不新增新的 channel 级历史模型。
- 不做前端治理视图的重布局。
- 不移除现有兼容字段。
- 不把 query history 的复杂度重新推回通用 timeline 本地重建。

## Decisions

### 1. Dedicated endpoint remains the primary growth path

Reasoning:

- dedicated endpoint 更容易承载 query/detail/history 的单一职责。
- `runtime-profile` 适合作为聚合 / 兼容入口，但不适合作为后续所有扩展的主承载层。

Alternatives considered:

- Keep expanding `runtime-profile` only: simpler initially, but quickly turns into an overloaded contract.
- Move everything to a brand new query service: cleaner in theory, but would increase integration cost and duplication.

### 2. Query detail and query history stay separate contracts

Reasoning:

- `main_chat_query_detail` answers “what happened for one query”.
- `main_chat_query_history` answers “what happened across many queries”.
- Combining the two would make both summaries and pagination harder to reason about.

Alternatives considered:

- Merge detail and history into one endpoint: convenient for some callers, but blurs responsibilities.
- Keep only recent summaries: insufficient for longer-term governance review.

### 3. Frontend interpretation must be shared

Reasoning:

- `RuntimeSurfacePanel` and `GovernanceTimelinePanel` are different surfaces over the same read model.
- Shared normalization avoids divergent labels, fallback behavior, and route interpretation.

Alternatives considered:

- Each panel keeps its own helper set: fastest short-term, but causes drift.
- Add a giant shared store: too heavy for the current boundary and likely to spread UI coupling.

### 4. History expansion stays cursor-friendly

Reasoning:

- Query history is naturally time-sequenced and may grow over time.
- The contract should remain compatible with page-based usage while preserving cursor evolution space.

## Risks / Trade-offs

- [Risk] `runtime-profile` and dedicated endpoints may overlap for a period. → [Mitigation] Keep `runtime-profile` as compatibility surface and designate dedicated endpoints as the primary extension path.
- [Risk] Frontend consumer parity could still drift if shared helpers are not reused. → [Mitigation] Require both `RuntimeSurfacePanel` and `GovernanceTimelinePanel` to consume the same normalization helpers.
- [Risk] History pagination shape may need to evolve. → [Mitigation] Keep cursor-compatible metadata in the contract now.

## Migration Plan

1. Keep `main_chat_query_detail` and `main_chat_query_history` as the read model anchors.
2. Ensure `runtime-profile` continues to expose compatibility fields, but no new growth should depend on it exclusively.
3. Reuse the same contract interpretation helper in both front-end consumers.
4. Update docs and tests together when the read model contract expands.

Rollback strategy:

- If a new field causes inconsistency, revert the field addition first and keep the contract boundary.
- Avoid rolling back the dedicated endpoint boundary unless absolutely necessary.

## Open Questions

- Should future history pagination prefer cursor-first responses or continue page/page_size plus next_cursor compatibility for a longer window?
- Are there any remaining `runtime-profile` consumers outside the governance views that still need the compatibility layer?

