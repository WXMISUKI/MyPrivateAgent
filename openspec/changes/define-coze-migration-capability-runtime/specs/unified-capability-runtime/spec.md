## ADDED Requirements

### Requirement: Coze migration workflows may be exposed as provider-neutral capabilities
The capability runtime SHALL be able to expose ready Coze migration workflows as provider-neutral capabilities using stable capability ids.

#### Scenario: Ready workflow appears as capability
- **GIVEN** a Coze workflow `customer_intake` is active and ready
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the registry may include `coze.workflow.customer_intake`
- **AND** the capability contract includes `kind = workflow`
- **AND** the capability contract includes workflow identity, input schema, output schema, status, and governance metadata

#### Scenario: Draft workflow is not exposed as default callable capability
- **GIVEN** a Coze workflow status is `draft`
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the capability runtime MUST NOT expose it as a default callable production capability
- **AND** development visibility may remain available through the Coze migration registry

### Requirement: Coze workflow capability invocation must use standard envelopes
The capability runtime SHALL invoke Coze workflow capabilities through the same provider-neutral invoke envelope used by other capabilities.

#### Scenario: Invoke ready Coze workflow capability
- **WHEN** a client posts to `POST /api/capabilities/coze.workflow.customer_intake/invoke`
- **THEN** the backend validates the request against the workflow input schema
- **AND** returns a provider-neutral response envelope
- **AND** includes workflow run identity and structured result or error

#### Scenario: Blocked Coze workflow capability returns structured error
- **GIVEN** a workflow has unresolved readiness blockers
- **WHEN** a client invokes its capability id
- **THEN** the backend returns `ok = false`
- **AND** the error code is stable and machine-readable
