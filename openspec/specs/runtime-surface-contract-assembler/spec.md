# runtime-surface-contract-assembler Specification

## Purpose
Define how Runtime Surface assembles contract sections into a stable profile for frontend and governance consumers.
## Requirements
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

### Requirement: Runtime Surface profile context assembly MUST be concern-specific
The system MUST keep Runtime Surface profile input context, runtime scope construction, and recovery target derivation behind a concern-specific assembler boundary while preserving the public Runtime Profile contract.

#### Scenario: Runtime scope is assembled through the profile context boundary
- **WHEN** `RuntimeSurfaceProfileAssembler` builds a runtime profile for a scoped request
- **THEN** it MUST obtain the runtime scope through the dedicated profile context assembler boundary
- **AND** the returned profile MUST preserve the existing `runtime_core`, `governance_overview`, and `run_recovery` payload shape

#### Scenario: Recovery target precedence remains stable
- **WHEN** a scoped runtime profile includes multiple possible run identifiers
- **THEN** the recovery target MUST continue to prefer `parent_run_id`
- **AND** it MUST fall back to `runtime_scope.scheduler_run_id`
- **AND** it MUST finally fall back to `runtime_scope.run_id`

#### Scenario: Context assembler does not become a profile shell
- **WHEN** the context assembler is changed
- **THEN** it MUST NOT add or remove public Runtime Profile fields by itself
- **AND** it MUST NOT assemble child executor, provider catalog, governance overview, or embedded runtime contracts

### Requirement: Runtime Core contract assembly MUST use a concern-specific builder
The system MUST assemble the Runtime Surface `runtime_core` contract through a concern-specific builder boundary while preserving the public Runtime Profile contract.

#### Scenario: Runtime Core builder preserves default shell
- **WHEN** Runtime Surface assembles a profile without runtime scope
- **THEN** the `runtime_core` contract MUST keep its existing default fields and values
- **AND** the profile payload shape MUST remain unchanged for frontend and governance consumers

#### Scenario: Runtime Core builder preserves scoped overlay
- **WHEN** Runtime Surface assembles a profile with runtime scope
- **THEN** the builder MUST preserve `run_id`, `parent_run_id`, `child_run_id`, `child_display_id`, `scheduler_run_id`, `run_kind`, `status`, `trace_count`, and `latest_trace_event`
- **AND** `child_display_id` MUST continue to fall back to `child_run_id` when an explicit display id is absent

#### Scenario: Runtime Core builder preserves child merge evidence
- **WHEN** runtime scope includes child merge state or section evidence
- **THEN** the builder MUST preserve the existing child merge fields in `runtime_core`
- **AND** it MUST NOT reinterpret those fields as query lifecycle identifiers

#### Scenario: Service wrapper remains compatible
- **WHEN** existing backend callers invoke `RuntimeSurfaceService._build_runtime_core_contract()`
- **THEN** the method MUST continue to return the same contract shape
- **AND** it MUST delegate to the dedicated Runtime Core builder

### Requirement: Governance overview run-state assembly MUST be decomposable before full overview extraction
The system MUST allow the `governance_overview.run` section to be extracted into a dedicated builder without requiring the full governance overview contract to move at the same time.

#### Scenario: Run section is extracted independently
- **WHEN** maintainers refactor Runtime Surface governance overview assembly
- **THEN** they MAY extract `governance_overview.run` as an independent concern-specific builder
- **AND** the full governance overview shell MUST preserve existing recovery, child executor, approval, audit, and main chat sections

### Requirement: Runtime contracts can reference PromptOps visibility
Runtime contract documentation and read models SHALL be able to reference PromptOps as governance visibility without treating it as a behavior-affecting runtime dependency.

#### Scenario: PromptOps is available as governance metadata
- **WHEN** runtime contract consumers inspect agent behavior governance
- **THEN** PromptOps visibility can explain prompt version, activation status, eval binding, grounding policy reference, and rollback metadata
- **AND** default chat execution remains governed by the existing prompt injection path until a later eval-backed promotion change
