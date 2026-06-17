## ADDED Requirements

### Requirement: Embedded SDK and Harness Runtime Surface assembly MUST be delegated by concern
The system MUST keep Embedded SDK and Harness Runtime Surface read-model assembly behind a dedicated builder boundary so profile assembly and service wrapper methods do not directly own those contract construction details.

#### Scenario: Profile assembler delegates embedded SDK read-model assembly
- **WHEN** `RuntimeSurfaceProfileAssembler` assembles the Runtime Profile
- **THEN** it MUST delegate Embedded SDK / Harness bundle construction to the dedicated builder boundary
- **AND** it MUST preserve the existing Runtime Profile contract shape

#### Scenario: Service recovery wrappers delegate read-model construction
- **WHEN** `RuntimeSurfaceService` builds run recovery, default runtime recovery, or embedded bootstrap contracts
- **THEN** the service wrapper methods MUST remain compatible for existing backend callers
- **AND** read-model construction MUST be delegated through the dedicated Embedded SDK Runtime Surface builder
- **AND** execution and validation side effects MUST remain outside the builder boundary
