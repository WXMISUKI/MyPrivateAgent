# durable-recovery-operation-contract Specification Delta

## MODIFIED Requirements

### Requirement: Successful durable reattachment MUST record recovered operation evidence

The SDK MUST record a recovered operation when a persisted descriptor is reattached through the continuation registry during an actual recovery entrypoint call, and the latest operation evidence MUST be available to the Runtime Surface recovery read model.

#### Scenario: Approved tool continuation recovers via registry

- **GIVEN** a persisted tool continuation descriptor is available
- **AND** the current SDK instance reattaches it through the continuation registry
- **WHEN** `submit_approval(request_id, "approved")` completes recovery
- **THEN** run metadata MUST include a latest recovery operation with `operation_status = recovered`
- **AND** the operation entrypoint MUST be `submit_approval.approved`
- **AND** a subsequent recovery probe MUST expose the latest recovery operation for `run_recovery` consumption

#### Scenario: Loop continuation recovers via registry

- **GIVEN** a persisted loop continuation descriptor is available
- **AND** the current SDK instance reattaches it through the continuation registry
- **WHEN** `resume_run(run_id, continue_loop=True)` completes recovery
- **THEN** run metadata MUST include a latest recovery operation with `operation_status = recovered`
- **AND** the operation entrypoint MUST be `resume_run.continue_loop`
- **AND** a subsequent recovery probe MUST expose the latest recovery operation for `run_recovery` consumption
