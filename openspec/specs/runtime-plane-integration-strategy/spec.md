# runtime-plane-integration-strategy Specification

## Purpose

Define how MyPrivateAgent uses mature execution/runtime systems through adapters while preserving local control-plane governance and development constraints.
## Requirements
### Requirement: Control Plane Must Not Expand Into Execution Platform

MyPrivateAgent SHALL NOT self-build general-purpose execution capabilities that are already available in mature frameworks such as LangGraph, AgentRun, ADK, or OpenAI Agents SDK.

#### Scenario: Evaluating whether to build a checkpoint engine

- **WHEN** the team needs durable execution checkpointing
- **THEN** the team MUST use LangGraph's checkpointing or an equivalent mature framework capability
- **AND** the team MUST NOT build a custom checkpoint engine in MyPrivateAgent

#### Scenario: Evaluating whether to build a sandbox runtime

- **WHEN** the team needs isolated agent execution environments
- **THEN** the team MUST use AgentRun's sandbox or an equivalent managed runtime capability
- **AND** the team MUST NOT build a custom sandbox runtime in MyPrivateAgent

#### Scenario: Evaluating whether to build a worker scheduler

- **WHEN** the team needs parallel multi-agent execution scheduling
- **THEN** the team MUST use LangGraph's graph execution or an equivalent framework capability
- **AND** the team MUST NOT build a general-purpose worker scheduler in MyPrivateAgent

#### Scenario: AgentHarnessFacade expansion

- **WHEN** a developer wants to add execution capabilities to AgentHarnessFacade
- **THEN** the capability MUST be evaluated against the 10 development constraints in runtime_plane_integration_strategy.md
- **AND** capabilities that belong to the execution plane MUST be implemented as adapter integrations, not facade extensions

### Requirement: External Execution Frameworks Must Integrate Through ExecutionAdapter

External execution frameworks SHALL integrate through standardized ExecutionAdapter contracts that normalize framework-native requests, events, results, and errors into MyPrivateAgent governance-compatible envelopes.

#### Scenario: Defining an ExecutionAdapter contract

- **WHEN** a new execution framework adapter is created
- **THEN** the adapter MUST implement `translate_input()` to convert `ExecutionRequest` to framework-native format
- **AND** the adapter MUST implement `stream_events()` to convert framework-native events to `ExecutionEvent` envelopes
- **AND** the adapter MUST implement `translate_output()` to convert framework-native results to `ExecutionResult`
- **AND** none of these conversions SHALL expose Python callables, active stream iterators, or provider clients in the envelope

#### Scenario: Using a framework directly without adapter

- **WHEN** a developer wants to use LangGraph, AgentRun, or ADK capabilities
- **THEN** the developer MUST go through the corresponding adapter
- **AND** the developer MUST NOT import or call framework-native APIs directly in business logic or control-plane code

### Requirement: Domain Agents Must Be Manifest-Driven

Every agent that participates in the runtime plane SHALL have a manifest (`agent.yaml`) that declares its identity, capabilities, and governance boundaries.

#### Scenario: Creating a new agent

- **WHEN** a developer creates a new agent
- **THEN** the agent MUST have an `agent.yaml` file in `backend/domain_agents/<agent_id>/`
- **AND** the manifest MUST declare `agent_id`, `role`, `capabilities`, and governance boundaries
- **AND** the agent MUST NOT be registered in the runtime plane without a valid manifest

#### Scenario: Agent-to-agent communication

- **WHEN** one agent needs to invoke another agent's capability
- **THEN** the invocation MUST go through registry / API / tool contract
- **AND** the invocation MUST NOT directly import the other agent's internal code

### Requirement: Development Must Follow Phased Adoption

Runtime plane integration SHALL follow the four-stage adoption plan defined in runtime_plane_integration_strategy.md.

#### Scenario: Starting Stage 1 work

- **WHEN** the team begins Stage 1 (runtime plane MVP)
- **THEN** the team MUST implement exactly three vertical slices: simple_agent, tool_agent, approval_agent
- **AND** each vertical slice MUST use the same ExecutionAdapter envelope
- **AND** each agent MUST have a manifest, prompts, and minimum smoke test

#### Scenario: Promoting an adapter beyond pilot

- **WHEN** an execution adapter is ready for production use
- **THEN** the adapter MUST provide readiness evidence, failure handling, policy coordination, and governance observability
- **AND** the promotion MUST go through OpenSpec with explicit promotion gate evidence
- **AND** the adapter MUST NOT be used in default main-chat execution until promotion is approved

### Requirement: Development Constraints Must Be Enforceable

The 10 development constraints defined in runtime_plane_integration_strategy.md SHALL be enforced through documentation, code review, and quality gates.

#### Scenario: New capability proposal

- **WHEN** a developer proposes a new capability
- **THEN** the proposal MUST identify which of the 10 constraints applies
- **AND** the proposal MUST specify whether the capability belongs to control_plane, runtime_plane, framework_adapters, domain_agents, or capability_runtime
- **AND** if the capability violates a constraint, the proposal MUST include a formal exception justification

#### Scenario: Quality gate check

- **WHEN** a code change is submitted
- **THEN** the quality gate SHOULD verify that new agents have manifests
- **AND** the quality gate SHOULD verify that framework usage goes through adapters
- **AND** the quality gate SHOULD verify that control-plane code does not import framework-native execution APIs

### Requirement: Runtime plane integration strategy must be explicit
The system MUST define a runtime-plane integration strategy that explains how mature execution/runtime systems are used through adapters while MyPrivateAgent retains control-plane ownership.

