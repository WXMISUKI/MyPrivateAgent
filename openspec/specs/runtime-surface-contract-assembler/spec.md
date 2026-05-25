# runtime-surface-contract-assembler Specification

## Purpose
Define how Runtime Surface assembles contract sections into a stable profile for frontend and governance consumers.
## Requirements
### Requirement: Runtime Surface profile assembly MUST remain contract-stable
The system MUST keep `RuntimeSurfaceService.get_runtime_profile()` externally stable while allowing its internal assembly logic to be refactored into dedicated assembler or builder boundaries.

#### Scenario: Stable profile shape
- **WHEN** clients call `get_runtime_profile()`
- **THEN** the returned profile MUST preserve the existing top-level contract shape
- **AND** the refactor MUST NOT require frontend or API consumers to change their payload interpretation

#### Scenario: Internal assembly refactor
- **WHEN** backend maintainers extract runtime profile assembly into a dedicated assembler
- **THEN** the assembler MAY reorganize internal helper boundaries
- **AND** the service MUST continue to present the same runtime profile contract

### Requirement: Runtime Surface profile assembly MUST be decomposable by concern
The system MUST separate runtime profile assembly concerns so model/provider aggregation, governance read models, recovery contracts, and child executor summaries can evolve independently.

#### Scenario: Concern isolation
- **WHEN** the runtime profile is assembled
- **THEN** model/provider aggregation MUST remain separable from governance read model assembly
- **AND** recovery-related contracts MUST remain separable from query/read model contracts
- **AND** child executor summary assembly MUST remain separable from main profile composition

### Requirement: Refactored runtime profile assembly MUST remain testable
The system MUST keep the runtime profile assembly path covered by focused tests after the assembler boundary is introduced.

#### Scenario: Contract regression protection
- **WHEN** the assembler boundary changes the internal implementation
- **THEN** focused backend tests MUST continue to assert the same runtime profile contract fields
- **AND** contract snapshot guards MUST continue to pass without widening the public surface unexpectedly
