# runtime-harness-reference-alignment Specification

## Purpose
Align runtime harness contracts with the platform runtime model used by Embedded SDK and governance consumers.
## Requirements
### Requirement: Runtime Harness Development Must Distinguish Conceptual References From Control-Plane References

The project MUST treat teaching-style harness references and production-style control-plane references as different inputs, with different intended use.

#### Scenario: Choosing a reference for runtime recovery semantics

- **GIVEN** the team is defining runtime recovery, runtime task, or teammate semantics
- **WHEN** they choose an external reference source
- **THEN** `learn-claude-code` SHOULD be treated as the primary conceptual reference
- **AND** `claude-code` SHOULD be treated as a secondary control-plane mechanism reference

### Requirement: External References Must Not Override Project Domain Semantics Directly

The project MUST preserve its own Runtime Core / Governance / Approval / Read Model language when adopting external patterns.

#### Scenario: Adopting a teammate backend or recovery mechanism

- **GIVEN** an external project contains a useful backend, runner, or reconnection pattern
- **WHEN** the pattern is adopted
- **THEN** it MUST be mapped into local Runtime Core and governance contracts
- **AND** it MUST NOT be copied wholesale with its original product-specific naming and coupling

### Requirement: Child Executor And Worker Runtime Planning Must Cite Approved Reference Slices

Future child executor or worker runtime changes MUST cite specific approved reference slices instead of broad “inspired by X repo” claims.

#### Scenario: Planning II-1.6 child executor preflight

- **GIVEN** the team starts a child executor preflight change
- **WHEN** the spec is written
- **THEN** it MUST identify which reference slices are being borrowed
- **AND** it MUST state what is intentionally not being copied
