## ADDED Requirements

### Requirement: LangGraph controlled pilot readiness is machine-readable
The system SHALL expose a side-effect-free readiness gate for deciding whether `langgraph_draft` can enter an explicit controlled pilot smoke.

#### Scenario: LangGraph pilot readiness is ready
- **WHEN** `langgraph_draft` is registered, required package and environment evidence is present, runtime execution is enabled, external pilot is enabled, and the authoring template has Stage 1 proof mapping
- **THEN** readiness status is `ready`
- **AND** `can_start_controlled_pilot` is `true`
- **AND** `next_allowed_action` is `run_explicit_controlled_pilot_smoke`
- **AND** `will_execute`, `trace_write`, `audit_write`, and `default_chat_entry` remain disabled in the readiness check

#### Scenario: LangGraph pilot readiness is blocked by precheck
- **WHEN** package, environment, runtime, or external pilot precheck evidence is missing or disabled
- **THEN** readiness status is `blocked`
- **AND** `can_start_controlled_pilot` is `false`
- **AND** blockers include machine-readable reason codes for the failed gates
- **AND** the readiness check does not execute the adapter or call LangGraph

#### Scenario: Unknown adapter is blocked
- **WHEN** an unknown adapter id is reviewed for controlled pilot readiness
- **THEN** readiness status is `blocked`
- **AND** blockers include `adapter_not_registered`
- **AND** `can_start_controlled_pilot` is `false`

#### Scenario: Registered non-LangGraph adapter is blocked
- **WHEN** a registered adapter other than `langgraph_draft` is reviewed for LangGraph controlled pilot readiness
- **THEN** readiness status is `blocked`
- **AND** blockers include `unsupported_controlled_pilot_target`
- **AND** the result explains that this gate only covers the LangGraph draft adapter
