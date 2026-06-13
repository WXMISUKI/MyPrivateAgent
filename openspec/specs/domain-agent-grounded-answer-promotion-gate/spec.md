# domain-agent-grounded-answer-promotion-gate Specification

## Purpose

Define the caller-owned promotion gate that determines whether a domain agent may enter a grounded-answer repo-side trial using already-available control-plane evidence. This capability does not enable default `/api/chat` retrieval injection.

## Requirements

### Requirement: Promotion gate returns a bounded trial decision

The system SHALL expose a machine-readable grounded-answer promotion decision for a domain agent.

#### Scenario: Domain agent is ready for grounded-answer trial
- **WHEN** provider readiness is ready
- **AND** grounding decision is allowed
- **AND** PromptOps evidence is active or review
- **AND** MemoryOps evidence keeps retrieved knowledge promotion explicit
- **AND** multi-turn eval evidence has passed
- **THEN** the promotion decision is `go`
- **AND** the recommended next action is to start a repo-side grounded-answer trial

#### Scenario: Package dry-run requires promotion go
- **WHEN** a grounded-answer package dry-run is requested
- **AND** the promotion decision is not `go`
- **THEN** the package dry-run MUST remain `review` or `blocked`
- **AND** promotion `go` alone still does not permit answer generation

#### Scenario: Required evidence is missing
- **WHEN** required provider, grounding, PromptOps, MemoryOps, or eval evidence is missing
- **THEN** the promotion decision is `blocked` or `review`
- **AND** the output includes machine-readable blockers or warnings

### Requirement: Promotion gate is side-effect-free

The promotion gate SHALL only aggregate readiness evidence and SHALL NOT invoke provider, chat, answer generation, memory writes, or source binding behavior.

#### Scenario: Promotion gate is evaluated
- **WHEN** a caller evaluates the promotion gate
- **THEN** no provider request is sent
- **AND** no answer is generated
- **AND** no memory, audit, source binding, or chat state is mutated
- **AND** default `/api/chat` retrieval injection remains disabled

#### Scenario: Trial surface consumes promotion decision
- **WHEN** the grounded-answer trial surface evaluates a requested agent
- **THEN** it consumes the promotion decision as trial evidence
- **AND** the trial surface does not promote runtime behavior or default chat retrieval injection by itself

### Requirement: Promotion gate fails closed for provider and grounding blockers

The promotion gate SHALL block repo-side grounded-answer trial when provider readiness or grounding policy evidence is unsafe.

#### Scenario: Provider is not ready
- **WHEN** provider evidence is unavailable, degraded, or not ready
- **THEN** the promotion decision is `blocked`
- **AND** the blockers identify provider readiness as the missing prerequisite

#### Scenario: Governance readiness allows document RAG trial promotion
- **WHEN** provider evidence includes `governance_readiness.rag_retrieve.status = ready`
- **AND** grounding, PromptOps, MemoryOps, and eval evidence satisfy the existing promotion requirements
- **THEN** the promotion gate SHALL treat provider readiness as ready for document RAG trial promotion
- **AND** the promotion gate SHALL preserve `default_chat_grounding.status = gated` as a behavior boundary rather than a blocker for repo-side trial

#### Scenario: Governance readiness blocks unreachable provider
- **WHEN** provider evidence includes `governance_readiness.overall_status = unreachable`
- **THEN** the promotion decision SHALL be `blocked`
- **AND** the blockers SHALL identify provider readiness as unreachable

#### Scenario: Governance readiness reviews degraded source catalog
- **WHEN** provider evidence includes `governance_readiness.source_catalog.status = degraded`
- **THEN** the promotion decision SHALL be `review` or `blocked`
- **AND** the output SHALL preserve a machine-readable provider catalog reason

#### Scenario: Grounding decision is blocked
- **WHEN** grounding policy decision is `blocked`
- **THEN** the promotion decision is `blocked`
- **AND** the blockers preserve the grounding reason code

#### Scenario: Grounding policy needs review
- **WHEN** grounding policy decision is `review`
- **THEN** the promotion decision is `review`
- **AND** the warnings preserve the grounding reason code

### Requirement: PromptOps, MemoryOps, and eval evidence gate trial promotion

The promotion gate SHALL require enough prompt, memory, and deterministic eval evidence to avoid promoting behavior changes from isolated provider success.

#### Scenario: PromptOps evidence is missing
- **WHEN** PromptOps version visibility evidence is missing
- **THEN** the promotion decision is `review`
- **AND** the warnings identify missing prompt readiness

#### Scenario: MemoryOps evidence is unsafe
- **WHEN** MemoryOps evidence does not report retrieved knowledge promotion as explicit-only
- **THEN** the promotion decision is `review`
- **AND** the warnings identify memory boundary review

#### Scenario: Multi-turn eval is failed or blocked
- **WHEN** multi-turn eval evidence is `failed` or `blocked`
- **THEN** the promotion decision is `blocked`
- **AND** the blockers identify eval readiness as the missing prerequisite

### Requirement: GraphRAG remains separately gated

The promotion gate SHALL NOT treat document RAG readiness as GraphRAG execution readiness.

#### Scenario: Graph grounded answer trial is requested before promotion
- **WHEN** a promotion decision requests graph usage
- **THEN** the promotion decision is `blocked`
- **AND** the output identifies GraphRAG execution as not promoted

#### Scenario: Graph request is blocked despite RAG readiness
- **WHEN** a promotion decision requests graph usage
- **AND** provider evidence includes `governance_readiness.rag_retrieve.status = ready`
- **AND** `governance_readiness.graph_query.status = gated`
- **THEN** the promotion decision SHALL be `blocked`
- **AND** the blockers SHALL identify GraphRAG execution as not promoted
