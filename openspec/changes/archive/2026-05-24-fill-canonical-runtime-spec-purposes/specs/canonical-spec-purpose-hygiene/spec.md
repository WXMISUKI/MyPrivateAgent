## ADDED Requirements

### Requirement: Canonical specs MUST document explicit purposes

Canonical OpenSpec specs MUST use explicit Purpose text that names the capability boundary and MUST NOT retain archive-generated placeholder Purpose text.

#### Scenario: Canonical spec is reviewed

- **WHEN** a canonical spec under `openspec/specs/` is used as a contract reference
- **THEN** its Purpose section explains the capability boundary without `TBD`, `created by archiving`, or `Update Purpose` placeholder text

#### Scenario: Requirement semantics are unchanged

- **WHEN** Purpose text is clarified for an existing canonical spec
- **THEN** existing Requirements and Scenarios remain the normative behavior source
