## ADDED Requirements

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
