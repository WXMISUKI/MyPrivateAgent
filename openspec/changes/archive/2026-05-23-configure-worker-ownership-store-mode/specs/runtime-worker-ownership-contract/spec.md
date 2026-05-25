## ADDED Requirements

### Requirement: Runtime MUST configure default worker ownership store mode

The runtime MUST expose a configurable default worker ownership store mode while keeping the default behavior compatible with the existing in-memory ownership adapter.

#### Scenario: Default ownership store remains memory-only

- **WHEN** no `WORKER_OWNERSHIP_STORE_MODE` is configured
- **THEN** default embedded runtime dependencies MUST use the in-memory worker ownership store
- **AND** the runtime contract MUST report `worker_ownership.adapter_kind = "in_memory"`
- **AND** it MUST report `worker_ownership.durable = false`

#### Scenario: SQL ownership store can be selected explicitly

- **WHEN** `WORKER_OWNERSHIP_STORE_MODE` is configured as `strict_sql`
- **THEN** default embedded runtime dependencies MUST use the SQLAlchemy worker ownership store
- **AND** the runtime contract MUST report `worker_ownership.adapter_kind = "sqlalchemy"`
- **AND** it MUST report `worker_ownership.durable = true`

#### Scenario: SQL ownership bootstrap failure fails closed in strict mode

- **WHEN** `WORKER_OWNERSHIP_STORE_MODE` is configured as `strict_sql`
- **AND** the SQL ownership store cannot initialize
- **THEN** default dependency construction MUST fail closed
- **AND** it MUST NOT silently return an in-memory ownership store

#### Scenario: SQL ownership bootstrap failure can fallback in prefer mode

- **WHEN** `WORKER_OWNERSHIP_STORE_MODE` is configured as `prefer_sql_with_fallback`
- **AND** the SQL ownership store cannot initialize
- **THEN** default dependency construction MAY return an in-memory ownership store
- **AND** the runtime contract MUST still expose the configured ownership mode for diagnosis

#### Scenario: Runtime contract exposes ownership store mode source

- **WHEN** a consumer inspects the embedded runtime factory contract
- **THEN** `default_runtime_profile` MUST include `worker_ownership_store_mode`
- **AND** it MUST include `worker_ownership_store_mode_source`
- **AND** `configurable_bootstrap_knobs` MUST include `WORKER_OWNERSHIP_STORE_MODE`
