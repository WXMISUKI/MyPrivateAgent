# unified-knowledge-capability-runtime Specification

## MODIFIED Requirements

### Requirement: Knowledge provider readiness does not enable chat grounding
The unified knowledge provider trial and closure evidence SHALL NOT enable default chat retrieval injection without a separate grounding policy promotion.

#### Scenario: Provider trial passes
- **WHEN** the unified knowledge provider repo-side trial outcome is `trial_passed`
- **THEN** default `/api/chat` retrieval injection remains disabled
- **AND** any use of returned evidence remains controlled by caller-side grounding policy decisions

#### Scenario: Grounding policy decision is evaluated
- **WHEN** a caller-owned answer path evaluates grounding policy
- **THEN** it may consume provider evidence already returned by a separate provider call
- **AND** it does not call the provider or mutate runtime defaults

#### Scenario: Promotion gate consumes provider trial evidence
- **WHEN** a grounded-answer promotion gate evaluates provider readiness
- **THEN** provider trial success is treated as one readiness input
- **AND** provider trial success alone does not enable chat grounding, answer generation, source binding, or GraphRAG execution
