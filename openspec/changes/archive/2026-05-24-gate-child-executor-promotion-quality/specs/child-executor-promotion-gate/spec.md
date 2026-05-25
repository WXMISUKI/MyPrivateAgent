## MODIFIED Requirements

### Requirement: Child Executor Promotion Gate Must Be Quality-Gated

The child executor promotion gate MUST be covered by runtime contract smoke and quality gate summary evidence so consumers can detect missing or malformed promotion gate contracts.

#### Scenario: Promotion gate smoke is healthy

- **WHEN** runtime contract smoke evaluates the current runtime profile
- **THEN** it MUST emit a `child_executor_promotion_gate` contract check
- **AND** the check MUST include gate status, allow/deny result, failure reason, blocker count, and recommended next step
- **AND** the check MUST report healthy only when the gate evidence is machine-readable

#### Scenario: Promotion gate remains relationship-only

- **WHEN** the default gate is blocked
- **THEN** the smoke evidence MUST preserve `allowed = false`
- **AND** it MUST NOT imply that a real child executor has started

