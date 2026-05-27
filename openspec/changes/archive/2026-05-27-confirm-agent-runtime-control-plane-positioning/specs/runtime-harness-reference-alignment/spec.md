## ADDED Requirements

### Requirement: Mature Agent Frameworks Must Be Treated As Adapter Candidates

Mature agent frameworks MUST be classified as execution-engine references and adapter candidates, not as replacements for the local Runtime Core or enterprise governance control plane.

#### Scenario: Reviewing framework capabilities

- **WHEN** the team reviews LangGraph, OpenAI Agents SDK, Qwen-Agent, CrewAI, AutoGen/Microsoft Agent Framework, DeerFlow, Agno, or similar frameworks
- **THEN** the review MUST identify what can be borrowed as execution behavior, lifecycle mapping, tracing, handoff, tool execution, or adapter design
- **AND** the review MUST state what will not be copied into local runtime contracts or product positioning

#### Scenario: Using framework documentation in a proposal

- **WHEN** a proposal cites an external framework
- **THEN** it MUST map the cited framework capability into a local module such as Framework Adapter, ToolRuntimeService, Query Control Plane, Runtime Surface, Governance Timeline, or Runtime Contract Gate
- **AND** broad claims such as "use this framework directly" MUST NOT be accepted as sufficient design input

### Requirement: Local Runtime Governance Must Remain Framework-Agnostic

Runtime governance contracts MUST remain framework-agnostic so that multiple frameworks can be observed, governed, and promoted through the same local control plane.

#### Scenario: Rendering adapter status in governance UI

- **WHEN** Governance Timeline or Runtime Surface displays adapter status
- **THEN** the data MUST come from local runtime/governance contracts
- **AND** framework-specific payloads MAY only appear as compact diagnostic evidence after normalization

#### Scenario: Comparing two framework adapters

- **WHEN** two framework adapters are compared
- **THEN** the comparison MUST use local readiness, policy, trace, audit, and failure semantics
- **AND** it MUST NOT rely only on framework-native concepts or repository popularity
