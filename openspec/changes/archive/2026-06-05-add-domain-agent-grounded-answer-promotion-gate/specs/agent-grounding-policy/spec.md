# agent-grounding-policy Specification

## MODIFIED Requirements

### Requirement: Grounding policy readiness is visible before enforcement
The system SHALL expose grounding policy readiness as governance-visible data before it changes default chat behavior.

#### Scenario: Runtime Surface reads grounding policy
- **WHEN** the Runtime Surface profile is assembled
- **THEN** domain-agent grounding policy data is visible to governance consumers
- **AND** the output indicates that default `/api/chat` retrieval injection is not enabled by this change

#### Scenario: Provider readiness is unavailable
- **WHEN** a policy references knowledge behavior and the external provider is absent or degraded
- **THEN** grounding readiness reports a machine-readable `unknown` or `degraded` state
- **AND** application startup and default chat behavior remain healthy

#### Scenario: Promotion gate consumes grounding decision
- **WHEN** a grounded-answer promotion gate evaluates a domain agent
- **THEN** it consumes the side-effect-free grounding policy decision as readiness evidence
- **AND** it does not enable retrieval, prompt injection, memory injection, or answer generation by itself
