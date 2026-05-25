# surface-child-executor-gate-governance-summary

## Why

`child_executor_promotion_gate_coverage` is already normalized into Runtime Contract Gate summaries and guarded by snapshot/specs. Governance Timeline compact runtime contract warnings currently expose recovery, ownership, approval, tool, and persistence coverage, but not whether the child executor promotion gate smoke evidence is covered.

## What Changes

- Extend runtime contract warning summary text with `child_executor_gate=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 child executor promotion gate 决策，不启用真实 child executor dispatch，不修改 smoke/quality gate derivation，不修改 Runtime Contract Gate fingerprint/dedupe 语义。
