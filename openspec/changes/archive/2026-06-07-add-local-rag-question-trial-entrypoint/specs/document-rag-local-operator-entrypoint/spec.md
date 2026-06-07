## ADDED Requirements
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
