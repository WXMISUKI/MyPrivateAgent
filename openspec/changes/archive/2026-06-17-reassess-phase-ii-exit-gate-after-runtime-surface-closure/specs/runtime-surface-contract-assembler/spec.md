## ADDED Requirements

### Requirement: Runtime Surface assembler closure MUST inform Phase II exit readiness
The Phase II exit gate MUST consider completed Runtime Surface assembler closure work when deciding whether Phase II remains open.

#### Scenario: Runtime Surface closure evidence is included
- **WHEN** Phase II exit readiness is reassessed
- **THEN** Runtime Surface profile shell, profile context, runtime core, provider catalog, and Embedded SDK Runtime Surface builder extraction MUST be counted as assembler closure evidence
- **AND** remaining governance overview builder extraction MUST NOT automatically block Phase II unless it is the highest-value remaining blocker
