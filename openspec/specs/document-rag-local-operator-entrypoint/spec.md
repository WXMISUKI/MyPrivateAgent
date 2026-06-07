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
MyPrivateAgent SHALL expose a backend API for running a local document RAG upload-to-use trial from a local document path.

#### Scenario: Readiness is ready
- **WHEN** the local trial API receives a document path and readiness is `go`
- **THEN** the API runs the existing document RAG upload-to-use loop
- **AND** returns combined readiness and trial reports
- **AND** records the final trial decision and report paths

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

### Requirement: Settings diagnostics exposes a minimal local operator entrypoint
The Settings diagnostics panel SHALL provide a compact local document RAG operator card.

#### Scenario: Operator runs readiness from Settings
- **WHEN** the operator clicks the readiness action
- **THEN** the frontend calls the readiness API
- **AND** displays decision, reason, and report path

#### Scenario: Operator runs local trial from Settings
- **WHEN** the operator enters a local document path and clicks the trial action
- **THEN** the frontend calls the local trial API
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
