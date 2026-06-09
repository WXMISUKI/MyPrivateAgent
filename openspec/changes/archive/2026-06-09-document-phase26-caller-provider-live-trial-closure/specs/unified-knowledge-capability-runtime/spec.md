## ADDED Requirements

### Requirement: Real caller trial closure takes priority over provider optimization
The unified knowledge capability runtime SHALL prioritize real caller-side trial closure over further provider retrieval optimization after the provider-side feedback contract is ready.

#### Scenario: Provider feedback contract is already available
- **WHEN** MyPrivateAgent can already export a provider feedback-compatible trial payload
- **THEN** the next default step is to run and document a real caller-side live trial closure
- **AND** the team does not treat retrieval strategy ideas as immediate implementation work
