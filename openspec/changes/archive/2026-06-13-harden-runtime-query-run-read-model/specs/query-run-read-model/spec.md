## ADDED Requirements

### Requirement: Query read-model hardening preserves lifecycle identity
The system SHALL harden existing `main_chat` query read models around `query_id` as the lifecycle identity and SHALL NOT allow `run_id` or timeline event identity to replace it in query detail or history contracts. `associated_run_ids` MAY expose execution instances associated with a query lifecycle, but it MUST remain an associated field.

#### Scenario: Query detail preserves query identity
- **WHEN** `main_chat_query_detail` returns a recorded or empty-state detail contract
- **THEN** the contract SHALL keep `query_id` as the primary lifecycle identifier
- **AND** any `run_id` value SHALL remain an associated execution-instance field rather than the detail identity

#### Scenario: Query history preserves query identity
- **WHEN** `main_chat_query_history` returns summary items
- **THEN** each item SHALL use `query_id` as the summary identity
- **AND** the history contract SHALL NOT require the frontend to infer query identity from raw timeline event identifiers

### Requirement: Shared interpretation consumes stable read-model metadata
The frontend SHALL interpret `main_chat` query detail and history contracts through shared normalization logic when the same metadata appears in Runtime Surface and Governance Timeline.

#### Scenario: Runtime Surface and Governance Timeline share metadata interpretation
- **WHEN** both Runtime Surface and Governance Timeline display `read_model_layer`, `source_channel`, `identity_kind`, `recording_state`, or query summary metadata
- **THEN** they SHALL use the shared governance interpretation helper
- **AND** they SHALL NOT maintain separate query/run semantic mappings for the same fields

#### Scenario: Fallbacks remain transitional
- **WHEN** a frontend fallback is still needed for old or empty payloads
- **THEN** the fallback SHALL preserve the same query/run terminology as the shared helper
- **AND** it SHALL NOT become a new component-local domain interpretation rule

### Requirement: Query read-model hardening does not promote new behavior
This hardening slice SHALL preserve current behavior boundaries and MUST NOT promote provider, retrieval, or non-`main_chat` query workspace behavior.

#### Scenario: Provider behavior remains unchanged
- **WHEN** this change is implemented
- **THEN** `unifiedKnowledgeRAG` provider behavior and default `/api/chat` retrieval behavior SHALL remain unchanged
- **AND** this change SHALL NOT introduce GraphRAG, rerank, hybrid retrieval, query rewrite, or automatic source binding behavior

#### Scenario: Other channels are not promoted
- **WHEN** this change is implemented
- **THEN** `subagent_lane` and `external_adapter` SHALL NOT be promoted to full query history or query workspace behavior
- **AND** any existing recent summary or query detail contracts for those channels SHALL retain their existing scope
