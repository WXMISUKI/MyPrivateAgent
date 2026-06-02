# unified-capability-runtime Specification Delta

## ADDED Requirements

### Requirement: Document ingestion workflow contract

The backend SHALL expose a document ingestion workflow that orchestrates existing document capabilities and persists successful outputs as artifacts.

#### Scenario: Submit OCR ingestion
- **WHEN** a client posts `POST /api/document-ingestions`
- **AND** the request includes `parse_mode=ocr`, `file_base64`, `media_type`, and `filename`
- **THEN** the backend invokes `document.ocr.extract`
- **AND** persists a compact document artifact on success
- **AND** returns `ok=true`
- **AND** returns `ingestion.ingest_id`
- **AND** returns `ingestion.artifact_id`.

#### Scenario: Submit Layout ingestion
- **WHEN** a client posts `POST /api/document-ingestions`
- **AND** the request includes `parse_mode=layout`, `file_base64`, `media_type`, and `filename`
- **THEN** the backend invokes `document.layout.parse`
- **AND** forwards layout options such as `output_format`, `include_tables`, `include_layout`, and `max_pages`
- **AND** persists a compact document artifact on success.

#### Scenario: Submit async VLM ingestion
- **WHEN** a client posts `POST /api/document-ingestions`
- **AND** the request includes `parse_mode=vlm_async`, `file_base64`, `media_type`, and `filename`
- **THEN** the backend invokes `document.vlm.parse.async`
- **AND** records provider job metadata when the provider returns a non-terminal job
- **AND** persists a compact document artifact when a terminal successful result is available.

#### Scenario: Read ingestion status
- **WHEN** a client requests `GET /api/document-ingestions/{ingest_id}`
- **THEN** the backend returns persisted ingestion metadata including status, parse mode, provider, warnings, error, and artifact reference.

#### Scenario: Read ingestion result
- **WHEN** a client requests `GET /api/document-ingestions/{ingest_id}/result`
- **AND** the ingestion has an artifact reference
- **THEN** the backend returns ingestion metadata, artifact metadata, and compact artifact payload.

#### Scenario: Unknown ingestion id
- **WHEN** a client requests an unknown ingestion id
- **THEN** the backend returns HTTP 404
- **AND** returns error code `DOCUMENT_INGEST_NOT_FOUND`.

#### Scenario: Invalid ingestion input
- **WHEN** a client submits an unsupported parse mode or missing required document payload
- **THEN** the backend returns HTTP 400
- **AND** returns error code `DOCUMENT_INGEST_INVALID_INPUT`.

### Requirement: Document ingestion diagnostics action

The frontend diagnostics panel SHALL expose a minimal document ingestion test area for local provider orchestration.

#### Scenario: Submit ingestion from diagnostics
- **WHEN** a user selects a file and parse mode
- **THEN** the diagnostics panel can call `POST /api/document-ingestions`
- **AND** displays the returned `ingest_id`, `status`, and `artifact_id`.

#### Scenario: Display structured ingestion errors
- **WHEN** ingestion submission fails
- **THEN** the diagnostics panel displays the backend error code and message.
