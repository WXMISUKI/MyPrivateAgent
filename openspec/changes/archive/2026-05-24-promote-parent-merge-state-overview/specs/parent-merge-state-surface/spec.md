## MODIFIED Requirements

### Requirement: Runtime Surface Must Surface Parent Merge State In Overview

Runtime Surface MUST expose child merge state in a parent-facing overview location, not only in the child output details workspace.

#### Scenario: Runtime Surface shows child merge state in run overview

- **GIVEN** child merged semantics are available
- **WHEN** Runtime Surface renders governance/runtime overview
- **THEN** the parent-facing overview MUST show the current child merge intent and latest merged conclusion
- **AND** it MUST preserve section-source and section-count evidence from `parent_state_surface`

