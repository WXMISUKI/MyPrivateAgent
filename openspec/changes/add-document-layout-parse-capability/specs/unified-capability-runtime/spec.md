# unified-capability-runtime Specification Delta

## ADDED Requirements

### Requirement: External document layout capability registration

The backend SHALL support registering `document.layout.parse` as an HTTP capability when an external layout provider is configured.

#### Scenario: Layout capability is discoverable
- **GIVEN** layout provider integration is enabled
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the registry includes `document.layout.parse`
- **AND** the capability uses `kind=layout` and `transport=http`.

### Requirement: Document layout parse normalization

The backend SHALL map layout parse requests to the external provider and normalize responses into a provider-neutral envelope.

#### Scenario: Layout invocation returns markdown and table evidence
- **WHEN** a client invokes `POST /api/capabilities/document.layout.parse/invoke`
- **THEN** the response includes `markdown`, `elements`, `tables`, `pages`, `artifacts`, `warnings`, and `raw`.
