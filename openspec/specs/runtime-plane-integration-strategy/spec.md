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
