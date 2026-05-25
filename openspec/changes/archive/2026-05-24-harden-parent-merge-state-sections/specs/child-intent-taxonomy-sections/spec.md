## MODIFIED Requirements

### Requirement: Parent Merged Semantics Must Expose Sectioned View

Parent merged semantics MUST expose a sectioned read model so parent consumers do not need to infer sections from flat fields.

#### Scenario: Dedicated merged semantics exposes sections

- **GIVEN** one or more child outputs were merged into a parent run
- **WHEN** `summarize_child_executor_merged_semantics(...)` is called
- **THEN** the contract MUST expose `merged_sections`
- **AND** it MUST include sectioned views for merged entities, focus, actions, and latest conclusion
- **AND** each section MUST expose a stable `section_kind`
- **AND** list sections MUST expose `item_count`
- **AND** text sections MUST expose `text_length`

