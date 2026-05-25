# subagent-lane-detail-gate-trace

## Why

`subagent_lane_query_detail_coverage` is now available in the runtime contract gate summary, but degraded runtime contract traces do not yet normalize it into payloads or fingerprint inputs. That means governance timeline dedupe can miss the transition from "detail smoke missing" to "detail smoke covered".

## What Changes

- Normalize `subagent_lane_query_detail_coverage` in runtime contract degraded trace payloads.
- Include the normalized coverage in degraded trace fingerprint / dedupe semantics.
- Keep scope backend-only; no frontend timeline rendering changes in this slice.

## Impact

- 收口对象：`backend/routers/health.py`, `tests.agent_framework.test_health_router`, runtime contract docs.
- Contract：`runtime_contract_gate_degraded.payload.runtime_contract_summary.subagent_lane_query_detail_coverage`.
- 非目标：不改 quality gate report 生成逻辑、不新增前端卡片、不改变 subagent detail endpoint。
