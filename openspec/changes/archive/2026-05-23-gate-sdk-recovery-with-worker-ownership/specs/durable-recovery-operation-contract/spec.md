# durable-recovery-operation-contract Specification Delta

## MODIFIED Requirements

### Requirement: Fail-closed recovery MUST record blocked operation evidence

The SDK MUST record blocked recovery operation evidence whenever an actual recovery entrypoint fails closed, including worker ownership validation failures when ownership enforcement is explicitly configured.

#### Scenario: Recovery is blocked by worker ownership gate

- **WHEN** a recovery attempt fails closed because worker ownership validation fails
- **THEN** the SDK MUST emit a `recovery_failed_closed` event
- **AND** the event payload MUST include `recovery_operation.operation_status = blocked`
- **AND** the operation MUST include compact `worker_ownership` evidence
- **AND** run metadata MUST retain the latest recovery operation
