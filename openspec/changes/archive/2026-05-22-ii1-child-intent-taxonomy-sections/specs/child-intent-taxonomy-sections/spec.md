## ADDED Requirements

### Requirement: Child Executor Intent Taxonomy Must Be Stable

Child executor merge-related contracts MUST expose a stable supported intent set rather than rely on ad hoc string conventions.

#### Scenario: Merged semantics read model exposes supported intents

- **GIVEN** the runtime returns a child executor merged semantics contract
- **WHEN** the contract is read by a consumer
- **THEN** it MUST expose `intent_catalog_version`
- **AND** it MUST expose the stable supported child intents

### Requirement: Parent Merged Semantics Must Expose Sectioned View

Parent merged semantics MUST expose a sectioned read model so parent consumers do not need to infer sections from flat fields.

#### Scenario: Dedicated merged semantics exposes sections

- **GIVEN** one or more child outputs were merged into a parent run
- **WHEN** `summarize_child_executor_merged_semantics(...)` is called
- **THEN** the contract MUST expose `merged_sections`
- **AND** it MUST include sectioned views for merged entities, focus, actions, and latest conclusion

### Requirement: Existing Flat Semantics Must Stay Compatible

Sectioned merge semantics MUST extend the current contract without breaking existing flat-field consumers.

#### Scenario: Existing fields remain available

- **GIVEN** a merged semantics contract is returned
- **WHEN** an existing consumer reads `intent_label`, `entities`, `focus_points`, `action_items`, or `merge_behavior`
- **THEN** those fields MUST still be present
- **AND** they MUST stay coherent with the sectioned view
