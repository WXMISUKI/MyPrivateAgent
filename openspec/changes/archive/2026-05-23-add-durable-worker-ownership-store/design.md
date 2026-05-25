## Context

The current worker ownership seam lives in `backend/agent_framework/worker_ownership.py` and is already exposed through `EmbeddedRuntimeDependencies` and `EmbeddedRuntimeFactory.build_runtime_contract()`. The default store is in-memory, so it validates lease/fencing semantics in-process but cannot survive process restarts or coordinate separate workers.

The existing persistence pattern for embedded runtime state uses SQLAlchemy models plus a `session_factory`-injected store. This change follows that pattern for ownership leases while keeping the SDK recovery gate descriptor-evidence driven.

## Goals / Non-Goals

**Goals:**

- Provide a SQLAlchemy-backed worker ownership store with the same public methods as the in-memory store.
- Persist one active ownership row per `run_id`, including worker, lease, fencing token, heartbeat, and expiration evidence.
- Preserve fail-closed behavior for active competing claims, expired ownership validation, stale fencing tokens, and mismatched leases.
- Mark SQL-backed ownership evidence as `adapter_kind = "sqlalchemy"` and `durable = true`.
- Keep runtime contract shape compatible with the current dependency boundary.

**Non-Goals:**

- Do not switch the default runtime dependency from in-memory to SQL in this slice.
- Do not implement cross-region distributed locks, advisory locks, or database-vendor-specific row locking.
- Do not add a background heartbeat scheduler or automatic SDK lease claim.
- Do not change recovery behavior when persisted descriptors have no `worker_ownership` evidence.

## Decisions

- **Use a dedicated ORM record instead of embedding ownership inside run metadata.** This keeps lease/fencing updates independent from recovery operation history and avoids rewriting large run snapshots for every heartbeat. Alternative considered: storing ownership inside embedded workspace metadata, rejected because heartbeat is a high-churn ownership operation.
- **Keep the store API duck-compatible with the in-memory store.** SDK and runtime factory consumers already call `claim_run`, `heartbeat`, `validate_ownership`, and `get_lease`; a matching SQL adapter avoids a new abstraction layer in this slice. Alternative considered: introducing a formal protocol class first, deferred until more adapters exist.
- **Use monotonic fencing per run based on the persisted row.** Replacement after expiration increments the previous token, while refreshing the same worker lease preserves the token. Alternative considered: global sequence tokens, rejected as unnecessary for the current single-row-per-run contract.
- **Fail closed on SQL operation errors.** Ownership is an authorization boundary for recovery execution; unlike optional governance trace writers, it must not silently fall back to in-memory state once a durable store is explicitly selected.

## Risks / Trade-offs

- **Concurrent claims on databases without row locks may race** -> The table uses `run_id` uniqueness and the store re-reads/updates one row per claim; true multi-worker production deployments should later add database-specific locking or optimistic version checks.
- **SQLite tests do not prove distributed lock semantics** -> Tests verify durable persistence and fencing semantics, not vendor-specific lock isolation.
- **New table requires migration awareness** -> Add an ORM model and Alembic revision, while tests continue to use `Base.metadata.create_all` for focused verification.
- **Default runtime remains non-durable** -> This is intentional; switching defaults should be a later explicit OpenSpec change after deployment config and migration expectations are clear.
