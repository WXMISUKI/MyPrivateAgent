# runtime-worker-ownership-contract Specification Delta

## MODIFIED Requirements

### Requirement: Ownership loss MUST fail closed

The runtime MUST stop or block recovery continuation when worker ownership is lost. The first SDK implementation MAY enforce this only when a worker ownership store and ownership evidence are explicitly supplied.

#### Scenario: Fencing token is stale

- **WHEN** a worker presents a stale fencing token
- **THEN** the runtime MUST reject the recovery operation
- **AND** it MUST record `operation_status = blocked`
- **AND** the recovery reason MUST be `stale_worker_fencing_token`
- **AND** the recovery entrypoint MUST NOT execute the recovered continuation

#### Scenario: Valid ownership allows recovery

- **GIVEN** worker ownership is implemented
- **AND** the worker presents valid lease and fencing evidence
- **WHEN** the recovery entrypoint records a recovery operation
- **THEN** the operation evidence MUST include validated `worker_ownership`
- **AND** the recovery entrypoint MAY continue execution

#### Scenario: Ownership store is not configured

- **WHEN** SDK recovery runs without an ownership store
- **THEN** existing recovery behavior MUST remain compatible
- **AND** operation evidence MUST continue to report `worker_ownership.implemented = false`
