## ADDED Requirements

### Requirement: Runtime contracts can reference PromptOps visibility
Runtime contract documentation and read models SHALL be able to reference PromptOps as governance visibility without treating it as a behavior-affecting runtime dependency.

#### Scenario: PromptOps is available as governance metadata
- **WHEN** runtime contract consumers inspect agent behavior governance
- **THEN** PromptOps visibility can explain prompt version, activation status, eval binding, grounding policy reference, and rollback metadata
- **AND** default chat execution remains governed by the existing prompt injection path until a later eval-backed promotion change
