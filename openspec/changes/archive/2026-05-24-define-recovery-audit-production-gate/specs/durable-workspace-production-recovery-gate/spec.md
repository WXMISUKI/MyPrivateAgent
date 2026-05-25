## MODIFIED Requirements

### Requirement: Durable workspace production recovery gate MUST be machine-readable

The runtime MUST expose a production recovery gate before cross-process recovery can become default runtime behavior.

#### Scenario: Recovery audit is ready but ownership or rollout is missing

- **WHEN** recovery audit operation history readiness is implemented and covered by runtime quality gates
- **THEN** the production recovery gate marks `recovery_audit_operation_history` as ready
- **AND** the gate still remains blocked when worker ownership, rollout, registry policy, or checkpoint/cursor gate sections are missing
