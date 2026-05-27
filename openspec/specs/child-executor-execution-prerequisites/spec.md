# child-executor-execution-prerequisites Specification

## Purpose
Define the machine-readable execution prerequisites required before a delegated child run may leave the relationship seam and start a real child executor.

## Requirements
### Requirement: Child Executor Execution Prerequisites Must Be Machine-Readable
The system MUST expose a machine-readable `child_executor_execution_prerequisites` contract that states whether a delegated child run has all prerequisites needed before a real child executor can be started.

The contract MUST include:

- a contract version
- an overall status
- a boolean readiness result
- a list of requirement entries
- a list of missing requirements
- a recommended next step

Each requirement entry MUST include a stable requirement name, a status, compact evidence, and a blocker when the requirement is not ready.

#### Scenario: Prerequisites are blocked
- **WHEN** one or more required child executor execution prerequisites are missing
- **THEN** the contract MUST report a blocked status
- **AND** it MUST set readiness to false
- **AND** it MUST expose the missing requirement names and blockers
- **AND** it MUST NOT imply that a real child executor has started

#### Scenario: Prerequisites are ready
- **WHEN** executor binding, context budget, merge contract, worker backend, recovery boundary, and promotion gate prerequisites are all ready
- **THEN** the contract MUST report a ready status
- **AND** it MUST set readiness to true
- **AND** it MUST expose an empty missing requirement list

### Requirement: Child Executor Execution Prerequisites Must Be Side-Effect Free
The system MUST evaluate child executor execution prerequisites without creating child runs, starting executors, mutating persisted run state, or changing approval/recovery state.

#### Scenario: Prerequisites are evaluated
- **WHEN** a caller requests child executor execution prerequisites
- **THEN** the system MUST return prerequisite evidence
- **AND** it MUST NOT create or execute a child executor
- **AND** it MUST keep the delegated run in relationship seam mode unless a separate future executor implementation explicitly starts execution

### Requirement: Child Executor Execution Prerequisites Must Be Quality-Gated
The runtime contract smoke and quality gate summary MUST expose coverage evidence for the child executor execution prerequisites contract.

#### Scenario: Prerequisite smoke is healthy
- **WHEN** runtime contract smoke evaluates the runtime profile
- **THEN** it MUST emit child executor execution prerequisite evidence
- **AND** the quality gate summary MUST expose `child_executor_execution_prerequisites_coverage`
- **AND** missing or malformed prerequisite evidence MUST fail closed as uncovered

### Requirement: Execution Prerequisites Must Include Backend Registry Evidence
Child executor execution prerequisites MUST include backend registry evidence when reporting worker backend readiness.

#### Scenario: Worker backend blocks execution
- **WHEN** worker backend dispatch readiness is blocked by the backend registry
- **THEN** execution prerequisites MUST include `worker_backend_dispatch_ready` in `missing_requirements`
- **AND** the requirement evidence MUST include the registry backend status and blockers
- **AND** readiness MUST remain false

### Requirement: Explicit Executor Binding Opt-In Must Be Required
The system MUST require explicit executor binding opt-in before a delegated child run can be considered ready for real executor handoff.

The explicit binding readiness evidence MUST include binding status, binding source, selected backend id, adapter kind, readiness boolean, missing requirements, and non-goals.

#### Scenario: Explicit binding is missing
- **WHEN** child executor preflight has context budget, merge semantics, and worker backend evidence but no explicit executor binding opt-in
- **THEN** `child_executor_execution_prerequisites` MUST include `explicit_executor_binding_opt_in` in `missing_requirements`
- **AND** readiness MUST remain false
- **AND** the relationship seam MUST remain preserved

#### Scenario: Explicit binding is present
- **WHEN** child executor preflight includes explicit executor binding opt-in and the remaining prerequisites are ready
- **THEN** the explicit binding requirement MUST report ready
- **AND** the evidence MUST identify the opt-in source and selected backend

#### Scenario: Record-only binding is not execution authorization
- **WHEN** `delegate_binding.binding_status = bound` exists without explicit executor binding opt-in
- **THEN** the system MUST NOT treat that binding as real executor authorization
- **AND** execution and dispatch readiness MUST remain fail-closed.

### Requirement: Context Budget Policy Must Be Machine-Readable
Child executor execution prerequisites MUST expose a machine-readable context budget policy for the `child_context_budget_defined` requirement.

