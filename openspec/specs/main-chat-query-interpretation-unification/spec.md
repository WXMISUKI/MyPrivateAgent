# main-chat-query-interpretation-unification Specification

## Purpose
Unify interpretation of main chat query metadata so read models and governance views share the same query identity semantics.
## Requirements
### Requirement: Query Read Model Interpretation Is Shared
The system MUST normalize `main_chat_query_detail` and `main_chat_query_history` through a shared interpretation path so Runtime Surface and Governance Timeline observe the same contract semantics.

#### Scenario: Shared detail interpretation
- **WHEN** Runtime Surface and Governance Timeline consume `main_chat_query_detail`
- **THEN** they MUST use the same normalize helper path
- **AND** they MUST preserve the same metadata semantics for read model layer, source channel, and identity kind

#### Scenario: Shared history interpretation
- **WHEN** Runtime Surface and Governance Timeline consume `main_chat_query_history`
- **THEN** they MUST use the same normalize helper path
- **AND** they MUST preserve the same pagination and identity semantics

#### Scenario: Backward-compatible display
- **WHEN** existing UI components render the normalized contracts
- **THEN** they MUST retain current visible behavior
- **AND** they MUST NOT require per-component contract redefinition
