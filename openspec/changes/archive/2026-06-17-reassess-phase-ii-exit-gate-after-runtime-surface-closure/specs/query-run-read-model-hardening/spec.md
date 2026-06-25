## ADDED Requirements

### Requirement: Query/Run read-model hardening MUST inform Phase II exit readiness
The Phase II exit gate MUST consider completed Query/Run read-model hardening as evidence that backend read-model convergence is no longer the default blocker.

#### Scenario: Query/Run closure evidence is included
- **WHEN** Phase II exit readiness is reassessed
- **THEN** `main_chat_query_detail`, `main_chat_query_history`, `recent_queries`, and shared interpretation metadata MUST be counted as read-model closure evidence
- **AND** further multi-channel query history/workspace expansion MUST remain paused unless a separate promotion decision exists
