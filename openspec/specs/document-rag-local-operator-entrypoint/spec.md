# document-rag-local-operator-entrypoint Specification

## Purpose
Defines the minimal MyPrivateAgent local operator entrypoint for real document RAG trials. The entrypoint wraps local readiness and upload-to-use tooling behind backend APIs and a compact Settings diagnostics control so local users can operate the current RAG flow without manually stitching scripts together.
## Requirements
### Requirement: Local operator can request document RAG readiness through API
MyPrivateAgent SHALL expose a backend API for refreshing local document RAG readiness.

#### Scenario: Readiness request succeeds
- **WHEN** a caller posts local readiness options
- **THEN** the API returns `ok=true`
- **AND** it includes readiness `decision`, `reason_code`, checks, summary, and report paths

#### Scenario: Readiness is blocked
- **WHEN** local readiness detects a blocked dependency
- **THEN** the API still returns the readiness report
- **AND** `ok=false`
- **AND** the report identifies the blocking reason

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

### Requirement: Local operator entrypoint preserves runtime boundaries
The local operator entrypoint SHALL remain explicit local tooling.

#### Scenario: Entrypoint runs
- **WHEN** readiness or trial API runs
- **THEN** it does not enable default `/api/chat` retrieval injection
- **AND** it does not create source-to-agent binding
- **AND** it does not mutate domain-agent manifests
- **AND** it does not write memory, audit, approval, or governance records
- **AND** it does not start PaddleOCR or unifiedKnowledgeRAG services
- **AND** it does not execute GraphRAG

### Requirement: Local operator can run a RAG question trial through API
MyPrivateAgent SHALL expose a backend API for asking one explicit business question against an already-ingested local RAG `source_id`.

#### Scenario: Question trial returns grounded answer
- **WHEN** the question trial API receives `source_id`, `question`, `provider_base_url`, and `top_k`
- **AND** the provider returns retrieved documents and an `answered` response
- **THEN** the API returns `ok=true`
- **AND** it includes `decision=go`, `answer_status=answered`, answer text, citations, evidence status, and report paths
- **AND** all returned answer citations are within the retrieved citation allowlist

#### Scenario: Question trial returns insufficient evidence
- **WHEN** the question trial API receives a question that the selected source cannot support
- **AND** the provider returns `answer_status=insufficient_evidence`
- **THEN** the API returns `ok=true`
- **AND** it includes `decision=go`
- **AND** it exposes the insufficient-evidence status to the operator

#### Scenario: Question trial detects unsupported citations
- **WHEN** the provider answer contains citations outside the retrieved citation allowlist
- **THEN** the API returns a review decision
- **AND** it lists the invalid citations
- **AND** it does not promote the result into chat, memory, or agent binding

#### Scenario: Question trial provider call fails
- **WHEN** the provider retrieve or answer request fails
- **THEN** the API returns `ok=false`
- **AND** it includes a blocked decision and stable reason code
- **AND** it keeps the failure local to the diagnostics entrypoint

### Requirement: Settings diagnostics exposes local RAG question trial
The Settings diagnostics panel SHALL let a local operator ask one explicit RAG question after a source has been ingested.

#### Scenario: Operator asks a local RAG question
- **WHEN** the operator enters a question and clicks the question trial action
- **THEN** the frontend sends `source_id`, `question`, `provider_base_url`, and `top_k` to the backend
- **AND** it displays decision, reason, answer status, answer text, citations, evidence status, and report path

#### Scenario: Operator sees insufficient evidence
- **WHEN** the backend returns `answer_status=insufficient_evidence`
- **THEN** the frontend displays that status explicitly
- **AND** it keeps the result inside the local diagnostics card

### Requirement: Local RAG question trial preserves runtime boundaries
The local RAG question trial SHALL remain an explicit local diagnostics action.

#### Scenario: Question trial runs
- **WHEN** the backend question trial runs
- **THEN** it does not enable default `/api/chat` retrieval injection
- **AND** it does not create source-to-agent binding
- **AND** it does not mutate domain-agent manifests
- **AND** it does not write memory, audit, approval, or governance records
- **AND** it does not start external services
- **AND** it does not execute GraphRAG

