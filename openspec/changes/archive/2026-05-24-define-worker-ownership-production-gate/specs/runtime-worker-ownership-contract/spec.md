## ADDED Requirements

### Requirement: Runtime worker ownership contract MUST include production gate evidence

The runtime worker ownership contract MUST expose production gate evidence alongside adapter kind, durable status, enforcement mode, operations, fail-closed reasons, and operational readiness.

#### Scenario: Contract exposes blocked production gate

- **WHEN** the default runtime worker ownership contract is inspected
- **THEN** it includes `production_gate`
- **AND** the gate reports whether production default ownership is enabled
- **AND** missing production readiness sections are machine-readable

### Requirement: Production gate MUST fail closed for default recovery ownership

The runtime MUST NOT infer default recovery ownership authorization from durable adapter presence alone.

#### Scenario: Durable adapter exists but gate is blocked

- **WHEN** the worker ownership adapter is durable
- **AND** production gate evidence is blocked
- **THEN** SDK recovery ownership remains descriptor-evidence driven
- **AND** recovery entry auto-claim remains explicitly configured rather than default-enabled
