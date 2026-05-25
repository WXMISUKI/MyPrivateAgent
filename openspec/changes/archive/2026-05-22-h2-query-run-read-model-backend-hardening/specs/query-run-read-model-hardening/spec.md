## ADDED Requirements

### Requirement: Dedicated Query History Is a Stable Read Model
The system MUST provide `main_chat_query_history` as a dedicated read model for cross-query history browsing.

#### Scenario: History browsing beyond recent summaries
- **WHEN** a caller needs query history beyond `recent_queries`
- **THEN** the system MUST serve that need through `main_chat_query_history`
- **AND** it MUST NOT require front-end reconstruction from a generic timeline

### Requirement: Query Detail and Query History Remain Separate
The system MUST keep `main_chat_query_detail` and `main_chat_query_history` as separate contracts with distinct responsibilities.

#### Scenario: Detail vs history
- **WHEN** a caller needs one query’s lifecycle detail
- **THEN** the system MUST use `main_chat_query_detail`
- **WHEN** a caller needs browsing across multiple queries
- **THEN** the system MUST use `main_chat_query_history`

### Requirement: Recent Queries Remain Lightweight
The system MUST continue to expose `recent_queries` as a lightweight summary list and MUST NOT turn it into the primary long-history contract.

#### Scenario: Recent summary usage
- **WHEN** a caller only needs recent query summaries
- **THEN** the system MUST allow `recent_queries` to satisfy that request
- **AND** it MUST keep the list backward compatible

### Requirement: Dedicated Endpoints Are the Primary Growth Path
The system MUST treat dedicated query read-model endpoints as the primary growth path for `main_chat` detail and history expansion.

#### Scenario: Endpoint growth
- **WHEN** query read-model capabilities expand
- **THEN** the system MUST prefer dedicated endpoints for the new behavior
- **AND** it MUST NOT rely on `runtime-profile` as the only growth surface

### Requirement: Shared Query Contract Interpretation
The system MUST ensure `RuntimeSurfacePanel` and `GovernanceTimelinePanel` interpret `main_chat_query_detail` and `main_chat_query_history` through the same normalization rules.

#### Scenario: Shared interpretation
- **WHEN** both panels consume query read model contracts
- **THEN** they MUST use the same shared interpretation logic
- **AND** they MUST NOT independently redefine field semantics

### Requirement: History Pagination Remains Cursor-Friendly
The system MUST keep `main_chat_query_history` compatible with pagination and future cursor evolution.

#### Scenario: Pagination compatibility
- **WHEN** the history contract grows
- **THEN** the contract MUST preserve pagination-friendly metadata
- **AND** it MUST keep item fields compatible with existing recent summary mappings

