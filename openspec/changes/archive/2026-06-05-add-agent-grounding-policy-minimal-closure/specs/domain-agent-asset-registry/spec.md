## ADDED Requirements

### Requirement: Domain agent manifests expose grounding policy readiness
The domain agent registry SHALL preserve normalized grounding policy and grounding readiness details from domain agent manifests.

#### Scenario: Agent has grounding policy
- **WHEN** a domain agent manifest declares `grounding_policy`
- **THEN** the normalized agent contract includes `grounding_policy`
- **AND** the normalized agent contract includes `grounding_policy_status`

#### Scenario: Grounding policy registry is assembled
- **WHEN** the domain agent registry contract is built
- **THEN** it includes `grounding_policy_registry`
- **AND** the registry remains `visibility_only`
