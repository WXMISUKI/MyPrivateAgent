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

### Requirement: Knowledge provider readiness does not enable chat grounding
The unified knowledge provider trial and closure evidence SHALL NOT enable default chat retrieval injection without a separate grounding policy promotion.

#### Scenario: Provider trial passes
- **WHEN** the unified knowledge provider repo-side trial outcome is `trial_passed`
- **THEN** default `/api/chat` retrieval injection remains disabled
- **AND** any use of returned evidence remains controlled by caller-side grounding policy decisions

#### Scenario: Grounding policy decision is evaluated
- **WHEN** a caller-owned answer path evaluates grounding policy
- **THEN** the decision uses already-returned evidence pack metadata
- **AND** it does not call the provider or mutate runtime defaults

#### Scenario: Promotion gate consumes provider trial evidence
- **WHEN** a grounded-answer promotion gate evaluates provider readiness
- **THEN** provider trial success is treated as one readiness input
- **AND** provider trial success alone does not enable chat grounding, answer generation, source binding, or GraphRAG execution

### Requirement: Repo-side document RAG trial records provider readiness closure
The unified knowledge provider repo-side trial outcome SHALL optionally consume provider-side document RAG trial readiness closure evidence as read-only context.

#### Scenario: Provider readiness closure supports trial start
- **WHEN** the trial outcome is generated with a provider readiness artifact path
- **AND** the artifact reports `decision=go`
- **AND** the artifact reports `trial_readiness_state=ready_for_repo_side_document_rag_trial`
- **THEN** the trial outcome includes a `provider_document_rag_readiness` check with status `ready`
- **AND** the trial still runs the live provider health, manifest, preflight, source-binding, and RAG retrieve checks

#### Scenario: Provider readiness closure is blocked
- **WHEN** the trial outcome is generated with a provider readiness artifact path
- **AND** the artifact is missing, invalid, malformed, or reports a blocked decision
- **THEN** the trial outcome includes a blocked `provider_document_rag_readiness` check
- **AND** the trial outcome identifies the recovery action before continuing integration

#### Scenario: Provider readiness closure is omitted
- **WHEN** the trial outcome is generated without a provider readiness artifact path
- **THEN** the trial outcome remains compatible with the existing HTTP-only repo-side trial
- **AND** the output records that provider document RAG readiness evidence was not supplied

### Requirement: Provider readiness cannot replace caller-side trial checks
Provider-side readiness evidence SHALL NOT bypass MyPrivateAgent repo-side trial checks or mutate caller/provider state.

#### Scenario: Provider readiness is ready
- **WHEN** provider document RAG readiness evidence is `ready`
- **THEN** the trial still requires live HTTP trial checks before emitting `trial_passed`
- **AND** the trial does not create source-to-agent binding, approval records, audit policy changes, runtime promotion, default chat retrieval injection, or GraphRAG execution

### Requirement: Knowledge provider supports domain-agent live trial retrieval
MyPrivateAgent SHALL be able to use the external knowledge provider RAG retrieve contract as an explicit domain-agent trial input.

#### Scenario: Domain-agent live trial retrieves provider evidence
- **WHEN** a domain-agent live grounded-answer trial calls `POST /api/rag/retrieve`
- **THEN** the provider result is interpreted through the existing `documents` and `metadata.evidence_pack` contract
- **AND** the retrieved evidence is treated as trial evidence, not as default chat context injection

### Requirement: Local provider corpus trial is exportable
MyPrivateAgent SHALL provide a read-only local corpus trial for an approved provider-visible knowledge source.

#### Scenario: Local corpus trial passes
- **WHEN** the configured provider base URL is reachable
- **AND** the configured source is visible in `/api/rag/sources`
- **AND** its source document manifest is available
- **AND** answerable corpus questions return retrieved evidence and answer citations within the retrieve citation allowlist
- **AND** the negative-control query returns insufficient evidence without citations
- **THEN** the trial decision is `go`
- **AND** the output records source id, query cases, retrieve counts, answer statuses, citations, invalid citations, and recommended next action

#### Scenario: Local corpus trial needs review
- **WHEN** the provider is reachable but an answerable case returns weak or missing evidence
- **OR** the negative-control case returns unexpected evidence without violating citation allowlists
- **THEN** the trial decision is `review`
- **AND** the output identifies the case-level reason before any grounded-answer workflow uses the source

#### Scenario: Local corpus trial is blocked
- **WHEN** the provider is unreachable, the source is missing, the manifest fails, retrieve/answer calls fail, response contracts are invalid, or answer citations are outside the retrieve citation allowlist
- **THEN** the trial decision is `blocked`
- **AND** the output identifies the blocking check and recovery action

### Requirement: Local provider corpus trial preserves caller/provider boundaries
The local corpus trial SHALL remain explicit, read-only, and outside default chat grounding.

#### Scenario: Trial is run
- **WHEN** the local corpus trial exporter runs
- **THEN** it does not create source-to-agent binding, mutate domain-agent manifests, write audit or memory records, enable default `/api/chat` retrieval injection, run MyPrivateAgent orchestration, start provider services, promote retrieval backends, start OCR, or execute GraphRAG

#### Scenario: Provider API key is supplied
- **WHEN** the trial command receives a provider API key
- **THEN** it sends supported provider API headers to `/api/*` requests
- **AND** it never writes the secret value into JSON or Markdown output

