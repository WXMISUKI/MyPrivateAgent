## MODIFIED Requirements

### Requirement: Real caller trial closure takes priority over provider optimization
The unified knowledge capability runtime SHALL prioritize real caller-side trial closure over further provider retrieval optimization after the provider-side feedback contract is ready.

#### Scenario: Provider feedback contract is already available
- **WHEN** MyPrivateAgent can already export a provider feedback-compatible trial payload
- **THEN** the next default step is to run and document a real caller-side live trial closure
- **AND** the team does not treat retrieval strategy ideas as immediate implementation work

#### Scenario: Provider local use loop is already closed
- **WHEN** the external provider reports local usable evidence and MyPrivateAgent has Phase 26 caller closure docs
- **THEN** MyPrivateAgent refreshes caller-owned smoke and provider feedback artifacts instead of reopening provider-readiness phases
- **AND** the closure keeps default `/api/chat` retrieval injection, source binding automation, GraphRAG execution, and provider runtime promotion disabled

#### Scenario: Caller closure documents local enablement
- **WHEN** the Phase 26 caller closure is completed
- **THEN** MyPrivateAgent documents the local provider enablement settings and explicit caller verification commands
- **AND** successful explicit verification does not imply default chat grounding or final answer policy promotion
