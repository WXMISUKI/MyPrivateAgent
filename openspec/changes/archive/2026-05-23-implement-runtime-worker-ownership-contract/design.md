## Overview

这是一刀最小可验证 ownership seam。它不声称已经具备跨实例 SQL lease 或 distributed lock；它先把 lease/fencing/heartbeat 的 Interface 固定下来，并提供 in-memory adapter 供 SDK 和后续实现使用。

## Module Shape

新增 `backend/agent_framework/worker_ownership.py`：

- `build_worker_ownership_contract(...)`
- `RuntimeWorkerLease`
- `InMemoryRuntimeWorkerOwnershipStore`
- reason/status 常量

Store Interface：

- `claim_run(run_id, worker_id, lease_ttl_seconds=...)`
- `heartbeat(run_id, worker_id, lease_id, lease_ttl_seconds=...)`
- `validate_ownership(run_id, worker_id, lease_id, fencing_token)`
- `get_lease(run_id)`

## Semantics

- First claim creates an active lease.
- Same worker + lease may refresh via heartbeat without changing fencing token.
- Another worker cannot claim while active lease exists.
- Expired lease can be replaced by a newer lease with a greater fencing token.
- Stale fencing token validation returns fail-closed evidence.

## Recovery Operation Integration

`build_recovery_operation_record(...)` accepts optional `worker_ownership`. If present, it is compacted into the operation payload. If absent, existing `implemented=false` payload remains unchanged.

## Non-Goals

- No SQL adapter.
- No DB migration.
- No automatic SDK recovery gate enforcement.
- No retry policy implementation.

## Validation

- Focused tests for worker claim / heartbeat / stale token / expired lease.
- Existing SDK and Runtime Surface tests to guard compatibility.
- OpenSpec strict validation.
