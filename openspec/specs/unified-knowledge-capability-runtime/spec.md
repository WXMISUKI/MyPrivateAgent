# unified-knowledge-capability-runtime Specification

## Purpose
Defines provider-neutral RAG and knowledge graph capabilities, read-only Runtime Surface knowledge registries, and the external Knowledge Provider development contract. MyPrivateAgent owns registration, health, invocation envelopes, and governance visibility while vector stores, graph databases, embedding, document parsing, and indexing remain outside the core backend.
## Requirements
### Requirement: Knowledge capabilities are provider-neutral
The system SHALL expose RAG and knowledge graph capabilities through provider-neutral capability contracts without requiring vector store, graph database, embedding, reranker, OCR, or document parsing dependencies in the core backend.

#### Scenario: Registry lists knowledge capabilities
- **WHEN** an external knowledge provider is configured
- **THEN** `GET /api/capabilities` includes `knowledge.rag.retrieve` and `knowledge.graph.query`
- **AND** each capability includes `capability_id`, `kind`, `transport`, `provider`, `status`, `input_schema`, and `output_schema`

#### Scenario: Provider is not configured
- **WHEN** no external knowledge provider is configured
- **THEN** the main application starts normally
- **AND** the knowledge capabilities are absent from the default registry

### Requirement: RAG retrieval returns citation evidence
The system SHALL require RAG retrieval responses to include source-level citation evidence suitable for trace, audit, and user-facing attribution.

#### Scenario: RAG retrieve invocation succeeds
- **WHEN** a client invokes `POST /api/capabilities/knowledge.rag.retrieve/invoke`
- **THEN** the response includes a provider-neutral envelope
- **AND** the result includes `answer_context`
- **AND** each returned document includes `source_id`, `document_id`, `title`, `snippet`, `score`, and `citation`

#### Scenario: RAG provider is unavailable
- **WHEN** the configured RAG provider cannot be reached
- **THEN** the invoke or health response returns a structured provider error
- **AND** `/api/chat` and the main server remain healthy

### Requirement: Knowledge graph query returns graph evidence
The system SHALL expose knowledge graph query capability separately from RAG retrieval.

#### Scenario: Graph query invocation succeeds
- **WHEN** a client invokes `POST /api/capabilities/knowledge.graph.query/invoke`
- **THEN** the response includes a provider-neutral envelope
- **AND** the result includes `graph_id`, `entities`, `relations`, `paths`, and `evidence`

#### Scenario: Graph provider is unavailable
- **WHEN** the configured graph provider cannot be reached
- **THEN** the invoke or health response returns a structured provider error
- **AND** the main server remains healthy

### Requirement: Knowledge registries expose domain agent bindings
The Runtime Surface SHALL expose read-only knowledge registries derived from domain agent manifests.

#### Scenario: Domain agent declares RAG and graph sources
- **WHEN** a domain agent manifest declares `capabilities.rag_sources` or `capabilities.graph_sources`
- **THEN** Runtime Surface includes `rag_source_registry`
- **AND** Runtime Surface includes `knowledge_graph_registry`
- **AND** each registry entry includes the owning `agent_id`

#### Scenario: No domain agent declares knowledge sources
- **WHEN** no manifest declares RAG or graph sources
- **THEN** the registry contracts remain stable
- **AND** they report zero entries without blocking Runtime Surface assembly

### Requirement: External Knowledge Provider development contract is documented
The repository SHALL document how an external Knowledge Provider should be developed and integrated.

#### Scenario: Developer reads provider guide
- **WHEN** a developer opens the external RAG provider development guide
- **THEN** the guide describes project layout, minimum HTTP API, RAG request and response contracts, graph query contracts, health checks, and MyPrivateAgent environment wiring

### Requirement: External provider guidance preserves runtime boundary
The external knowledge provider guidance SHALL keep implementation dependencies and data lifecycle concerns outside MyPrivateAgent core runtime.

#### Scenario: Provider uses LlamaIndex
- **WHEN** the external provider implements document RAG with LlamaIndex
- **THEN** MyPrivateAgent invokes it only through provider-neutral HTTP capability contracts
- **AND** MyPrivateAgent does not import LlamaIndex modules

