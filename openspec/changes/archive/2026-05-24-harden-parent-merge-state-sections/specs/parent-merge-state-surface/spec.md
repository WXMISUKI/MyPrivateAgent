## MODIFIED Requirements

### Requirement: Merged Semantics Must Expose Parent State Surface

The dedicated child merged semantics contract MUST expose a minimal parent state surface so parent overview consumers do not need to reconstruct summary state from sections.

#### Scenario: Parent overview reads merged semantics state

- **GIVEN** a merged semantics contract is returned
- **WHEN** a parent overview consumer reads it
- **THEN** it MUST expose `parent_state_surface`
- **AND** the surface MUST include current intent, counts, primary entities, and latest conclusion
- **AND** the surface MUST identify the section source used to derive parent counts
- **AND** section-derived counts MUST remain coherent with `merged_sections`

