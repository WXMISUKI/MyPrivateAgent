# unified-capability-runtime Specification Delta

## ADDED Requirements

### Requirement: Document artifact persistence contract

The backend SHALL expose a local document artifact contract for compact OCR/Layout/VLM capability outputs.

#### Scenario: Persist compact document artifact
- **WHEN** a client posts `POST /api/document-artifacts`
- **AND** the request includes `capability_id`, `provider`, and `result`
- **THEN** the backend persists compact artifact metadata and payload
- **AND** returns `ok=true`
- **AND** returns `artifact.artifact_id`
- **AND** returns `artifact.content_hash`.

#### Scenario: Raw provider payload is excluded by default
- **WHEN** the result contains a `raw` field
- **AND** `include_raw` is not true
- **THEN** the persisted payload MUST NOT include `raw`.

#### Scenario: Read document artifact
- **WHEN** a client requests `GET /api/document-artifacts/{artifact_id}`
- **THEN** the backend returns metadata and compact payload for that artifact.

#### Scenario: List document artifacts
- **WHEN** a client requests `GET /api/document-artifacts`
- **THEN** the backend returns a list of artifact metadata records sorted newest first.

#### Scenario: Unknown artifact id
- **WHEN** a client requests an unknown artifact id
- **THEN** the backend returns HTTP 404
- **AND** returns error code `DOCUMENT_ARTIFACT_NOT_FOUND`.

### Requirement: Diagnostics artifact action

The frontend diagnostics panel SHALL allow users to persist successful document capability results on demand.

#### Scenario: Persist action appears for successful document result
- **WHEN** OCR/Layout/VLM diagnostics result is successful
- **THEN** the panel exposes a persist artifact action.

#### Scenario: Persist action returns artifact id
- **WHEN** a user persists a successful result
- **THEN** the panel calls `POST /api/document-artifacts`
- **AND** displays the returned `artifact_id`.
