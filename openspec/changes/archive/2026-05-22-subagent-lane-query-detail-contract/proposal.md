# subagent-lane-query-detail-contract

## Why

`subagent_lane query detail readiness` now proves that the channel can advance beyond recent summary. The next backend slice is a dedicated single-query detail contract so callers do not have to reconstruct subagent lifecycle details from raw timeline entries.

## What Changes

- Add a backend-only `subagent_lane query detail` read model.
- Expose a dedicated Runtime Profile endpoint for a single `subagent_lane` `query_id`.
- Reuse the existing Query Control trace source and keep detail semantics separate from child executor replay, history, and workspace.
- Add focused backend tests and docs.

## Capabilities

### New Capabilities
- `subagent-lane-query-detail-contract`: exposes a dedicated single-query detail contract for `subagent_lane`.

### Modified Capabilities

## Impact

- 收口对象：`RuntimeSurfaceService`, runtime surface builders, health router endpoint, focused backend tests.
- 后端 contract：`/api/runtime-profile/subagent-lane-query-detail`.
- 前端消费点：none required in this slice.
- 文档真源：`docs/architecture/runtime_contracts.md`, `docs/roadmap/next_phase_hardening.md`, `docs/test_manual.md`.
- 非目标：不做 `subagent_lane query history`、不做 workspace、不中断 child executor replay/summary/merged semantics、不做 external_adapter 对称实现。
