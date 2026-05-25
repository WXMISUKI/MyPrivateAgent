## ADDED Requirements

### Requirement: Runtime worker ownership MUST expose an opt-in renewal supervisor seam

The runtime MUST provide a renewal supervisor seam that can renew worker ownership leases only when explicitly invoked and MUST NOT start background work by default.

#### Scenario: Explicit renewal refreshes a valid lease

- **GIVEN** a worker owns a valid lease
- **WHEN** the renewal supervisor is explicitly asked to renew once with the matching run id, worker id, lease id, and fencing token
- **THEN** it MUST call the ownership store heartbeat path
- **AND** it MUST return compact renewal evidence with `renewal_status = renewed`
- **AND** it MUST NOT start a thread, timer, worker, or loop

#### Scenario: Explicit renewal fails closed on stale evidence

- **GIVEN** a worker lease exists
- **WHEN** the renewal supervisor is asked to renew once with stale fencing, mismatched identity, expired ownership, or no store
- **THEN** it MUST return compact blocked evidence
- **AND** it MUST include the ownership failure reason when available
- **AND** it MUST NOT authorize recovery execution

#### Scenario: Renewal supervisor contract exposes seam evidence

- **WHEN** worker ownership renewal supervisor readiness is inspected
- **THEN** the contract MUST expose `renew_once_supported`, `owner_identity_required`, `ttl_interval_policy_ready`, and `lease_loss_fail_closed`
- **AND** `supervisor_enabled_by_default` MUST remain false unless explicitly enabled after the readiness sections are complete
