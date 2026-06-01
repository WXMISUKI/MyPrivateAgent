# unified-capability-runtime Specification Delta

## ADDED Requirements

### Requirement: External document VLM capability registration

The backend SHALL support registering `document.vlm.parse` as an HTTP capability when an external VLM provider is configured.

#### Scenario: VLM capability appears in registry
- **GIVEN** VLM provider integration is enabled
- **WHEN** a client requests `GET /api/capabilities`
- **THEN** the registry includes `document.vlm.parse`
- **AND** the capability uses `kind=vlm` and `transport=http`.

### Requirement: Document VLM parse normalization

The backend SHALL map VLM parse requests to the external provider and normalize responses into a provider-neutral semantic envelope.

#### Scenario: VLM invocation returns semantic understanding and evidence
- **WHEN** a client invokes `POST /api/capabilities/document.vlm.parse/invoke`
- **THEN** the response includes `summary`, `sections`, `entities`, `answers`, `evidence`, `warnings`, and `raw`.
