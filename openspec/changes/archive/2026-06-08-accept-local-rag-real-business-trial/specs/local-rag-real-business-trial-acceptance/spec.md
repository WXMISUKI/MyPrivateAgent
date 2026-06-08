## ADDED Requirements
### Requirement: Local RAG real business trial acceptance summarizes real-use readiness
MyPrivateAgent SHALL provide a local acceptance report for a real business document RAG trial.

#### Scenario: Acceptance returns go
- **GIVEN** the document upload-to-use report has `decision=go`
- **AND** all answerable question trial reports have `decision=go`, `answer_status=answered`, citations, and no invalid citations
- **AND** all negative-control question trial reports have `decision=go`, `answer_status=insufficient_evidence`, and no citations
- **WHEN** the acceptance report is exported
- **THEN** it returns `decision=go`
- **AND** it records `no_follow_up_required`

#### Scenario: Acceptance returns review for quality or evidence gaps
- **GIVEN** the upload-to-use report is not blocked
- **AND** at least one question trial result has unsafe citations, unexpected answer status, missing expected answer evidence, or negative-control evidence leakage
- **WHEN** the acceptance report is exported
- **THEN** it returns `decision=review`
- **AND** it classifies the follow-up as citation/evidence, retrieval-quality, parser/OCR, or operator-flow review

#### Scenario: Acceptance returns blocked for hard blockers
- **GIVEN** the upload-to-use report is blocked, required report files are missing, or a question trial report records provider unavailability
- **WHEN** the acceptance report is exported
- **THEN** it returns `decision=blocked`
- **AND** it records machine-readable blocker reasons

### Requirement: Local RAG real business trial acceptance is refreshable from CLI
MyPrivateAgent SHALL provide a local CLI exporter for the acceptance report.

#### Scenario: CLI exports acceptance report
- **WHEN** the operator runs the acceptance export command with upload and question report paths
- **THEN** JSON and Markdown reports are written under `docs/integration/local-rag-real-business-trial-acceptance/`
- **AND** the command exits non-zero only when the decision is `blocked`

### Requirement: Local RAG real business trial acceptance preserves lightweight boundaries
The acceptance report SHALL remain a local trial decision artifact.

#### Scenario: Acceptance runs
- **WHEN** the acceptance report is built or exported
- **THEN** it does not enable default `/api/chat` retrieval injection
- **AND** it does not create source-to-agent binding
- **AND** it does not mutate domain-agent manifests
- **AND** it does not start external services
- **AND** it does not add GraphRAG, vector backend promotion, hybrid retrieval, rerank, or parser engines
- **AND** it does not write memory, audit, approval, trace, or governance records
