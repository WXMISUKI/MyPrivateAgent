# runtime-plane-governance-read-model Specification

## Purpose
TBD - created by archiving change add-runtime-plane-governance-read-model. Update Purpose after archive.
## Requirements
### Requirement: Runtime-plane envelopes must have a compact governance projection
The system SHALL provide a side-effect-free governance projection for runtime-plane adapter envelopes.

#### Scenario: Projection is built for a completed run
- **WHEN** an adapter has an `ExecutionRequest`, `AgentManifest`, `ExecutionEvent` list, and `ExecutionResult`
- **THEN** the projection includes request id, run id, agent id, runtime, adapter identity, result status, event count, stage counts, trace reference, and read-model boundary flags
- **AND** the projection does not include raw provider clients, Python callables, active streams, or large raw payloads

### Requirement: Projection must preserve tool and approval indicators
The system SHALL summarize tool and approval posture from normalized events and results.

#### Scenario: Tool and approval events are projected
- **WHEN** the envelope includes tool calls or an approval-required event
- **THEN** the projection includes `tool_call_count`
- **AND** it includes `approval_required = true` for approval-required events or approval-pending results
- **AND** it includes the approval tool name when available

### Requirement: Projection must remain side-effect-free
The system SHALL keep runtime-plane governance projection read-only.

#### Scenario: Adapter returns a governance projection
- **WHEN** adapter `execute(...)` returns an envelope with `governance_projection`
- **THEN** no trace, audit, approval, scheduler, checkpoint, worker, or chat state is written by the projection
- **AND** the projection reports `read_model_only = true`, `will_persist_trace = false`, `will_submit_approval = false`, and `default_chat_changed = false`

### Requirement: Reference adapters must expose the same projection shape
The system SHALL expose the same governance projection shape from Stage 1 reference adapters.

#### Scenario: Simple, tool, and approval adapters execute
- **WHEN** `simple_agent`, `tool_agent`, or `approval_agent` returns an adapter envelope
- **THEN** each envelope includes a top-level `governance_projection`
- **AND** the projection field names remain consistent across adapter types

