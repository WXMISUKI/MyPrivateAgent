# embedded-sdk-persistence-interface Specification Delta

## MODIFIED Requirements

### Requirement: Runtime dependencies MUST centralize embedded recovery seams

The embedded runtime dependency bundle MUST centralize shared recovery seams used by SDK, facade, and Runtime Surface consumers.

#### Scenario: Dependency bundle exposes recovery seams

- **WHEN** the embedded runtime factory contract is inspected
- **THEN** dependency sources MUST include `workspace_store`, `continuation_registry`, and `worker_ownership_store`
- **AND** worker ownership durability MUST be reported separately from workspace persistence posture
- **AND** worker ownership availability MUST NOT imply durable workspace readiness
