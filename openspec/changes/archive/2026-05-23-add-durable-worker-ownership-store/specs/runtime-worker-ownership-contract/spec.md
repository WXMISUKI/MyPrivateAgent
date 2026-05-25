## ADDED Requirements

### Requirement: Runtime MUST support a durable worker ownership adapter

The runtime MUST provide an opt-in durable worker ownership adapter that preserves the same lease, heartbeat, validation, and fencing semantics as the in-memory adapter while storing ownership evidence in SQL-backed state.

#### Scenario: Durable adapter declares SQL ownership capability

- **WHEN** a durable worker ownership store is inspected through its contract
- **THEN** it MUST report `adapter_kind = "sqlalchemy"`
- **AND** it MUST report `durable = true`
- **AND** it MUST expose `claim_run`, `heartbeat`, `validate_ownership`, and `get_lease`

#### Scenario: Durable claim survives a new store instance

- **GIVEN** a SQL-backed worker ownership store has claimed a run
- **WHEN** another store instance uses the same database session factory
- **THEN** it MUST read the same lease through `get_lease`
- **AND** it MUST block a competing worker while the lease is unexpired

#### Scenario: Durable expired lease replacement increments fencing

- **GIVEN** a SQL-backed worker ownership lease has expired
- **WHEN** another worker claims the same run
- **THEN** the new lease MUST replace the expired ownership
- **AND** the new lease MUST use a greater `fencing_token`

#### Scenario: Durable heartbeat preserves fencing

- **GIVEN** a SQL-backed worker owns an unexpired lease
- **WHEN** the worker sends a heartbeat with the current `worker_id` and `lease_id`
- **THEN** the lease expiration MUST be refreshed
- **AND** the `fencing_token` MUST remain unchanged

#### Scenario: Durable stale fencing fails closed

- **WHEN** a worker validates SQL-backed ownership with a stale `fencing_token`
- **THEN** validation MUST return `owned = false`
- **AND** the reason MUST be `stale_worker_fencing_token`
- **AND** the recovery entrypoint MUST NOT treat the evidence as executable authorization
