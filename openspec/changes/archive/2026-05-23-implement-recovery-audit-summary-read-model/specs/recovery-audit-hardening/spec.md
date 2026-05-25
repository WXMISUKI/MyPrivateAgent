# recovery-audit-hardening Specification Delta

## MODIFIED Requirements

### Requirement: Recovery audit MUST provide a governance-grade summary

The runtime MUST provide a compact audit summary for recovery operations that can be consumed by Runtime Surface, Governance Timeline, and quality gates. The first implementation MAY provide a read-side summary without writing governance trace records.

#### Scenario: Audit summary is available

- **WHEN** a run has recovery operation history
- **THEN** the Runtime Surface recovery read model MUST expose a recovery audit summary
- **AND** the summary MUST include latest status, latest entrypoint, latest reason, operation counts, retry counts, ownership status, and terminal status
- **AND** the summary MUST be derived from compact recovery operation evidence rather than executable internals

#### Scenario: No operation history exists

- **WHEN** Runtime Surface has no recovery operation history for a run
- **THEN** it MUST still expose an empty recovery audit summary
- **AND** the summary MUST report `operation_count = 0`

### Requirement: Recovery audit MUST expose failure and retry distribution

Audit summary MUST make repeated failure patterns observable.

#### Scenario: Recovery has multiple failed or blocked attempts

- **WHEN** recovery operation history contains multiple blocked, failed, or retried operations
- **THEN** the audit summary MUST include counts by `operation_status`, `entrypoint`, and `recovery_reason`
- **AND** it MUST identify the latest terminal reason if one exists
- **AND** it MUST include retry status counts when retry evidence exists

### Requirement: Recovery audit MUST remain separated from execution authorization

Recovery audit MUST not grant execution authority.

#### Scenario: Audit summary reports worker ownership

- **WHEN** audit summary includes worker ownership fields
- **THEN** consumers MUST treat them as evidence only
- **AND** they MUST NOT use audit summary as the source of truth for lease validation
- **AND** the summary MUST explicitly identify that it is not an authorization source
