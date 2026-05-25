## Design

### Audit Readiness Contract

The production audit contract describes whether the runtime can retain and summarize compact recovery operation evidence:

- `contract_version`
- `ready`
- `operation_history_supported`
- `audit_summary_supported`
- `timeline_writer_available`
- `idempotent_trace_dedupe`
- `authorization_source = false`
- `required_evidence`
- `non_goals`

This does not require automatic SDK trace writing. The existing `RecoveryAuditTimelineService` remains opt-in and fail-open.

### Production Gate Semantics

`build_embedded_sdk_persistence_interface()` can mark `recovery_audit_operation_history` ready because the runtime now has:

- compact operation record contract
- bounded operation history read model
- recovery audit summary
- opt-in trace writer with dedupe key

The durable workspace production recovery gate still remains blocked by registry binding policy, checkpoint/cursor production gate, worker ownership production gate, and rollout.

### Quality Gate Semantics

Runtime smoke will emit audit readiness evidence as part of the embedded persistence posture check. Quality Gate and Runtime Contract Gate normalize that evidence into `recovery_audit_operation_history_coverage.audit_smoke` and fail closed for old or dirty reports.

### Non-Goals

- No production cross-process recovery executor.
- No default audit trace writing from SDK recovery.
- No worker lease validation.
- No audit evidence as execution authorization.
