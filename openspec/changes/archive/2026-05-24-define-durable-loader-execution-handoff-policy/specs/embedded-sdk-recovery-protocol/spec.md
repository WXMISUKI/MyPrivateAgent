## MODIFIED Requirements

### Requirement: Recovery protocol MUST require production gate for default cross-process recovery

The recovery protocol MUST keep run-specific recovery probes separate from production default recovery enablement.

#### Scenario: Probe is recoverable and handoff policy is defined

- **WHEN** a run-specific probe reports a registry-backed recoverable candidate
- **AND** loader execution handoff policy is ready
- **THEN** recovery remains explicit or conditional
- **AND** default background or automatic cross-process recovery MUST NOT execute
- **AND** missing executor binding MUST remain a fail-closed handoff decision
