## ADDED Requirements

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
