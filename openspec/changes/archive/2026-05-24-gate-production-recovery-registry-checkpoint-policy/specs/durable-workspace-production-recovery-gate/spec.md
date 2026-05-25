## MODIFIED Requirements

### Requirement: Durable workspace production recovery gate MUST be machine-readable

The runtime MUST expose a production recovery gate before cross-process recovery can become default runtime behavior.

#### Scenario: Registry/checkpoint policy is ready but ownership or rollout is missing

- **WHEN** registry binding resolution policy and checkpoint/resume cursor gate policy are implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `registry_binding_resolution` and `checkpoint_resume_cursor_gate` as ready
- **AND** the gate still remains blocked when worker ownership production gate or rollout sections are missing
- **AND** default production recovery execution remains disabled
