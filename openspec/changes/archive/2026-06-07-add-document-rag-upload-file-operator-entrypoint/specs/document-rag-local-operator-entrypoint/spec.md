# document-rag-local-operator-entrypoint Specification Delta

## MODIFIED Requirements

### Requirement: Local operator can run document RAG trial through API
MyPrivateAgent SHALL expose a backend API for running a local document RAG upload-to-use trial from either a local document path or an uploaded document payload.

#### Scenario: Readiness is ready for path input
- **WHEN** the local trial API receives a document path and readiness is `go`
- **THEN** the API runs the existing document RAG upload-to-use loop
- **AND** returns combined readiness and trial reports
- **AND** records the final trial decision and report paths

#### Scenario: Readiness is ready for uploaded file input
- **WHEN** the local trial API receives `file_base64`, `filename`, and `media_type`
- **AND** readiness is `go`
- **THEN** the API materializes the upload into a controlled local operator upload directory
- **AND** runs the existing document RAG upload-to-use loop with the materialized document path
- **AND** returns combined readiness and trial reports
- **AND** records upload materialization metadata in the result summary

#### Scenario: Readiness is blocked
- **WHEN** local readiness returns `blocked`
- **THEN** the API does not run document ingestion or provider ingestion
- **AND** it returns `ok=false`
- **AND** it records `upload_to_use_status=not_run`

#### Scenario: Readiness needs review
- **WHEN** local readiness returns `review`
- **AND** `allow_review_readiness=false`
- **THEN** the API does not run document ingestion or provider ingestion
- **AND** it returns a review decision with `upload_to_use_status=not_run`

#### Scenario: Trial input is missing
- **WHEN** the local trial API receives neither `document_path` nor `file_base64`
- **THEN** it returns an invalid input error
- **AND** it does not run readiness, document ingestion, or provider ingestion

### Requirement: Settings diagnostics exposes a minimal local operator entrypoint
The Settings diagnostics panel SHALL provide a compact local document RAG operator card with file upload as the primary local input and path input as an advanced fallback.

#### Scenario: Operator runs readiness from Settings
- **WHEN** the operator clicks the readiness action
- **THEN** the frontend calls the readiness API
- **AND** displays decision, reason, and report path

#### Scenario: Operator runs local trial with uploaded file from Settings
- **WHEN** the operator selects a local document file and clicks the trial action
- **THEN** the frontend sends `file_base64`, `filename`, and `media_type` to the local trial API
- **AND** displays readiness and trial decisions, source id, report paths, selected filename, and materialized upload path when returned

#### Scenario: Operator runs local trial with path fallback from Settings
- **WHEN** the operator does not select a file
- **AND** enters a local document path
- **AND** clicks the trial action
- **THEN** the frontend sends `document_path` to the local trial API
- **AND** displays readiness and trial decisions, source id, and report paths
