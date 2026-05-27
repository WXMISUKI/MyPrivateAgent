## ADDED Requirements

### Requirement: Runtime Surface child merge run-state fixtures MUST align with child executor prerequisites
Runtime Surface tests that assert child merge state in `runtime_core` or `governance_overview.run` MUST construct child executor fixtures that satisfy current child executor execution prerequisites.

#### Scenario: Governance run state surfaces merged child semantics
- **WHEN** Runtime Surface test setup expects `runtime_core.child_merge_intent` and `governance_overview.run.child_merge_intent` to reflect executed child output
- **THEN** the setup MUST first produce a successfully merged child executor output
- **AND** it MUST include required execution opt-in evidence instead of relying on blocked child execution fallback semantics
