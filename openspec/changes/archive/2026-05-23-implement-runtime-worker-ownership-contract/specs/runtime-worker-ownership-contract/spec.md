# runtime-worker-ownership-contract Specification Delta

## MODIFIED Requirements

### Requirement: Worker ownership MUST use lease and fencing evidence

The runtime MUST use explicit lease and fencing evidence before a worker can claim recovery execution ownership. The first implementation MAY provide an in-memory adapter seam, but it MUST keep the same claim, heartbeat, validation, and fencing semantics expected from future durable adapters.

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
