## ADDED Requirements

### Requirement: Knowledge provider readiness does not enable chat grounding
The unified knowledge provider trial and closure evidence SHALL NOT enable default chat retrieval injection without a separate grounding policy promotion.

#### Scenario: Provider trial passes
- **WHEN** the unified knowledge provider repo-side trial outcome is `trial_passed`
- **THEN** default `/api/chat` retrieval injection remains disabled
- **AND** any use of returned evidence remains controlled by caller-side grounding policy decisions

#### Scenario: Grounding policy decision is evaluated
- **WHEN** a caller-owned answer path evaluates grounding policy
- **THEN** the decision uses already-returned evidence pack metadata
- **AND** it does not call the provider or mutate runtime defaults
