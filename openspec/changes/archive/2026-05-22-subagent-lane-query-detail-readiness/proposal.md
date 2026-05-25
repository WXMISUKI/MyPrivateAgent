# subagent-lane-query-detail-readiness

## Why

`subagent_lane recent summary` has landed as the first non-`main_chat` query read-model trial. Before building a full detail endpoint, the backend needs a dedicated readiness contract that says whether this channel is eligible for `query detail` promotion.

## What Changes

- Add a backend-only `subagent_lane query detail readiness` contract.
- Expose a dedicated Runtime Profile endpoint for the readiness read model.
- Keep the result as assessment / gate metadata only; do not implement query detail, history, or workspace in this change.
- Close the older follow-up items that depended on deciding whether the recent summary trial passed.

## Capabilities

### New Capabilities
- `subagent-lane-query-detail-readiness`: exposes whether `subagent_lane` satisfies the preconditions for a future dedicated query detail contract.

### Modified Capabilities

## Impact

- 收口对象：`RuntimeSurfaceService`, `SubagentLaneRecentSummaryBuilder`/new builder seam, health router dedicated endpoint, focused backend tests.
- 后端 contract：new readiness read model under Runtime Profile.
- 前端消费点：none required in this slice; UI can consume the endpoint later.
- 文档真源：`docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, OpenSpec change tasks.
- 非目标：不实现 `subagent_lane query detail`、不做 query history/workspace、不新增数据库迁移、不做外部 adapter 对称试点。
