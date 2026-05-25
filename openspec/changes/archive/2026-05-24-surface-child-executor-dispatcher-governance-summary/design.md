# Design

## Boundary

This change only updates Governance Timeline presentation of an existing Runtime Contract Gate summary field. Backend runtime contract shape, dispatcher behavior, quality gate derivation, and snapshot guards are already in place.

## Display Rule

`formatRuntimeContractGateSummary(...)` reads `runtime_contract_summary.child_executor_dispatcher_coverage.dispatcher_smoke`:

- `overall_status = unknown` -> `child_executor_dispatcher=unknown`
- `dispatcher_smoke = true` -> `child_executor_dispatcher=covered`
- missing, non-object, or false evidence -> `child_executor_dispatcher=missing`

The label is placed immediately after `child_executor_dispatch` so operators see boundary readiness and opt-in execution coverage together.

## Failure Mode

Malformed or legacy payloads fail closed to `missing` unless the overall runtime contract status is `unknown`, matching the existing compact summary semantics.
