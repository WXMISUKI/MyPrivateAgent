# phase-ii-exit-gate-reassessment Specification

## Purpose
Define how Phase II exit readiness is reassessed after Runtime Surface and Query/Run closure work lands.

## Requirements
### Requirement: Phase II exit reassessment MUST produce an actionable decision
The system documentation MUST reassess Phase II using current repository evidence and MUST produce a concrete decision rather than an open-ended status report.

#### Scenario: Exit decision is explicit
- **WHEN** Phase II exit gate is reassessed
- **THEN** the assessment MUST state whether Phase II is closed, blocked by one final slice, or intentionally kept in limited closure mode
- **AND** the assessment MUST name the next allowed implementation action

#### Scenario: Evidence is repository-backed
- **WHEN** the reassessment cites completed work
- **THEN** it MUST reference current docs, canonical specs, or archived OpenSpec changes
- **AND** it MUST NOT rely on conversation memory as the durable source

### Requirement: Phase II reassessment MUST distinguish readiness evidence from production authorization
The reassessment MUST avoid treating readiness contracts as production behavior.

#### Scenario: SDK and recovery readiness remain bounded
- **WHEN** Embedded SDK recovery, worker ownership, retry, or child executor evidence is considered
- **THEN** the reassessment MUST distinguish contract/readiness coverage from production durable recovery, worker lease enforcement, automatic retry scheduling, or real child executor dispatch

#### Scenario: Provider readiness remains explicit-only
- **WHEN** provider or domain-agent evidence is considered
- **THEN** the reassessment MUST NOT treat provider management readiness as default chat grounding, GraphRAG enablement, source binding automation, or final answer policy promotion

### Requirement: Phase II reassessment MUST stop local infinite optimization
The reassessment MUST explicitly pause low-value continuation paths unless a concrete trigger appears.

#### Scenario: Paused directions are named
- **WHEN** the reassessment defines next work
- **THEN** it MUST name directions that are not default next steps
- **AND** it MUST include provider evidence piling, query workspace expansion, multi-channel history/workspace, and UI micro-polish unless they have an explicit trigger
