# runtime-worker-ownership-contract Specification

## ADDED Requirements

### Requirement: Runtime MUST expose worker ownership as a first-class contract

The runtime MUST define a machine-readable worker ownership contract for any recovery or continuation operation that may run outside the original process.

#### Scenario: Ownership contract is declared

- **WHEN** a consumer inspects runtime recovery capabilities
- **THEN** the runtime MUST expose whether worker ownership is implemented
- **AND** it MUST expose the ownership contract version
- **AND** it MUST distinguish ownership readiness from durable storage readiness

### Requirement: Worker ownership MUST use lease and fencing evidence

The runtime MUST use explicit lease and fencing evidence before a worker can claim recovery execution ownership.

#### Scenario: Worker claims ownership

- **WHEN** a worker attempts to claim a run for recovery
- **THEN** it MUST create or refresh a lease record
- **AND** the lease MUST include `run_id`, `worker_id`, `lease_id`, `fencing_token`, `lease_expires_at`, and `claimed_at`
- **AND** the claim MUST fail closed if an unexpired lease with a newer or equal fencing token exists

#### Scenario: Worker heartbeat refreshes ownership

- **GIVEN** a worker owns a lease
- **WHEN** it sends a heartbeat before expiration
- **THEN** the lease expiration MAY be extended
- **AND** the fencing token MUST remain stable for the same lease
- **AND** the heartbeat MUST NOT create a parallel owner

### Requirement: Recovery operation MUST include ownership evidence when implemented

Recovery operation evidence MUST include ownership fields once worker ownership is implemented.

#### Scenario: Recovery operation runs under a worker lease

- **GIVEN** worker ownership is implemented
- **AND** a worker has claimed a recovery lease
- **WHEN** the worker records a recovery operation
- **THEN** the operation evidence MUST include `worker_ownership.implemented = true`
- **AND** it MUST include `worker_id`, `lease_id`, `fencing_token`, and `lease_status`
- **AND** it MUST remain compact and non-executable

### Requirement: Ownership loss MUST fail closed

The runtime MUST stop or block recovery continuation when worker ownership is lost.

#### Scenario: Lease expires before recovery completes

- **WHEN** a worker tries to continue recovery after its lease expires
- **THEN** the runtime MUST block the continuation
- **AND** it MUST record `operation_status = blocked`
- **AND** the recovery reason MUST be `worker_ownership_lost`

#### Scenario: Fencing token is stale

- **WHEN** a worker presents a stale fencing token
- **THEN** the runtime MUST reject the recovery operation
- **AND** it MUST record `operation_status = blocked`
- **AND** the recovery reason MUST be `stale_worker_fencing_token`
