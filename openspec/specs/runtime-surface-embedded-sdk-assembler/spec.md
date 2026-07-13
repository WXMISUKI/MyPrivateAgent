# runtime-surface-embedded-sdk-assembler Specification

## Purpose
Define the dedicated Runtime Surface read-model builder boundary for Embedded SDK / Harness contracts.
## Requirements
### Requirement: Embedded SDK Runtime Surface assembly MUST use a dedicated read-model builder
The system MUST assemble Runtime Surface Embedded SDK / Harness read-model contracts through a concern-specific builder boundary while preserving the existing public contract shape.

#### Scenario: Profile embedded runtime bundle is assembled through the dedicated builder
- **WHEN** `RuntimeSurfaceService.get_runtime_profile()` builds a Runtime Profile
- **THEN** `embedded_runtime_factory`, `embedded_runtime_bootstrap`, and `default_runtime_recovery` MUST be derived through the dedicated Embedded SDK Runtime Surface builder
- **AND** the returned Runtime Profile MUST preserve the existing top-level field names and nested payload semantics

#### Scenario: Dedicated bootstrap endpoint remains stable
- **WHEN** callers request the embedded runtime bootstrap contract
- **THEN** the service MUST continue returning the existing bootstrap payload shape
- **AND** bootstrap recovery validation MUST remain present when available
- **AND** the builder MUST NOT change bootstrap validation execution semantics

#### Scenario: Run recovery endpoint remains stable
- **WHEN** callers request run recovery with or without a run id
- **THEN** the service MUST continue returning the existing run recovery payload shape
- **AND** the builder MUST preserve recovery entrypoints, workspace backend projection, checkpoint, resume cursor, and continuation fields

### Requirement: Embedded SDK Runtime Surface assembly MUST remain read-model only
The dedicated builder MUST only assemble existing Runtime Surface read models and MUST NOT execute Embedded SDK, provider, recovery, worker, or chat behavior.

#### Scenario: Builder does not trigger execution behavior
- **WHEN** Runtime Surface assembles Embedded SDK / Harness contracts
- **THEN** the builder MUST NOT call provider models, run tools, resume SDK runs, submit approvals, schedule workers, write persistence state, or invoke default chat grounding
- **AND** any validation already performed by existing service methods MUST remain explicitly owned by those methods

#### Scenario: Provider and domain-agent behavior remains untouched
- **WHEN** this builder is introduced
- **THEN** provider capability invocation, domain-agent execution, GraphRAG, source binding automation, and final answer policy MUST remain unchanged

### Requirement: Governance recovery projection MUST consume stable builder outputs
Runtime Surface governance overview MUST continue projecting recovery state from stable recovery contracts without becoming the owner of Embedded SDK / Harness assembly.

#### Scenario: Governance overview recovery sections remain aligned
- **WHEN** a Runtime Profile includes `run_recovery` and `default_runtime_recovery`
- **THEN** `governance_overview.run_recovery`, `governance_overview.default_runtime_recovery`, and `governance_overview.recovery_alignment_summary` MUST preserve their existing compact shape
- **AND** the alignment summary MUST continue comparing default expected entrypoints against current run recovery entrypoints

### Requirement: Embedded SDK Runtime Surface assembly MUST expose authorization read models
The dedicated Embedded SDK Runtime Surface builder MUST expose production recovery authorization read models for default recovery posture and run-specific recovery views.

#### Scenario: Default recovery includes authorization summary
- **WHEN** Runtime Surface assembles `default_runtime_recovery`
- **THEN** the payload MUST include compact Embedded SDK production recovery authorization evidence
- **AND** the builder MUST preserve the existing recovery payload shape while adding the new authorization summary

#### Scenario: Run recovery includes authorization summary
- **WHEN** Runtime Surface assembles `run_recovery`
- **THEN** the payload MUST include compact Embedded SDK production recovery authorization evidence
- **AND** the authorization summary MUST remain separate from run-specific recoverability

#### Scenario: Builder remains read-model only
- **WHEN** Runtime Surface assembles authorization summaries
- **THEN** the builder MUST NOT execute recovery, claim ownership, submit approval, or start workers
- **AND** it MUST only project existing gate and readiness evidence into the read model

