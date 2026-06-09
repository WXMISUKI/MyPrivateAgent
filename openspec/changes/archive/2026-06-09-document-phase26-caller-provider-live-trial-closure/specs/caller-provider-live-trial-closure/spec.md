## ADDED Requirements

### Requirement: Phase 26 prioritizes caller-provider live trial closure
MyPrivateAgent SHALL treat the next knowledge-provider phase as a caller-provider live trial closure, not as a new provider feature expansion phase.

#### Scenario: Team plans the next phase
- **WHEN** the team chooses the next knowledge-provider improvement task
- **THEN** the default priority is a real caller-side live trial closure
- **AND** provider-side retrieval strategy enhancement stays out of the default backlog unless a later trigger proves it is needed

### Requirement: Live trial closure uses an explicit minimal caller entrypoint
MyPrivateAgent SHALL document and prefer one minimal explicit caller entrypoint for Phase 26 trial execution.

#### Scenario: Team prepares the first Phase 26 trial
- **WHEN** the team needs a real caller-side trial artifact
- **THEN** the runbook identifies a minimal recommended entrypoint, command, output path, and success criteria
- **AND** the entrypoint remains read-only and outside default `/api/chat` grounding

### Requirement: RAG techniques remain candidate strategies only
MyPrivateAgent SHALL keep external RAG technique experience as candidate strategy input rather than automatic implementation backlog.

#### Scenario: Team reviews external RAG technique references
- **WHEN** the team consults `RAG_Techniques` or similar experience notes
- **THEN** the notes are interpreted as optional future strategies
- **AND** they do not become mandatory tasks until real caller evidence justifies them

### Requirement: Provider reopen is trigger-based
MyPrivateAgent SHALL reopen provider enhancement work only when a limited set of caller- or provider-owned triggers is met.

#### Scenario: Trial outcome exposes no concrete provider gap
- **WHEN** a Phase 26 live trial does not show a concrete provider-owned gap
- **THEN** provider enhancement work remains closed
- **AND** the team does not add rerank, hybrid retrieval, query rewrite, or GraphRAG execution by default

#### Scenario: Trial outcome exposes a provider-owned gap
- **WHEN** a real caller-side live trial identifies a repeated or provider-owned failure class
- **THEN** the team may open a focused provider change
- **AND** the new change documents the specific trigger before implementation starts
