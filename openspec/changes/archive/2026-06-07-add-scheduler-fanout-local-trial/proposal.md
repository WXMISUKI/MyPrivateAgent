## Why

The local knowledge-provider path is now usable and has a doctor entrypoint. The next project-level priority should return to Runtime Core: proving that MyPrivateAgent can run a minimal parent/child scheduler loop in a deterministic local trial.

Existing `SchedulerService` already supports fan-out, child run state, trace/audit events, and merge. The gap is a repeatable trial report that verifies those pieces as one local runtime slice without enabling production dispatch or real workers.

## What Changes

- Add a local scheduler fan-out trial that creates an in-memory plan item, prepares child runs, applies deterministic child outcomes, merges them back to the parent, and returns a compact report.
- Cover `go`, `review`, and `blocked` decisions:
  - `go`: all child runs complete and merge is completed.
  - `review`: at least one child fails but merge produces a partial result.
  - `blocked`: no valid fan-out can be prepared.
- Add a CLI command for local verification.
- Keep the trial side-effect constrained: no production child executor dispatch, no worker startup, no sandbox backend invocation, no retry scheduler, no real LLM call, no `/api/chat` behavior change, and no frontend UI.

## Capabilities

### New Capabilities

- `scheduler-fanout-local-trial`: deterministic local trial for SchedulerService fan-out / collect / merge.

### Modified Capabilities

- None.

## Impact

- Affected code:
  - new service under `backend/services/`
  - new script under `backend/scripts/`
- Affected tests:
  - focused unit tests for success, partial failure, blocked input, boundary, and CLI exit codes
- Affected docs:
  - runtime/scheduler roadmap notes
- No default chat, production dispatcher, worker, retry scheduler, or frontend behavior changes.
