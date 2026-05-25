# surface-worker-ownership-governance-summary

## Why

`worker_ownership_store_mode_coverage` is already normalized into Runtime Contract Gate summaries and guarded by snapshot/specs. Governance Timeline compact runtime contract warnings currently expose retry, checkpoint, approval, approved tool, SDK tool, and embedded persistence coverage, but not whether worker ownership store mode smoke evidence is covered.

## What Changes

- Extend runtime contract warning summary text with `worker_ownership=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary beside existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不改变 worker ownership lease/fencing/runtime 行为，不修改 smoke/quality gate derivation，不修改 Runtime Contract Gate fingerprint/dedupe 语义。
