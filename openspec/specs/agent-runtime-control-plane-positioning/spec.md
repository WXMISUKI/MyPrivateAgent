# agent-runtime-control-plane-positioning Specification

## Purpose

Define MyPrivateAgent's official positioning as an enterprise Agent Runtime Control Plane above pluggable external agent execution frameworks.

## Requirements

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

### Requirement: Future Planning Must Follow Spec Implementation Archive Git Gates

Framework positioning and runtime governance changes SHALL follow the project sequence of specification, implementation, archive, and git submission.

#### Scenario: Starting a runtime or adapter change

- **WHEN** a future change affects runtime contracts, read models, governance semantics, or external adapter behavior
- **THEN** the team MUST create or update an OpenSpec change before implementation
- **AND** the tasks MUST include verification, documentation sync, archive readiness, and git submission steps

#### Scenario: Completing a runtime or adapter change

- **WHEN** all implementation tasks for a runtime or adapter change are complete
- **THEN** the change MUST be archived only after canonical specs and roadmap/docs are synchronized
- **AND** git submission MUST happen after verification output and archive location are known