#### Scenario: Provider uses Neo4j GraphRAG
- **WHEN** the external provider implements graph retrieval with Neo4j GraphRAG
- **THEN** MyPrivateAgent invokes it only through provider-neutral HTTP capability contracts
- **AND** MyPrivateAgent does not import Neo4j or graph retriever modules

### Requirement: Knowledge provider catalog supports readiness checks
The external knowledge provider SHALL expose enough source catalog metadata for MyPrivateAgent governance surfaces to identify missing or degraded source bindings.

#### Scenario: Declared source is unavailable
- **WHEN** a domain agent declares a source id that the provider does not expose as ready
- **THEN** provider capability or heartbeat responses include a machine-readable missing or degraded status
- **AND** MyPrivateAgent can surface the condition without blocking application startup

### Requirement: Unified knowledge provider repo-side trial outcome is exportable
MyPrivateAgent SHALL provide a read-only repo-side trial outcome for the unified knowledge provider integration.

#### Scenario: Trial checks minimal provider access path
- **WHEN** the repo-side trial outcome is generated
- **THEN** it checks provider health, manifest discovery, preflight readiness, RAG retrieve consumption, and source binding review access
- **AND** it records each check with status, endpoint, summary, and recommended action

#### Scenario: Trial emits caller-owned decision
- **WHEN** all required trial checks pass
- **THEN** the outcome status is `trial_passed`
- **AND** the recommended next action is to proceed with MyPrivateAgent integration hardening

#### Scenario: Trial fails closed on required protocol failures
- **WHEN** the provider is unreachable, returns invalid JSON, fails a required endpoint, or omits required response fields
- **THEN** the outcome status is `trial_blocked`
- **AND** the output identifies the failing check and recovery action

### Requirement: Repo-side trial preserves provider and caller boundaries
The repo-side trial SHALL remain a read-only caller-side smoke and not mutate provider or caller control-plane state.

#### Scenario: Trial does not create source binding
- **WHEN** source binding review is checked
- **THEN** the trial only reads provider source-binding evidence
- **AND** it does not create source-to-agent binding, approvals, audit records, or runtime policy decisions

#### Scenario: Trial does not change runtime defaults
- **WHEN** the trial outcome is generated
- **THEN** it does not change chat defaults, retrieval backend defaults, GraphRAG execution, or answer composition behavior
- **AND** it does not store provider API key values in generated artifacts

### Requirement: Unified knowledge provider integration closure is explicit
MyPrivateAgent SHALL emit an explicit Phase 20 integration closure decision for the unified knowledge provider after caller-side trial evidence is available.

#### Scenario: Closure emits go after caller-side trial passes
- **WHEN** the Phase 19 trial outcome is `trial_passed`
- **AND** provider health, manifest, preflight, source binding review access, and RAG retrieve checks are all `ready`
- **THEN** the Phase 20 closure decision is `go`
- **AND** the recommended next line is grounding policy or integration hardening, not further handoff evidence expansion

#### Scenario: Closure blocks on failed required evidence
- **WHEN** the trial outcome is missing, invalid, `trial_blocked`, or includes a blocked required check
- **THEN** the Phase 20 closure decision is `blocked`
- **AND** the output identifies required recovery actions before integration can continue

#### Scenario: Closure preserves chat promotion boundary
- **WHEN** the closure decision is generated
- **THEN** default `/api/chat` retrieval injection remains disabled
- **AND** source binding, approval, audit policy, and final answer composition remain outside this phase

### Requirement: GraphRAG promotion remains separately gated
MyPrivateAgent SHALL NOT treat provider readiness evidence or RAG retrieve success as proof that GraphRAG execution is production-ready.

#### Scenario: Closure records GraphRAG boundary
- **WHEN** the Phase 20 closure decision is generated
- **THEN** it records GraphRAG as `not_promoted` unless a later provider-side GraphRAG gate proves executable graph evidence
- **AND** it permits schema discovery or structured not-implemented behavior without blocking the RAG integration closure
