## ADDED Requirements

### Requirement: MemoryOps registry exposes lifecycle entries
The system SHALL expose a read-only MemoryOps registry that normalizes existing memory-adjacent records into bounded lifecycle entries.

#### Scenario: Instruction memory is normalized
- **GIVEN** `AgentMemoryService` returns loaded memory entries
- **WHEN** the MemoryOps registry is built
- **THEN** each loaded memory layer is represented as `kind="runtime_instruction_memory"`
- **AND** each entry includes `memory_id`, `source`, `scope`, `status`, `confidence`, `ttl_policy`, and `injection_trace`

#### Scenario: No memory layers are loaded
- **GIVEN** no agent memory layers are available
- **WHEN** the MemoryOps registry is built
- **THEN** the registry still returns a stable contract
- **AND** it reports zero active entries without blocking application startup

### Requirement: Conversation summaries are visible as MemoryOps entries
The system SHALL represent durable conversation summaries as `conversation_summary` MemoryOps entries when a summary is available.

#### Scenario: Latest conversation summary exists
- **GIVEN** a durable conversation summary exists for a conversation
- **WHEN** the MemoryOps registry is requested for that conversation
- **THEN** the registry includes a `conversation_summary` entry with message count, last covered message id, trigger, and lifecycle status
- **AND** original message rows remain the audit source

#### Scenario: No conversation summary exists
- **GIVEN** no durable summary exists for the requested conversation
- **WHEN** the registry is built
- **THEN** the registry does not invent a summary entry
- **AND** it reports `conversation_summary.available=false`

### Requirement: Retrieved knowledge evidence is not durable memory by default
The MemoryOps contract SHALL distinguish retrieved knowledge evidence from durable memory.

#### Scenario: Registry reports retrieved knowledge posture
- **WHEN** MemoryOps registry is built
- **THEN** it reports `retrieved_knowledge_evidence.promotion_mode="explicit_only"`
- **AND** it does not store or expose retrieved snippets as long-term memory unless a later explicit promotion flow exists

### Requirement: MemoryOps visibility does not change runtime behavior
The MemoryOps registry SHALL be read-only and SHALL NOT change default chat context packing, prompt injection, or retrieval behavior.

#### Scenario: Registry is requested
- **WHEN** a caller reads the MemoryOps registry
- **THEN** no memory entry is created, deleted, promoted, expired, injected, or retrieved as a side effect
