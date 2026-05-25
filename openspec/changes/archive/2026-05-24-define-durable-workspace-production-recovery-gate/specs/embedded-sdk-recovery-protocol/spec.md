## ADDED Requirements

### Requirement: Recovery protocol MUST require production gate for default cross-process recovery

The recovery protocol MUST keep run-specific recovery probes separate from production default recovery enablement.

#### Scenario: Probe is recoverable but production gate is blocked

- **WHEN** a run-specific probe reports a registry-backed recoverable candidate
- **AND** the production recovery gate is blocked
- **THEN** recovery remains explicit or conditional
- **AND** default background or automatic cross-process recovery MUST NOT execute

### Requirement: Recovery protocol MUST define descriptor lifecycle evidence

The recovery protocol MUST expose descriptor lifecycle evidence before cross-process recovery can be production-default.

#### Scenario: Descriptor lifecycle is governed

- **WHEN** a descriptor participates in production recovery
- **THEN** lifecycle evidence MUST distinguish created, bound, ready, stale, resolved, and unsafe states
- **AND** unsafe callable-like payloads MUST remain fail-closed
