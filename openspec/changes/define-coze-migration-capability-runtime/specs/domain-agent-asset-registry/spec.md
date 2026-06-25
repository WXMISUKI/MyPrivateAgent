## ADDED Requirements

### Requirement: Domain agent manifests may reference Coze migration workflows
Domain agent manifests SHALL be able to reference Coze migration workflow capabilities without owning their execution implementation.

#### Scenario: Domain agent links to Coze workflow capability
- **GIVEN** a domain agent manifest declares `capabilities.coze_workflows`
- **WHEN** the domain agent registry contract is built
- **THEN** the normalized agent contract includes compact Coze workflow references
- **AND** each reference includes workflow id or capability id
- **AND** execution readiness remains delegated to the Coze migration workflow registry

#### Scenario: Domain agent cannot auto-execute workflow by reference
- **GIVEN** a domain agent references a Coze migration workflow
- **WHEN** the domain agent registry is inspected
- **THEN** the registry MUST NOT execute the workflow
- **AND** the registry MUST NOT auto-register a tool outside the unified workflow or capability runtime

### Requirement: Coze workflow references must fail closed when missing
The domain agent registry SHALL report missing Coze workflow references as readiness warnings or blockers without blocking unrelated agents.

#### Scenario: Referenced workflow does not exist
- **GIVEN** a domain agent references `customer_intake`
- **AND** no matching Coze workflow manifest exists
- **WHEN** the domain agent registry contract is built
- **THEN** the agent contract includes a missing workflow reference warning
- **AND** unrelated domain agents remain discoverable
