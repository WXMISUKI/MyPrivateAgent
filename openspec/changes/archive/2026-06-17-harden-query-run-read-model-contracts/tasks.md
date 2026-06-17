## 1. Specification

- [x] 1.1 Validate the OpenSpec change artifacts before implementation.
- [x] 1.2 Confirm the scope stays limited to query/run read models and recovery read models.

## 2. Implementation

- [x] 2.1 Review and, if needed, refactor Runtime Surface query/history builder seams so detail and history remain clearly separated.
- [x] 2.2 Align shared query/run interpretation helpers for Runtime Surface and Governance Timeline consumers.
- [x] 2.3 Verify `run_recovery` remains compact and non-executable while preserving recovery operation evidence shape.

## 3. Verification

- [x] 3.1 Add or adjust focused backend tests for `main_chat_query_detail`, `main_chat_query_history`, `recent_queries`, and `run_recovery`.
- [x] 3.2 Run focused Runtime Surface tests covering query detail/history and recovery read models.

## 4. Documentation and Archive

- [x] 4.1 Update runtime contract and roadmap docs to reflect the hardened query/run read-model boundary.
- [x] 4.2 Sync canonical specs, validate all OpenSpec specs strictly, and archive the completed change.