The policy evidence MUST include contract version, overall status, readiness boolean, budget source, normalized bounded limits, missing sections, fail-closed reason, next allowed action, and non-goals.

#### Scenario: Context budget policy is missing
- **WHEN** no child executor context budget source is available
- **THEN** `child_executor_execution_prerequisites` MUST keep `child_context_budget_defined` in `missing_requirements`
- **AND** the requirement evidence MUST expose `overall_status = blocked`
- **AND** the evidence MUST list missing budget source or bounded limit sections
- **AND** real executor dispatch MUST remain disabled

#### Scenario: Context budget policy is bounded
- **WHEN** child executor preflight includes a context budget with at least one positive bounded limit
- **THEN** the `child_context_budget_defined` requirement MUST report ready
- **AND** the policy evidence MUST expose the normalized limit and source path
- **AND** this readiness MUST NOT by itself authorize worker dispatch

#### Scenario: Context budget policy is malformed
- **WHEN** a child executor context budget object exists but does not define any supported positive bounded limit
- **THEN** the context budget policy MUST fail closed
- **AND** execution prerequisites MUST remain blocked

### Requirement: Context Budget Policy Must Be Quality-Gated
Runtime smoke, Quality Gate, and Runtime Contract Gate MUST expose coverage evidence for child executor context budget policy readiness.

#### Scenario: Context budget policy smoke is healthy
- **WHEN** runtime contract smoke evaluates child executor prerequisites
- **THEN** it MUST emit default fail-closed context budget policy evidence
- **AND** it MUST emit opt-in bounded budget policy evidence
- **AND** malformed or missing evidence MUST fail closed in the quality gate summary

### Requirement: Child Result Merge Handoff Must Be Machine-Readable
Child executor execution prerequisites MUST expose a machine-readable child result merge handoff contract for the `child_result_merge_semantics_defined` requirement.

The handoff evidence MUST include contract version, overall status, readiness boolean, merge source, normalized merge strategy, strategy support status, intent policy readiness, artifact envelope requirement, section handoff requirement, parent metadata support, replay compatibility, missing sections, next allowed action, and non-goals.

#### Scenario: Merge handoff is missing
- **WHEN** no child result merge source is available
- **THEN** `child_executor_execution_prerequisites` MUST keep `child_result_merge_semantics_defined` in `missing_requirements`
- **AND** the requirement evidence MUST expose blocked handoff status
- **AND** real executor dispatch MUST remain disabled

#### Scenario: Merge handoff is supported
- **WHEN** child executor preflight includes a supported merge strategy
- **THEN** the `child_result_merge_semantics_defined` requirement MUST report ready
- **AND** the handoff evidence MUST expose the normalized merge strategy and source path
- **AND** this readiness MUST NOT by itself authorize worker dispatch

#### Scenario: Merge handoff is unsupported
- **WHEN** child executor preflight includes an unsupported merge strategy
- **THEN** the handoff contract MUST fail closed
- **AND** execution prerequisites MUST remain blocked

### Requirement: Child Result Merge Handoff Must Be Quality-Gated
Runtime smoke, Quality Gate, Runtime Contract Gate, and snapshot guard MUST expose coverage evidence for child result merge handoff readiness.

#### Scenario: Merge handoff smoke is healthy
- **WHEN** runtime contract smoke evaluates child executor prerequisites
- **THEN** it MUST emit default fail-closed merge handoff evidence
- **AND** it MUST emit opt-in supported merge handoff evidence
- **AND** malformed or missing handoff evidence MUST fail closed in the quality gate summary

### Requirement: Executed child merge fixtures MUST satisfy execution prerequisites
Tests and integration fixtures that expect executed child executor output and merged semantics MUST provide the same explicit executor binding opt-in evidence required by the child executor execution prerequisites contract.

#### Scenario: Fixture expects executed child semantics
- **WHEN** a test fixture binds, executes, and merges an `embedded_sdk_worker` child executor output
- **AND** it asserts executed merged semantics such as `risk_review`
- **THEN** the fixture MUST include explicit executor binding opt-in evidence
- **AND** the execution gate MUST remain fail-closed when that evidence is absent

#### Scenario: Missing opt-in remains blocked
- **WHEN** a child executor payload omits explicit executor binding opt-in evidence
- **THEN** the execution prerequisites MUST continue to block execution
- **AND** Runtime Surface consumers MUST NOT treat the blocked merge as executed child semantics
