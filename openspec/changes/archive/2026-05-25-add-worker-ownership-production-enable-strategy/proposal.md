## Why

Worker ownership production gate now explains each major blocker, but the final default enablement decision still appears as a small fail-closed flag. Operators need one machine-readable strategy contract that summarizes whether all required blocker sections are ready, whether explicit default enablement was requested, and why production ownership remains disabled.

## What Changes

- Add a read-only production default enablement strategy contract.
- Thread the strategy into `worker_ownership.production_gate.sections[name=fail_closed_default_decision]`.
- Keep production default ownership disabled unless all required sections are ready and explicit default enablement is requested.
- Extend runtime smoke and quality-gate normalization to assert the strategy evidence is present and fail-closed by default.
- Update runtime contract docs and roadmap state.

## Impact

- Affected backend contracts: `worker_ownership.production_gate`, `worker_ownership.operational_readiness`, runtime smoke summary, Runtime Contract Gate summary.
- Affected SDK behavior: none.
- Non-goals: no production default enablement, no worker start, no recovery auto-claim, no vendor lock adapter implementation, no child executor dispatch.
