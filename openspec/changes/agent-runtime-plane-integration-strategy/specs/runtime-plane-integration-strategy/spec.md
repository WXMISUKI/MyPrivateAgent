## ADDED Requirements

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
