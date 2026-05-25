# durable-recovery-operation-contract Specification Delta

## MODIFIED Requirements

### Requirement: SDK MUST expose a recovery operation boundary

The Embedded SDK contract MUST declare the supported durable recovery operation entrypoints and the worker ownership boundary. Future worker ownership, retry, and audit hardening contracts MUST extend or consume this recovery operation evidence instead of replacing it with parallel recovery status models.

#### Scenario: Contract declares operation boundary

- **WHEN** a consumer calls `build_contract()`
- **THEN** the contract MUST include `recovery_operation_contract`
- **AND** it MUST list `submit_approval.approved` and `resume_run.continue_loop` as supported operation entrypoints
- **AND** it MUST state that worker ownership / lease is not implemented until the worker ownership contract is implemented
- **AND** future retry and audit contracts MUST preserve the same operation identity fields
