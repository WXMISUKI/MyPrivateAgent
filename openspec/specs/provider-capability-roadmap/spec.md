# provider-capability-roadmap Specification

## Purpose
TBD - created by archiving change stabilize-provider-capability-roadmap. Update Purpose after archive.
## Requirements
### Requirement: Provider capability roadmap is spec-backed

The project MUST maintain a canonical spec-backed provider capability roadmap for major provider-first Agent platform work.

#### Scenario: Future agents need task direction
- **WHEN** maintainers decide the next provider capability slice
- **THEN** they MUST consult `provider-capability-roadmap`
- **AND** they MUST choose a focused OpenSpec change rather than implementing unrelated P0/P1/P2 items together.

### Requirement: External RAG and GraphRAG remain data-plane work

MyPrivateAgent MUST keep RAG, GraphRAG, embedding, vector store, graph database, reranking, parsing, and index lifecycle inside external provider projects.

#### Scenario: External provider is still under development
- **WHEN** the external RAG / GraphRAG provider is not yet readiness-complete
- **THEN** MyPrivateAgent MUST limit work to contract, docs, source binding, health/readiness, and local integration smoke
- **AND** it MUST NOT add vector store, graph database, embedding, LlamaIndex, or Neo4j runtime dependencies to the main backend.

#### Scenario: Provider is ready for caller-side integration
- **WHEN** the external provider exposes stable `/health`, `/api/capabilities`, source catalog, `/api/rag/sources`, `/api/rag/retrieve`, and `/api/graph/schemas` responses
- **THEN** MyPrivateAgent MAY implement caller-side readiness visibility and retrieval consumption smoke
- **AND** default chat retrieval injection MUST remain blocked until a later grounding policy change.

### Requirement: P0 provider work follows active external RAG change

The project MUST treat `plan-external-rag-graphrag-provider` as the active P0 line for external knowledge provider readiness until it is archived.

#### Scenario: Continuing provider work
- **WHEN** maintainers continue RAG / GraphRAG provider work
- **THEN** they MUST first inspect `openspec/changes/plan-external-rag-graphrag-provider`
- **AND** they MUST avoid opening a competing broad RAG change unless the active change is archived or explicitly superseded.

### Requirement: Grounding policy is the next behavior control layer

The project MUST define grounding policy before enabling default knowledge injection in `/api/chat`.

#### Scenario: Agent declares knowledge behavior
- **WHEN** a domain agent needs controlled knowledge use
- **THEN** a future `add-agent-grounding-policy-contract` change MUST define fields such as `require_citations`, `allow_ungrounded`, `must_use_knowledge_for_domains`, `fallback_policy`, and `source_acl_mode`
- **AND** the first implementation SHOULD expose policy/readiness in Runtime Surface before changing default chat behavior.

### Requirement: PromptOps is distinct from prompt CRUD

The project MUST treat enterprise PromptOps as a separate governance capability from the existing `/prompts` CRUD endpoints.

#### Scenario: Prompt governance is expanded
- **WHEN** maintainers extend prompt management
- **THEN** a future `add-promptops-versioned-prompt-contract` change MUST define prompt versions, template variable schemas, eval bindings, activation history, rollout metadata, approval state, and rollback metadata.

### Requirement: MemoryOps is distinct from context packing

The project MUST treat long-term memory governance as separate from chat history packing and `/compact` summaries.

#### Scenario: Memory governance is expanded
- **WHEN** maintainers extend memory capability
- **THEN** a future `add-agent-memoryops-lifecycle-contract` change MUST distinguish hot session state, conversation summary, long-term user/team/domain memory, and retrieved knowledge evidence
- **AND** it MUST define source, TTL, confidence, deletion, expiration, conflict handling, and injection trace semantics.

### Requirement: Multi-turn evaluation gates prompt, RAG, and context changes

The project MUST add scenario-based multi-turn evaluation before treating prompt/RAG/context behavior as production-stable.

#### Scenario: Behavior-affecting change is proposed
- **WHEN** a future change affects prompt selection, RAG grounding, memory injection, or context packing
- **THEN** `add-multiturn-agent-evaluation-gate` or an equivalent focused change MUST define multi-turn scenarios, expected tool/knowledge use, expected refusal or fallback behavior, and regression reporting.

### Requirement: P2 work must wait for P0/P1 control contracts

The project MUST defer broader multimodal, workflow/chatflow, enterprise connector, and provider ops expansion until P0/P1 contracts are stable enough to avoid control-plane drift.

#### Scenario: New P2 capability is requested
- **WHEN** maintainers propose image/video/audio multimodal taxonomy, workflow/chatflow, enterprise connectors, or provider ops
- **THEN** they MUST create a focused OpenSpec change
- **AND** they MUST state how the work uses existing Capability Runtime, ToolRuntime, Policy/Approval, Trace/Audit, and Runtime Surface boundaries.

### Requirement: Provider readiness evidence has a stop condition
The provider capability roadmap SHALL define a stop condition for handoff and readiness evidence slices so provider readiness work does not continue indefinitely.

#### Scenario: Caller-side trial passes
- **WHEN** a caller-side trial outcome passes required provider access checks
- **THEN** the roadmap SHALL allow the readiness evidence chain to close with a go/review/blocked decision
- **AND** subsequent work SHALL move to the next focused control contract instead of adding more readiness evidence by default

#### Scenario: Default chat behavior is requested
- **WHEN** maintainers want default chat retrieval injection after readiness closure
- **THEN** the roadmap SHALL route that work through grounding policy and evaluation gates
- **AND** it SHALL NOT be treated as a readiness evidence follow-up
