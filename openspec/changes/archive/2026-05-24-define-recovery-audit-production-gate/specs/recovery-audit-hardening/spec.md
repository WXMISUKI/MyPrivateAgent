## MODIFIED Requirements

### Requirement: Recovery audit MUST provide a governance-grade summary

The runtime MUST provide a compact audit summary for recovery operations that can be consumed by Runtime Surface, Governance Timeline, and quality gates. The first implementation MAY provide a read-side summary without writing governance trace records.

#### Scenario: Audit summary is available

- **WHEN** a run has recovery operation history
- **THEN** the Runtime Surface recovery read model MUST expose a recovery audit summary
- **AND** the summary MUST include latest status, latest entrypoint, latest reason, operation counts, retry counts, ownership status, and terminal status
- **AND** the summary MUST be derived from compact recovery operation evidence rather than executable internals
- **AND** production audit readiness MAY use this summary as governance evidence, not as execution authorization

### Requirement: Recovery audit MUST remain separated from execution authorization

Recovery audit MUST not grant execution authority.

#### Scenario: Audit production gate is ready

- **WHEN** recovery audit production readiness reports ready
- **THEN** it proves operation history and audit summary evidence only
- **AND** it MUST NOT authorize recovery execution or worker ownership validation
