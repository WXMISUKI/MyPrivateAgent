# Design

## Boundary

This change surfaces existing coverage fields. It does not add new runtime contract sections or change recovery behavior.

## Coverage Labels

Governance Timeline compact summaries read:

- `runtime_contract_summary.recovery_retry_scheduler_coverage.scheduler_smoke`
- `runtime_contract_summary.durable_recovery_loader_coverage.loader_smoke`

Labels follow existing runtime contract warning behavior:

- status `unknown` -> `unknown`
- smoke flag true -> `covered`
- missing or false evidence -> `missing`

## Trace Payload

Health Router degraded trace payloads must preserve normalized `durable_recovery_loader_coverage` so persisted governance events match live Runtime Profile summaries.

## Failure Mode

Legacy or malformed coverage objects fail closed to false smoke flags. Existing retry evidence, checkpoint cursor, and child executor labels remain unchanged.
