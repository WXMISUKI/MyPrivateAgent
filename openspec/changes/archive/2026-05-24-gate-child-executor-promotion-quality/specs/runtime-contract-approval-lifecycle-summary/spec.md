## MODIFIED Requirements

### Requirement: Runtime contract summary MUST expose child executor promotion gate coverage

The Quality Gate runtime contract summary MUST expose child executor promotion gate coverage as a first-class machine-readable coverage object.

#### Scenario: Child executor promotion gate check is healthy

- **WHEN** runtime contract smoke emits `child_executor_promotion_gate` with `ok = true`
- **THEN** the runtime contract summary includes `child_executor_promotion_gate_coverage.gate_smoke = true`
- **AND** it preserves the gate status, allow/deny result, failure reason, blocker count, and recommended next step

#### Scenario: Child executor promotion gate check is missing

- **WHEN** a legacy report lacks `child_executor_promotion_gate`
- **THEN** the runtime contract summary includes `child_executor_promotion_gate_coverage.gate_smoke = false`
- **AND** it emits stable empty default evidence

