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

### Requirement: Layout parse error code contract

The backend SHALL return stable error codes for layout parse input and provider failures.

#### Scenario: Unsupported layout media type is rejected
- **WHEN** `media_type` is not in `{application/pdf, image/png, image/jpeg}`
- **THEN** response `error.code` MUST be `LAYOUT_UNSUPPORTED_MEDIA_TYPE`.

#### Scenario: Invalid layout output format is rejected
- **WHEN** `output_format` is not `markdown` or `json`
- **THEN** response `error.code` MUST be `LAYOUT_INVALID_OUTPUT_FORMAT`.

#### Scenario: Missing layout input is rejected
- **WHEN** `file_base64` is missing or empty
- **THEN** response `error.code` MUST be `LAYOUT_INVALID_INPUT`.

#### Scenario: Layout provider failures are mapped
- **WHEN** provider returns non-zero/non-null `errorCode` or transport errors
- **THEN** response `error.code` SHOULD be `PADDLE_LAYOUT_PROVIDER_ERROR` for mapped provider failures.

#### Scenario: Unreachable layout provider is reported
- **WHEN** HTTP transport is unreachable
- **THEN** response `error.code` SHOULD be `CAPABILITY_PROVIDER_UNREACHABLE`.

### Requirement: Layout parse status visibility

The contract SHALL expose health and heartbeat states as documented in `unified-capability-runtime`:

#### Scenario: Layout provider status is visible
- **WHEN** a client inspects the layout capability
- **THEN** the status MUST be one of `ready`, `disabled`, `unconfigured`, `missing_dependency`, or `unreachable`.
