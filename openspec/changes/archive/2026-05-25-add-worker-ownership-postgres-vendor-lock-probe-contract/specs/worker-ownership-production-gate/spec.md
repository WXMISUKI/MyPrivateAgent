## ADDED Requirements

### Requirement: Production ownership gate MUST expose PostgreSQL vendor lock probe blockers

The worker ownership production gate MUST expose PostgreSQL advisory lock probe evidence inside the `vendor_lock_semantics` section when a PostgreSQL vendor lock adapter seam is present or expected.

#### Scenario: PostgreSQL probe is missing

- **WHEN** the production ownership gate is inspected without PostgreSQL advisory lock probe readiness
- **THEN** the `vendor_lock_semantics` section evidence MUST include PostgreSQL probe contract version, status, advisory lock family, lock key derivation, lock scope, fencing binding, TTL/renewal strategy, failover behavior, stale cleanup, probe safety, execution flag, SQL-row-lease-not-vendor-lock evidence, and missing sections
- **AND** the `vendor_lock_semantics` section MUST remain blocked
- **AND** production default ownership enforcement MUST remain disabled

#### Scenario: PostgreSQL probe does not bypass production enablement

- **WHEN** the PostgreSQL advisory lock probe is ready
- **THEN** production default ownership MUST still require adapter capability readiness, target decision readiness, renewal supervisor readiness, rollout readiness, auto-claim policy readiness, audit evidence, and explicit production default enablement
- **AND** SQL row lease/fencing MUST NOT be treated as PostgreSQL advisory lock authority
