# document-rag-upload-to-use-loop Specification

## ADDED Requirements

### Requirement: Local document RAG upload-to-use loop can parse a document
MyPrivateAgent SHALL provide a local trial loop that starts from a local document file and reuses the existing document ingestion workflow.

#### Scenario: Document ingestion succeeds
- **WHEN** the loop is run with an existing document file, parse mode, source id, and title
- **AND** the existing document ingestion workflow returns a succeeded artifact
- **THEN** the loop records the ingestion id, artifact id, parse mode, provider, warnings, and artifact summary

#### Scenario: Document ingestion fails
- **WHEN** the document ingestion workflow fails or remains non-terminal
- **THEN** the loop decision is `blocked`
- **AND** it records the ingestion error or non-terminal status
- **AND** it does not run provider-side RAG ingestion

### Requirement: Local document artifact can be converted into a RAG handoff artifact
The loop SHALL convert a succeeded OCR or layout artifact into a normalized parser artifact handoff for unifiedKnowledgeRAG.

#### Scenario: OCR artifact becomes parser artifact
- **WHEN** the document artifact payload contains OCR blocks or text
- **THEN** the loop writes a normalized parser artifact JSON file with source id, title, original file metadata, parser metadata, text blocks, and citation anchors

#### Scenario: Layout artifact becomes parser artifact
- **WHEN** the document artifact payload contains markdown or page text
- **THEN** the loop writes a normalized parser artifact JSON file with at least one citation-anchored text block

#### Scenario: Artifact has no usable text
- **WHEN** the document artifact payload has no usable text or markdown
- **THEN** the loop decision is `blocked`
- **AND** it records `reason_code=document_artifact_has_no_rag_text`

### Requirement: Local document RAG upload-to-use loop can invoke provider-side ingestion
The loop SHALL optionally invoke the local unifiedKnowledgeRAG parser-artifact ingestion command for a generated parser artifact.

#### Scenario: Provider ingestion command succeeds
- **WHEN** the generated parser artifact exists
- **AND** the configured provider repo command exits successfully
- **THEN** the loop records provider ingestion status as `ready`
- **AND** it continues to provider source usability verification

#### Scenario: Provider ingestion command fails
- **WHEN** the configured provider repo command exits non-zero or cannot be run
- **THEN** the loop decision is `blocked`
- **AND** it records `reason_code=provider_ingestion_command_failed`

#### Scenario: Provider ingestion command is skipped
- **WHEN** the loop is run in handoff-only mode
- **THEN** the loop decision is `review`
- **AND** it writes the parser artifact path and recommends running provider ingestion before user-facing RAG usage

### Requirement: Local document RAG upload-to-use loop verifies provider usability
The loop SHALL verify the configured source through the existing local knowledge provider corpus trial after provider-side ingestion.

#### Scenario: Provider usability passes
- **WHEN** provider-side ingestion is ready
- **AND** the local knowledge provider corpus trial returns `go`
- **THEN** the loop decision is `go`
- **AND** it records source id, provider base URL, artifact paths, trial summary, and recommended next action

#### Scenario: Provider usability needs review
- **WHEN** provider-side ingestion is ready
- **AND** the local knowledge provider corpus trial returns `review`
- **THEN** the loop decision is `review`
- **AND** it records the trial reason code

#### Scenario: Provider usability is blocked
- **WHEN** provider-side ingestion is ready
- **AND** the local knowledge provider corpus trial returns `blocked`
- **THEN** the loop decision is `blocked`
- **AND** it records the trial reason code

### Requirement: Local document RAG upload-to-use loop preserves runtime boundaries
The loop SHALL remain explicit local tooling and SHALL NOT alter default runtime behavior.

#### Scenario: Loop runs
- **WHEN** the loop runs
- **THEN** it does not enable default `/api/chat` retrieval injection
- **AND** it does not create source-to-agent binding
- **AND** it does not mutate domain-agent manifests
- **AND** it does not write memory, audit, approval, or governance records
- **AND** it does not start PaddleOCR or unifiedKnowledgeRAG services
- **AND** it does not promote retrieval backends
- **AND** it does not execute GraphRAG

### Requirement: Local document RAG upload-to-use loop is refreshable from CLI
The system SHALL provide a CLI exporter for refreshing local document RAG upload-to-use loop artifacts.

#### Scenario: CLI exports reports
- **WHEN** the user runs the document RAG upload-to-use loop exporter
- **THEN** JSON and Markdown reports are written under `docs/integration/document-rag-upload-to-use-loop/`
- **AND** the command exits non-zero only when the loop decision is `blocked`
