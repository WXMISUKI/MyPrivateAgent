# Design

## Approach
Follow the existing runtime contract gate pattern used by worker ownership and child executor dispatch:

1. `runtime_contract_smoke.py` emits a dedicated `recovery_retry_evidence` check.
2. `quality_gate_report.py` derives `runtime_contract_summary.recovery_retry_evidence_coverage` from that check.
3. `RuntimeContractGateService` normalizes both generated summary coverage and legacy reports.
4. `RuntimeContractSnapshotService` treats the coverage object and `retry_smoke` flag as stable fields.

## Smoke Evidence
The smoke check should execute the smallest real SDK path:

- create a run in an in-memory workspace store;
- create an approval continuation;
- read from a fresh SDK instance so the in-memory backend is not cross-process durable;
- call `submit_approval(..., retry_attempt=...)`;
- assert the fail-closed `recovery_failed_closed` event contains compact `recovery_operation.retry` evidence.

The check must preserve the current semantics: the retry evidence is audit metadata, not automatic retry execution.

## Coverage Shape
`recovery_retry_evidence_coverage` contains:

- `retry_smoke`
- `contract_version`
- `attempt_number`
- `max_attempts`
- `retry_status`
- `retryable`
- `terminal`
- `recovery_reason`
- `idempotency_key_present`

`retry_smoke` is true only when the check is healthy and the evidence proves bounded exhausted retry metadata for the expected fail-closed reason.
