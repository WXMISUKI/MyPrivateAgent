## MODIFIED Requirements

### Requirement: Runtime Surface profile assembly MUST remain contract-stable
The system MUST keep `RuntimeSurfaceService.get_runtime_profile()` externally stable while allowing its internal assembly logic to be refactored into dedicated assembler or builder boundaries. The top-level profile shell assembler SHALL live behind a dedicated module boundary once extracted, while preserving compatibility for existing internal imports during the transition.

#### Scenario: Stable profile shape
- **WHEN** clients call `get_runtime_profile()`
- **THEN** the returned profile MUST preserve the existing top-level contract shape
- **AND** the refactor MUST NOT require frontend or API consumers to change their payload interpretation

#### Scenario: Internal assembly refactor
- **WHEN** backend maintainers extract runtime profile assembly into a dedicated assembler
- **THEN** the assembler MAY reorganize internal helper boundaries
- **AND** the service MUST continue to present the same runtime profile contract

#### Scenario: Dedicated profile shell module
- **WHEN** the top-level runtime profile shell assembler is extracted
- **THEN** `RuntimeSurfaceService.get_runtime_profile()` MUST delegate through the dedicated assembler module
- **AND** compatibility imports MAY remain for existing backend callers
- **AND** the extracted module MUST NOT introduce new public payload fields by itself
