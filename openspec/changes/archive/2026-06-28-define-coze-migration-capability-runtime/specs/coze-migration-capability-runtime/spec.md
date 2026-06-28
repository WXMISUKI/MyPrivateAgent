## ADDED Requirements

### Requirement: Coze migration workflows must use a stable asset directory
The system SHALL use `backend/coze_workflows/<workflow_id>/` as the standard asset root for Coze workflow migrations.

Each workflow directory MUST be owned independently and MUST contain a `workflow.yaml` manifest before the workflow can be discovered by the Coze migration registry.

#### Scenario: Workflow directory is discoverable
- **WHEN** a workflow manifest exists at `backend/coze_workflows/customer_intake/workflow.yaml`
- **THEN** the Coze migration registry includes `workflow_id = customer_intake`
- **AND** the registry includes the workflow asset directory and manifest path

#### Scenario: Workflow directory without manifest is ignored
- **WHEN** a directory exists under `backend/coze_workflows/` without `workflow.yaml`
- **THEN** the registry does not expose it as a callable workflow
- **AND** the registry may include a compact warning for maintainers

### Requirement: Coze workflow manifests must declare runtime and governance metadata
The system SHALL require every Coze workflow manifest to declare stable runtime and governance metadata.

The manifest MUST include `id`, `name`, `version`, `owner`, `source`, `entrypoint`, `inputs`, `outputs`, `dependencies`, `governance`, `acceptance`, and `status`.

#### Scenario: Valid manifest is normalized
- **GIVEN** a manifest includes all required sections
- **WHEN** the Coze migration registry is built
- **THEN** the workflow contract includes normalized identity, version, owner, source, entrypoint, schemas, dependencies, governance, acceptance, and status
- **AND** the workflow readiness is `ready` only when required dependencies and acceptance references are valid

#### Scenario: Missing required manifest field fails closed
- **GIVEN** a manifest is missing `owner`
- **WHEN** the Coze migration registry is built
- **THEN** the workflow is marked `invalid`
- **AND** the registry includes a machine-readable missing field error
- **AND** the workflow is not callable

### Requirement: Prompt assets must be referenced, not embedded in the manifest
The system SHALL keep workflow prompt bodies in prompt files and reference them from `workflow.yaml`.

#### Scenario: Prompt files are referenced
- **GIVEN** `workflow.yaml` references `prompts/system.md` and `prompts/task.md`
- **WHEN** the workflow contract is normalized
- **THEN** the contract includes prompt asset references
- **AND** the contract does not inline the full prompt body into the registry list response

### Requirement: Dependencies must be explicit
The system SHALL require Coze migration workflows to declare tool, MCP capability, Skill, provider, and knowledge-source dependencies explicitly.

#### Scenario: Dependency readiness is summarized
- **WHEN** a workflow declares `dependencies.tools`, `dependencies.mcp_capabilities`, `dependencies.skills`, or `dependencies.knowledge_sources`
- **THEN** the registry returns compact dependency readiness
- **AND** missing required dependencies produce readiness blockers

#### Scenario: Hidden dependency is disallowed
- **WHEN** a workflow implementation depends on a tool or provider that is not declared in the manifest
- **THEN** the workflow MUST be treated as not production-ready during review or smoke validation

### Requirement: Coze migration registry must be side-effect free
The Coze migration registry SHALL discover and validate workflow manifests without executing workflows, invoking tools, calling models, creating runs, or mutating runtime state.

#### Scenario: Registry is inspected
- **WHEN** Runtime Surface or a developer reads the Coze migration registry
- **THEN** the system returns compact workflow contracts
- **AND** no workflow execution starts
- **AND** no `run_id` is created

### Requirement: Coze migration workflows must be invoked through a unified entrypoint
The system SHALL invoke Coze migration workflows only through a unified runtime entrypoint.

The entrypoint MUST identify workflows by `workflow_id` or a derived `capability_id`, accept a schema-validated payload, and return a provider-neutral response envelope containing `run_id`, `status`, `result`, `error`, and trace references when available.

#### Scenario: Workflow invocation creates a run identity
- **WHEN** a caller invokes a ready Coze migration workflow through the unified entrypoint
- **THEN** the response includes a `run_id`
- **AND** the response includes the workflow identity and execution status
- **AND** the execution can be associated with runtime trace records

#### Scenario: Direct implementation import is not a supported invocation path
- **WHEN** another workflow or API needs a migrated workflow capability
- **THEN** it MUST call the unified entrypoint or capability runtime contract
- **AND** it MUST NOT import another workflow directory implementation directly

### Requirement: Invocation errors must be structured
The system SHALL return stable structured errors for unknown, invalid, blocked, or dependency-unavailable Coze migration workflows.

#### Scenario: Unknown workflow is requested
- **WHEN** a caller invokes an unknown workflow id
- **THEN** the response reports a not-found error
- **AND** the error includes code `COZE_WORKFLOW_NOT_FOUND`

#### Scenario: Workflow dependencies are unavailable
- **WHEN** a workflow has missing required dependencies
- **THEN** invocation is blocked before execution
- **AND** the error includes code `COZE_WORKFLOW_DEPENDENCY_UNAVAILABLE`

### Requirement: Migration acceptance examples must be declared
The system SHALL require migrated Coze workflows to declare acceptance examples before they can be promoted beyond draft or review status.

#### Scenario: Acceptance examples are listed
- **WHEN** a workflow manifest declares `acceptance.examples`
- **THEN** the registry includes the example ids and file paths
- **AND** the workflow readiness can report whether required example files exist

#### Scenario: Missing acceptance examples block promotion
- **WHEN** a workflow is marked `active` but has no acceptance examples
- **THEN** the registry reports a readiness blocker
- **AND** the workflow MUST NOT be treated as production-ready

### Requirement: Workflow status must support collaboration lifecycle
The system SHALL support workflow statuses `draft`, `review`, `active`, `deprecated`, and `archived`.

#### Scenario: Draft workflow is visible but not callable by default
- **WHEN** a workflow status is `draft`
- **THEN** the registry exposes it for maintainers
- **AND** default invocation is blocked unless an explicit development mode allows it

#### Scenario: Active workflow is callable when dependencies are ready
- **WHEN** a workflow status is `active`
- **AND** required dependencies and acceptance examples are valid
- **THEN** the workflow may be invoked through the unified entrypoint

### Requirement: Coze migration governance must be traceable
The system SHALL attach Coze migration workflow invocations to Runtime Core trace and governance contracts.

#### Scenario: Invocation emits traceable workflow metadata
- **WHEN** a Coze migration workflow runs
- **THEN** trace metadata includes `workflow_id`, `workflow_version`, `owner`, `source = coze_migration`, and dependency summary
- **AND** governance consumers can distinguish migrated workflow execution from normal chat execution

### Requirement: External workflow executors must be adapter candidates only
The system SHALL treat LangGraph, CrewAI, OpenAI Agents SDK, Dify exports, or other external workflow engines as adapter candidates rather than control-plane truth sources.

#### Scenario: Workflow uses an external executor
- **WHEN** a workflow manifest declares an external executor adapter
- **THEN** the adapter output MUST be mapped back to local run, event, result, error, and governance contracts
- **AND** frontend governance consumers MUST NOT depend on framework-native raw payloads
