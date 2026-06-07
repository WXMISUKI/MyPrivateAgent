# document-rag-local-readiness Specification

## ADDED Requirements

### Requirement: Local document RAG readiness check evaluates OCR provider availability
MyPrivateAgent SHALL provide a local readiness check that reports whether the configured OCR provider is reachable before running document upload-to-use trials.

#### Scenario: OCR provider is reachable
- **WHEN** the readiness check calls the configured OCR provider health endpoint
- **AND** the provider returns a successful response
- **THEN** the OCR provider check status is `ready`
- **AND** the output records endpoint, timeout, and OCR profile

#### Scenario: OCR provider is unreachable
- **WHEN** the OCR provider cannot be reached or returns an invalid health response
- **THEN** the readiness decision is `blocked`
- **AND** the output records `reason_code=ocr_provider_unreachable`

### Requirement: Local document RAG readiness check evaluates knowledge provider availability
The readiness check SHALL report whether the configured unifiedKnowledgeRAG provider can be used for explicit local RAG trials.

#### Scenario: Knowledge provider is reachable and source is visible
- **WHEN** provider health succeeds
- **AND** the source catalog includes the configured source id
- **THEN** the knowledge provider check status is `ready`

#### Scenario: Knowledge provider is reachable but source is missing
- **WHEN** provider health succeeds
- **AND** the source catalog does not include the configured source id
- **THEN** the readiness decision is `review`
- **AND** the output records `reason_code=source_not_visible`

#### Scenario: Knowledge provider is unreachable
- **WHEN** provider health or source catalog cannot be reached
- **THEN** the readiness decision is `blocked`
- **AND** the output records `reason_code=knowledge_provider_unreachable`

### Requirement: Local document RAG readiness check evaluates provider ingestion command prerequisites
The readiness check SHALL verify the local provider command prerequisites without running ingestion.

#### Scenario: Provider command prerequisites are present
- **WHEN** the configured provider repo exists
- **AND** the parser artifact ingestion script exists
- **AND** the configured provider Python command can be invoked for a low-cost version check
- **THEN** the provider command check status is `ready`

#### Scenario: Provider command prerequisites are missing
- **WHEN** the provider repo, parser artifact ingestion script, or provider Python command is missing or unusable
- **THEN** the readiness decision is `blocked`
- **AND** the output records the blocking prerequisite

### Requirement: Local document RAG readiness check reports CPU/GPU and timeout posture
The readiness check SHALL expose operator-facing OCR profile and timeout guidance.

#### Scenario: GPU profile is configured
- **WHEN** the checker is run with OCR profile `gpu`
- **THEN** the output records GPU as the intended OCR profile
- **AND** it recommends using the GPU OCR service endpoint for large PDF trials

#### Scenario: CPU profile or low timeout is configured
- **WHEN** the checker is run with OCR profile `cpu`
- **OR** the configured OCR timeout is below the recommended large-PDF threshold
- **THEN** the readiness decision is at most `review`
- **AND** the output recommends increasing timeout or using GPU for large PDFs

### Requirement: Local document RAG readiness check preserves runtime boundaries
The readiness check SHALL remain side-effect-free local operator tooling.

#### Scenario: Readiness check runs
- **WHEN** the local readiness exporter runs
- **THEN** it does not upload, parse, or ingest documents
- **AND** it does not start external services
- **AND** it does not enable default `/api/chat` retrieval injection
- **AND** it does not create source-to-agent binding
- **AND** it does not write memory, audit, approval, or governance records
- **AND** it does not execute GraphRAG

### Requirement: Local document RAG readiness check is refreshable from CLI
The system SHALL provide a CLI exporter for refreshing local readiness artifacts.

#### Scenario: CLI exports reports
- **WHEN** the user runs the document RAG local readiness exporter
- **THEN** JSON and Markdown reports are written under `docs/integration/document-rag-local-readiness/`
- **AND** the command exits non-zero only when the readiness decision is `blocked`
