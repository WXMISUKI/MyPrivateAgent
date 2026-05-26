# child-executor-sandbox-backend-binding Specification

## Purpose

Define the side-effect-free binding gate that proves a sandbox worker backend adapter is explicitly bound to a callable child executor dispatcher adapter before dispatch readiness can be reported.

## Requirements

### Requirement: Sandbox Backend Binding Must Explain Dispatcher Adapter Readiness

The system MUST expose a side-effect-free `child_executor_sandbox_backend_binding` contract that links sandbox backend adapter readiness to child executor dispatcher backend binding evidence.

The contract MUST report `overall_status`, `backend_id`, adapter contract readiness, dispatcher binding readiness, attempt envelope support, audit/idempotency readiness, missing sections, next allowed action, and non-goals.

#### Scenario: Default binding is blocked

- **WHEN** no explicit sandbox backend binding evidence is provided
- **THEN** the binding contract MUST report `overall_status = blocked`
- **AND** `dispatcher_binding_ready = false`
- **AND** missing sections MUST include `explicit_binding`
- **AND** it MUST NOT execute a backend adapter

#### Scenario: Ready adapter is not callable by dispatcher

- **WHEN** sandbox backend adapter contract evidence is ready
- **AND** the dispatcher backend adapter map does not contain a callable adapter for the backend id
- **THEN** the binding contract MUST report `overall_status = blocked`
- **AND** missing sections MUST include `dispatcher_backend_adapter`
- **AND** it MUST NOT treat adapter contract readiness as dispatcher binding authorization

#### Scenario: Explicit ready binding is recognized

- **WHEN** explicit binding is present
- **AND** backend registry entry and adapter contract are ready
- **AND** dispatcher backend adapter map contains a callable adapter for the backend id
- **THEN** the binding contract MUST report `overall_status = ready`
- **AND** `dispatcher_binding_ready = true`
- **AND** `attempt_envelope_supported = true`
- **AND** `audit_idempotency_ready = true`
- **AND** `will_dispatch = false`

### Requirement: Sandbox Backend Binding Coverage Must Enter Runtime Gates

Runtime smoke, Quality Gate, Runtime Contract Gate, and Snapshot MUST expose child executor sandbox backend binding coverage.

#### Scenario: Coverage is complete

- **WHEN** runtime smoke validates default blocked, missing callable, and ready opt-in binding paths
- **THEN** Quality Gate MUST expose `runtime_contract_summary.child_executor_sandbox_backend_binding_coverage.binding_smoke = true`
- **AND** Runtime Contract Gate MUST preserve normalized binding evidence
- **AND** Runtime Contract Snapshot MUST guard stable coverage fields

#### Scenario: Coverage is missing

- **WHEN** a report omits sandbox backend binding evidence
- **THEN** Quality Gate and Runtime Contract Gate MUST fail closed with `binding_smoke = false`
- **AND** Snapshot MUST degrade when required summary fields are missing
