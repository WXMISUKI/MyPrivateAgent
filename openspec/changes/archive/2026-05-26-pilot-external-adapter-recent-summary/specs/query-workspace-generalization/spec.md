## ADDED Requirements

### Requirement: external_adapter Recent Summary MUST Not Promote Workspace

The query workspace generalization layer MUST treat `external_adapter_recent_summary` as a shallow pilot and not as a query workspace promotion.

#### Scenario: external_adapter stays below query detail

- **WHEN** external adapter recent summary is recorded
- **THEN** query workspace generalization MUST continue to classify `external_adapter` below `query_detail`
- **AND** it MUST require a separate OpenSpec change before external adapter query detail, query history, or query workspace can be implemented
