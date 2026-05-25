# parent-merge-state-surface Specification

## Purpose
Define the parent-facing merge state surface produced from child executor outputs and merge semantics.
## Requirements
### Requirement: Merged Semantics Must Expose Parent State Surface

The dedicated child merged semantics contract MUST expose a minimal parent state surface so parent overview consumers do not need to reconstruct summary state from sections.

#### Scenario: Parent overview reads merged semantics state

- **GIVEN** a merged semantics contract is returned
- **WHEN** a parent overview consumer reads it
- **THEN** it MUST expose `parent_state_surface`
- **AND** the surface MUST include current intent, counts, primary entities, and latest conclusion
- **AND** the surface MUST identify the section source used to derive parent counts
- **AND** section-derived counts MUST remain coherent with `merged_sections`

### Requirement: Runtime Surface Must Surface Parent Merge State In Overview

Runtime Surface MUST expose child merge state in a parent-facing overview location, not only in the child output details workspace.

#### Scenario: Runtime Surface shows child merge state in run overview

- **GIVEN** child merged semantics are available
- **WHEN** Runtime Surface renders governance/runtime overview
- **THEN** the parent-facing overview MUST show the current child merge intent and latest merged conclusion
- **AND** it MUST preserve section-source and section-count evidence from `parent_state_surface`