### Requirement: Document RAG upload-to-use trial does not promote default knowledge runtime
The unified knowledge capability runtime SHALL treat document RAG upload-to-use results as explicit local trial evidence only.

#### Scenario: Upload-to-use loop succeeds
- **WHEN** the document RAG upload-to-use loop returns `go`
- **THEN** MyPrivateAgent may use the generated source id for explicit local RAG trial questions
- **AND** the success does not enable default `/api/chat` retrieval injection, source-to-agent binding, answer generation policy, or GraphRAG execution

### Requirement: Real caller trial closure takes priority over provider optimization
The unified knowledge capability runtime SHALL prioritize real caller-side trial closure over further provider retrieval optimization after the provider-side feedback contract is ready.

#### Scenario: Provider feedback contract is already available
- **WHEN** MyPrivateAgent can already export a provider feedback-compatible trial payload
- **THEN** the next default step is to run and document a real caller-side live trial closure
- **AND** the team does not treat retrieval strategy ideas as immediate implementation work

#### Scenario: Provider local use loop is already closed
- **WHEN** the external provider reports local usable evidence and MyPrivateAgent has Phase 26 caller closure docs
- **THEN** MyPrivateAgent refreshes caller-owned smoke and provider feedback artifacts instead of reopening provider-readiness phases
- **AND** the closure keeps default `/api/chat` retrieval injection, source binding automation, GraphRAG execution, and provider runtime promotion disabled

#### Scenario: Caller closure documents local enablement
- **WHEN** the Phase 26 caller closure is completed
- **THEN** MyPrivateAgent documents the local provider enablement settings and explicit caller verification commands
- **AND** successful explicit verification does not imply default chat grounding or final answer policy promotion

### Requirement: Repo-side trial outcome can feed provider-side feedback closure
MyPrivateAgent SHALL export a repo-side unified knowledge provider trial outcome that can be reused as input to provider-side feedback closure without manual field reconstruction.

#### Scenario: Trial outcome includes provider feedback contract fields
- **WHEN** the unified knowledge provider repo-side trial outcome is exported
- **THEN** the artifact includes a caller-owned `provider_feedback_input` payload with the minimum fields required by the provider Phase 25 feedback contract
- **AND** the output remains read-only and still preserves the existing MyPrivateAgent caller-side trial report

#### Scenario: Incomplete trial evidence stays conservative
- **WHEN** the repo-side trial outcome lacks enough evidence to prove a caller-side success state for provider follow-up
- **THEN** the feedback-compatible payload stays conservative
- **AND** it does not imply `no_provider_action_required` unless the required retrieve evidence, including citation allowlist, is present

### Requirement: Knowledge provider governance readiness is exposed
MyPrivateAgent SHALL expose a compact read-only governance readiness block for the external Knowledge Provider through the capability health or heartbeat surfaces.

#### Scenario: Provider is ready for explicit RAG
- **WHEN** the external knowledge provider is configured
- **AND** provider health is ready
- **AND** provider catalog is ready or contains at least one ready knowledge source
- **THEN** capability health or heartbeat SHALL include `governance_readiness`
- **AND** `governance_readiness.rag_retrieve.status` SHALL be `ready`
- **AND** `governance_readiness.provider_configured` SHALL be `true`

#### Scenario: Provider is unreachable
- **WHEN** the configured provider is unreachable
- **THEN** capability health or heartbeat SHALL still return a structured provider error
- **AND** `governance_readiness.overall_status` SHALL be `unreachable`
- **AND** the main application and ordinary chat behavior SHALL remain healthy

#### Scenario: Provider catalog is degraded
- **WHEN** provider health is ready but the source catalog is unavailable or reports degraded sources
- **THEN** `governance_readiness.overall_status` SHALL be `degraded`
- **AND** `governance_readiness.source_catalog.status` SHALL identify the catalog posture
- **AND** the readiness block SHALL NOT create source-to-agent bindings

### Requirement: Knowledge provider readiness preserves promotion boundaries
The governance readiness block MUST distinguish explicit RAG usability from GraphRAG execution and default chat grounding promotion.

#### Scenario: RAG ready does not promote GraphRAG
- **WHEN** `governance_readiness.rag_retrieve.status` is `ready`
- **THEN** `governance_readiness.graph_query.status` SHALL remain `gated` unless a later GraphRAG promotion gate proves execution readiness
- **AND** the readiness block SHALL NOT execute `/api/graph/query`

#### Scenario: RAG ready does not enable default chat grounding
- **WHEN** `governance_readiness.rag_retrieve.status` is `ready`
- **THEN** `governance_readiness.default_chat_grounding.status` SHALL remain `gated`
- **AND** `/api/chat` retrieval injection SHALL remain disabled

### Requirement: Knowledge provider readiness remains compact and caller-owned
The readiness block SHALL contain only compact governance evidence and MUST NOT copy raw retrieved documents, API keys, provider clients, or large provider payloads.

#### Scenario: Readiness payload is compact
- **WHEN** readiness is returned in health or heartbeat
- **THEN** it MAY include provider id, configured/enabled booleans, status, reasons, source counts, degraded source ids, and promotion boundary statuses
- **AND** it MUST NOT include provider API key values, retrieved document snippets, full provider raw payloads, or generated answer text
