## ADDED Requirements

### Requirement: Approval agent adapter must normalize high-risk tool intent
The system SHALL provide a runtime-plane approval agent adapter that converts high-risk or approval-required tool intent into a normalized approval interrupt envelope.

#### Scenario: High-risk tool call requires approval
- **WHEN** an approval agent model response contains a tool call for a tool with `risk_level = high` or `permission_level = ask`
- **THEN** the adapter emits an `ExecutionEvent` with `stage = approval` and `type = approval_required`
- **AND** the adapter returns an `ExecutionResult` with `status = approval_pending`
- **AND** the high-risk tool handler is not executed

### Requirement: Approval interrupt metadata must stay compact
The system SHALL expose only compact approval metadata through the runtime-plane envelope.

#### Scenario: Approval metadata is inspected
- **WHEN** a governance consumer reads the approval event metadata
- **THEN** the metadata includes request id, agent id, tool name, risk level, permission level, and approval reason
- **AND** the metadata does not include Python callables, provider clients, active streams, or large raw payloads

### Requirement: Approval agent adapter must stay side-effect-free
The system SHALL keep the approval agent adapter side-effect-free with respect to production approval and chat execution.

#### Scenario: Approval pending result is produced
- **WHEN** the adapter returns `approval_pending`
- **THEN** it does not call `ApprovalEngineService`
- **AND** it does not write trace, audit, scheduler, checkpoint, or worker state
- **AND** it does not modify default `/api/chat` behavior

### Requirement: Approval agent adapter must expose conservative health
The system SHALL expose conservative health and execution readiness for the approval agent adapter.

#### Scenario: Adapter has no approval-capable tools
- **WHEN** the adapter is constructed without a high-risk or approval-required tool
- **THEN** `health_check()` reports `blocked`
- **AND** `can_execute()` returns false with a machine-readable reason
