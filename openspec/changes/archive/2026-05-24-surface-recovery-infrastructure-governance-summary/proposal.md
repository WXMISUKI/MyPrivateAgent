# surface-recovery-infrastructure-governance-summary

## Why

Runtime Contract Gate already normalizes recovery retry scheduler and durable recovery loader coverage. Snapshot guards also protect both fields. Governance Timeline compact runtime contract warnings should expose these recovery infrastructure coverage states without requiring operators to expand the full payload.

## What Changes

- Add `recovery_retry_scheduler=<covered|missing|unknown>` to frontend compact runtime contract summaries.
- Add `durable_loader=<covered|missing|unknown>` to frontend compact runtime contract summaries and backend degraded trace detail.
- Normalize `durable_recovery_loader_coverage` in Health Router trace payloads.
- Add focused backend and frontend assertions.

## Impact

- 收口对象：`backend/routers/health.py`, `frontend-vue/src/services/governanceFormatting.js`, focused tests, docs/specs.
- 非目标：不改变 retry scheduler execution、durable loader behavior、quality gate derivation or snapshot guards。
