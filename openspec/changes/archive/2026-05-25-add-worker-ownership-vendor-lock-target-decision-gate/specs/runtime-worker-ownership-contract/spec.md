## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose vendor lock target decision evidence

The runtime worker ownership contract MUST expose a read-only vendor lock target decision before vendor-specific distributed lock semantics can be treated as production-ready.

#### Scenario: Default target decision is blocked

- **WHEN** the runtime worker ownership contract is inspected without a vendor lock target decision
- **THEN** `worker_ownership.vendor_lock_semantics.policy.target_decision.overall_status` MUST be `blocked`
- **AND** `target_backend`, `lock_adapter_kind`, `lock_scope`, `fencing_strategy`, `ttl_renewal_strategy`, `failover_strategy`, and `stale_owner_cleanup_strategy` gaps MUST be machine-readable
- **AND** `sql_row_lease_is_vendor_lock` MUST be false
- **AND** `production_lock_allowed` MUST be false

#### Scenario: Target decision is embedded in vendor lock semantics

- **WHEN** `worker_ownership.vendor_lock_semantics` is inspected
- **THEN** its policy MUST include `target_decision`
- **AND** a blocked target decision MUST keep vendor lock semantics blocked

#### Scenario: Target decision remains non-executable

- **WHEN** a target backend, adapter kind, scope, fencing strategy, TTL/renewal strategy, failover strategy, stale owner cleanup strategy, and production allowment are recorded
- **THEN** the target decision MAY report `overall_status = ready`
- **AND** it MUST NOT create or start a vendor lock adapter
- **AND** it MUST NOT treat SQL row lease/fencing as vendor-specific distributed lock semantics
