## ADDED Requirements

### Requirement: Control-plane positioning is visible from documentation entrypoints
MyPrivateAgent's official Agent Runtime Control Plane positioning SHALL be visible from repository entrypoint documentation.

#### Scenario: Reader checks project positioning
- **WHEN** a reader opens the current docs entrypoint
- **THEN** the documentation states that MyPrivateAgent owns runtime contracts, governance, permissions, audit, observability, provider contracts, and adapter normalization
- **AND** it states that external frameworks are adapter candidates rather than replacement implementations
- **AND** it states that external providers are data-plane services consumed through provider contracts rather than main-backend dependencies
