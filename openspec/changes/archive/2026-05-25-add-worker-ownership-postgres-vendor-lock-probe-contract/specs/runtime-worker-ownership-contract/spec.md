## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose PostgreSQL vendor lock probe evidence

The runtime worker ownership contract MUST expose a side-effect-free PostgreSQL advisory lock probe contract before a PostgreSQL vendor lock adapter can be considered production-ready.

#### Scenario: PostgreSQL probe defaults to blocked

- **WHEN** the PostgreSQL advisory lock probe contract is built without backend metadata
- **THEN** it MUST report `overall_status = blocked`
- **AND** it MUST expose missing sections for advisory lock family, lock key derivation, lock scope, fencing token binding, TTL/renewal strategy, failover behavior, stale owner cleanup, and probe safety
- **AND** it MUST report `executes_probe = false`
- **AND** it MUST report SQL row lease/fencing as non-vendor-lock authority

#### Scenario: Vendor lock adapter embeds PostgreSQL probe evidence

- **WHEN** `worker_ownership.vendor_lock_semantics.policy.adapter_contract` is inspected for a PostgreSQL adapter
- **THEN** it MUST include `backend_probe`
- **AND** a blocked PostgreSQL probe MUST keep the adapter contract blocked
- **AND** the runtime MUST NOT connect to PostgreSQL or execute advisory lock SQL as a side effect

#### Scenario: Ready PostgreSQL probe remains descriptive

- **WHEN** PostgreSQL advisory lock family, key derivation, scope, fencing binding, TTL/renewal, failover, stale cleanup, and probe safety evidence are complete
- **THEN** the probe MAY report `overall_status = ready`
- **AND** it MUST still not enable production default worker ownership by itself
