## Why

Recovery retry scheduler, durable recovery loader, and child executor dispatcher coverage are already enforced by runtime contract gate and snapshot code, but older canonical specs still describe only the earlier coverage set. This makes future governance work riskier because spec readers see a narrower contract than the implementation actually guards.

## What Changes

- Align trace summary coverage spec with the current normalized coverage set, including recovery retry scheduler, durable recovery loader, child executor dispatcher, checkpoint cursor, and recovery retry evidence.
- Align nested snapshot spec with the current stable `runtime_contract_summary` guard fields for recovery infrastructure and dispatcher coverage.
- Keep behavior unchanged; this is a contract/spec debt closure backed by existing focused tests.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `runtime-contract-trace-summary-coverage`: Expand the supported coverage sections and compact labels to match the current degraded trace payload/detail contract.
- `runtime-contract-summary-nested-snapshot`: Expand the nested summary guard scenarios to include recovery retry scheduler, durable recovery loader, and child executor dispatcher coverage.

## Impact

- 收口对象：OpenSpec canonical specs and focused verification around Health Router degraded trace and Runtime Contract Snapshot guard.
- 受影响后端 contract：`runtime_contract_gate_degraded.payload.runtime_contract_summary`, `runtime_contract_gate_degraded.detail`, `RuntimeContractSnapshotService` stable field guard.
- 受影响前端消费点：Governance Timeline compact runtime contract warning summaries, only as an already-implemented consumer; no frontend behavior change.
- 文档真源：`openspec/specs/runtime-contract-trace-summary-coverage/spec.md`, `openspec/specs/runtime-contract-summary-nested-snapshot/spec.md`, `docs/architecture/runtime_contracts.md`.
- 非目标：不新增 coverage 字段、不改变 gate derivation、不改变 snapshot behavior、不改 retry scheduler / durable loader / dispatcher runtime execution。
