## MODIFIED Requirements

### Requirement: Project Must Be Positioned As Runtime Control Plane
MyPrivateAgent SHALL be positioned as an enterprise Agent Runtime Control Plane that owns governance, runtime contracts, adapter normalization, permissions, audit, observability, and business-system integration above one or more agent execution frameworks.

#### Scenario: Evaluating a mature external agent framework

- **WHEN** the team evaluates a mature external agent framework
- **THEN** the framework MUST be considered an execution engine or adapter candidate
- **AND** the project MUST preserve its own Runtime Core, Tool Runtime, Query Control, and Governance contracts as the stable boundary

#### Scenario: Explaining why the project still exists

- **WHEN** a maintainer asks whether mature external frameworks make this project unnecessary
- **THEN** the answer MUST distinguish framework execution capabilities from enterprise runtime control-plane responsibilities
- **AND** the project MUST NOT be described as a replacement implementation of LangGraph, CrewAI, Qwen-Agent, OpenAI Agents SDK, DeerFlow, or similar frameworks

### Requirement: External Frameworks Must Integrate Through Adapters
External agent frameworks SHALL integrate through explicit framework adapters that map framework-native events, tools, handoffs, runs, failures, and approvals into local runtime contracts.

#### Scenario: Adding a new framework integration

- **WHEN** a new framework integration is proposed
- **THEN** the proposal MUST name the adapter boundary, lifecycle mapping, affected runtime contracts, promotion gate, and non-goals
- **AND** the implementation MUST NOT expose framework-native raw payloads as the primary frontend or governance contract

#### Scenario: Promoting an adapter toward production use

- **WHEN** an adapter is promoted beyond a pilot
- **THEN** the adapter MUST provide evidence for readiness, failure handling, policy coordination, and governance observability
- **AND** the adapter MUST remain disabled from default main-chat execution until an explicit promotion change approves it

### Requirement: Control-plane positioning is visible from documentation entrypoints
MyPrivateAgent's official Agent Runtime Control Plane positioning SHALL be visible from repository entrypoint documentation.

#### Scenario: Reader checks project positioning

- **WHEN** a reader opens the current docs entrypoint
- **THEN** the documentation states that MyPrivateAgent owns runtime contracts, governance, permissions, audit, observability, provider contracts, and adapter normalization
- **AND** it states that external frameworks are adapter candidates rather than replacement implementations
- **AND** it states that external providers are data-plane services consumed through provider contracts rather than main-backend dependencies

### Requirement: Control Plane Must Not Expand Into Execution Platform
MyPrivateAgent SHALL NOT self-build general-purpose execution capabilities that are already available in mature frameworks.

#### Scenario: Evaluating execution capability build-vs-buy

- **WHEN** the team needs an execution capability such as graph orchestration, durable checkpointing, sandbox isolation, or parallel worker scheduling
- **THEN** the team MUST first evaluate mature frameworks or managed runtime candidates before considering self-build
- **AND** self-build is only justified when no mature framework provides the capability AND the capability is core to control-plane governance

#### Scenario: AgentHarnessFacade growth boundary

- **WHEN** a developer proposes adding production execution capabilities to AgentHarnessFacade
- **THEN** the proposal MUST be evaluated against the runtime-plane integration strategy and adapter boundary
- **AND** capabilities that belong to the execution plane MUST be implemented through framework adapter integration, not facade extension
- **AND** AgentHarnessFacade MUST remain at preview stability level for local smoke and adapter demo purposes

#### Scenario: Directory boundary enforcement

- **WHEN** new code is written for control-plane or runtime-plane functionality
- **THEN** control-plane code SHOULD be placed under `backend/control_plane/`
- **AND** runtime-plane code SHOULD be placed under `backend/runtime_plane/`
- **AND** framework-specific code SHOULD be placed under `backend/framework_adapters/`
- **AND** existing code in `backend/services/` and `backend/agent_framework/` does not need to be moved immediately, but new code should follow the new boundaries
