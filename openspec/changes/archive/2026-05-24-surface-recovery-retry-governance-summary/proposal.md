# surface-recovery-retry-governance-summary

## Why

`recovery_retry_evidence_coverage` is now normalized into runtime contract degraded trace payloads and fingerprints. Governance Timeline still renders the compact runtime contract warning summary without this field, so operators may need to expand the payload to see whether retry evidence coverage is present.

## What Changes

- Extend runtime contract warning summary text with `recovery_retry=<covered|missing|unknown>`.
- Keep the display as a compact one-line summary next to the existing runtime contract labels.
- Add focused frontend formatting and panel assertions.

## Impact

- 收口对象：`frontend-vue/src/services/governanceFormatting.js`, focused Vitest tests, docs/specs.
- 非目标：不新增 retry scheduler，不改后端 payload/fingerprint，不新增 API，不改变 Runtime Contract Gate 语义。
