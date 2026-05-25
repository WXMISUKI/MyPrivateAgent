# subagent-detail-governance-summary

## Why

`subagent_lane_query_detail_coverage` is now written into runtime contract degraded trace payloads and dedupe fingerprints. Governance Timeline still summarizes runtime contract warnings without this field, so operators must expand the payload to see whether subagent lane query detail is covered.

## What Changes

- Extend runtime contract warning summary text with `subagent_detail=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary.
- Add focused frontend service and panel tests.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs.
- 非目标：不新增治理面板布局、不改后端 payload、不新增路由或 API。
