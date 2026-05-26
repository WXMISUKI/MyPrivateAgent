## ADDED Requirements

### Requirement: Sandbox backend binding MUST explain dispatcher adapter readiness
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

### Requirement: Dispatch contract MUST carry sandbox backend binding evidence
Child executor dispatch contract MUST include nested sandbox backend binding evidence when sandbox backend evidence is available.

#### Scenario: Dispatch contract includes binding evidence
- **WHEN** the dispatch contract is built for a sandbox backend candidate
- **THEN** it MUST include `child_executor_sandbox_backend_binding`
- **AND** the binding MUST be preserved under `evidence.child_executor_sandbox_backend_binding`
- **AND** dispatch MUST remain blocked unless the existing promotion gate, prerequisites, backend dispatch readiness, explicit executor opt-in, and binding readiness are all ready

### Requirement: Dispatcher attempts MUST preserve binding evidence
The child executor dispatcher MUST carry compact binding evidence into dispatch attempts when provided by the dispatch contract.

#### Scenario: Dispatcher attempt includes binding evidence
- **WHEN** dispatcher receives a dispatch contract with sandbox backend binding evidence
- **THEN** the attempt MUST include `sandbox_backend_binding_status`
- **AND** it MUST include `sandbox_backend_binding_ready`
- **AND** it MUST include `sandbox_backend_binding_missing_sections`
- **AND** blocked attempts MUST remain fail-closed

### Requirement: Sandbox backend binding coverage MUST enter runtime gates
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
