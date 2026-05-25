## MODIFIED Requirements

### Requirement: SDK recovery probe MUST expose durable checkpoint and resume cursor evidence

The SDK recovery probe MUST expose compact checkpoint and resume cursor evidence for durable recovery consumers without executing recovery.

#### Scenario: Production policy consumes checkpoint and cursor evidence

- **WHEN** registry-backed checkpoint and resume cursor evidence is available
- **THEN** production registry/checkpoint policy readiness MAY use that evidence as gate input
- **AND** it MUST NOT execute recovery or authorize default cross-process recovery by itself