#### Scenario: Team plans new runtime work
- **WHEN** the team starts runtime-related work beyond a simple bug fix
- **THEN** the project MUST have an explicit runtime-plane strategy that names the runtime candidates, adapter boundary, and control-plane responsibilities

#### Scenario: Strategy is reviewed by a maintainer
- **WHEN** a maintainer asks how the project uses AgentRun or LangGraph
- **THEN** the answer MUST distinguish runtime-plane ownership from control-plane ownership

### Requirement: Runtime integrations must use normalized execution envelopes
The system MUST normalize external runtime requests, events, results, interruptions, and errors into a stable execution envelope before those signals reach governance or front-end consumers.

#### Scenario: External framework emits native events
- **WHEN** a runtime integration produces framework-native events or errors
- **THEN** the integration MUST map them into the local execution envelope
- **AND** the governance surface MUST consume the normalized contract rather than the framework-native payload

#### Scenario: Approval interrupt is emitted by runtime
- **WHEN** an external runtime interrupts execution for approval
- **THEN** the event MUST be represented as a normalized approval interrupt in the local contract
- **AND** the approval decision MUST remain replayable

#### Scenario: Runtime Surface exposes projection readiness
- **WHEN** Runtime Surface exposes runtime-plane governance visibility
- **THEN** it MUST consume the normalized projection contract rather than adapter-native state
- **AND** it MUST remain read-only until a later change explicitly adds trace persistence or approval submission

### Requirement: Runtime plane and control plane must have distinct ownership boundaries
The system MUST keep runtime-plane and control-plane responsibilities distinct in architecture, code organization, and documentation.

#### Scenario: New code is added
- **WHEN** new code is written for control-plane or runtime-plane behavior
- **THEN** control-plane code MUST be placed under `backend/control_plane/`
- **AND** runtime-plane code MUST be placed under `backend/runtime_plane/`
- **AND** framework-specific code MUST be placed under `backend/framework_adapters/`

#### Scenario: Team updates architecture docs
- **WHEN** architecture docs are updated for runtime work
- **THEN** the docs MUST clearly say what belongs to control plane, runtime plane, adapter layer, domain agents, and capability runtime

### Requirement: Runtime plane development must be stage-gated
The system MUST use stage-gated runtime development so that each stage has a bounded scope, a review point, and a stop condition.

#### Scenario: Stage 0 freeze
- **WHEN** the project enters the freeze-and-align stage
- **THEN** the team MUST stop expanding local harness/runtime helpers into a production execution platform
- **AND** the docs MUST record the stage stop condition

#### Scenario: Stage 1 runtime slice
- **WHEN** the first runtime-plane slice is implemented
- **THEN** it MUST be a minimal adapter-backed slice
- **AND** it MUST not expand into a full platform rewrite

#### Scenario: Stage 1 approval-agent slice
- **WHEN** the approval-agent slice is implemented
- **THEN** it MUST normalize high-risk tool intent into an approval-pending envelope
- **AND** it MUST not execute the high-risk tool, submit production approval, resume execution, or change default chat behavior

### Requirement: Runtime plane must not become a hidden platform clone
The system MUST prevent the runtime plane from growing into a self-built replacement for mature orchestration and runtime platforms.

#### Scenario: Capability build-vs-buy review
- **WHEN** a new runtime capability is proposed such as checkpointing, sandboxing, worker scheduling, or model gateway behavior
- **THEN** the proposal MUST first evaluate mature runtime candidates before self-build is approved
- **AND** self-build MUST require a justification that the capability is core to control-plane governance

#### Scenario: Harness growth proposal
- **WHEN** a developer proposes extending `AgentHarnessFacade` into production runtime behavior
- **THEN** the proposal MUST be rejected unless it is explicitly scoped to preview/local smoke
- **AND** production execution behavior MUST go through the runtime-plane adapter path

### Requirement: Each stage must include a review loop
The system MUST require a written review after each runtime-plane stage so the team can verify that implementation still matches the plan.

#### Scenario: Stage is completed
- **WHEN** a runtime-plane stage completes
- **THEN** the team MUST record whether the implementation stayed within scope
- **AND** the review MUST state whether the next stage is still justified

#### Scenario: Stage drifts out of scope
- **WHEN** a runtime-plane stage starts to grow into a wider platform effort
- **THEN** the team MUST pause and return to the freeze-and-align stage
- **AND** the next task MUST be to tighten the adapter boundary or the stage definition

#### Scenario: Post-Stage-1 governance read model is added
- **WHEN** Stage 1 adapter envelopes are projected for governance visibility
- **THEN** the projection MUST remain side-effect-free and read-only
- **AND** the review MUST state that trace persistence, approval submission, Runtime Surface API wiring, and default chat changes are still out of scope

## Non-Goals

- This spec does not implement any specific framework integration (LangGraph, AgentRun, ADK, etc.).
- This spec does not move existing Python modules to new directories.
- This spec does not change the default `/api/chat` execution behavior.
- This spec does not promote AgentHarnessFacade to production execution runtime.
- This spec does not introduce a new low-code workflow builder.

## External References

- **LangGraph**: graph/state/checkpoint/human-in-loop execution semantics. [LangGraph overview](https://langchain-ai.github.io/langgraph/)
- **AgentRun**: managed runtime infrastructure, sandbox, model/tool operations, observability. [AgentRun](https://www.agentrun.cloud/)
- **ADK / A2A**: agent identity, discovery, and cross-agent boundary concepts. [Google ADK](https://google.github.io/adk-docs/)
- **OpenAI Agents SDK**: handoff, guardrail, session, tracing normalization. [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
- **Nacos Agent Registry**: namespace/version/registration/discovery. [Nacos](https://nacos.io/)
