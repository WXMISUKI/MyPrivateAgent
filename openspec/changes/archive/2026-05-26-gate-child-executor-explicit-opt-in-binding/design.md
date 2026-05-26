## Context

The current child executor path has several layers: preflight, promotion gate, routing, record-only binding, skeleton execution, merge, sandbox backend adapter gate, and dispatch contract. The relationship seam is intentionally conservative, but skeleton execution can currently occur once routing creates a bound record. This change adds an explicit opt-in binding requirement so record-only relationship binding is not treated as real executor authorization.

## Goals / Non-Goals

**Goals:**

- Represent explicit executor opt-in as machine-readable readiness evidence.
- Keep default child executor behavior blocked and relationship-only.
- Require explicit opt-in before skeleton execution or dispatch readiness can be considered.
- Gate the new evidence through smoke, Quality Gate, Runtime Contract Gate, and Snapshot.

**Non-Goals:**

- No real worker runtime implementation.
- No queue, sandbox process, remote executor, or default dispatcher enablement.
- No context budget enforcement beyond checking explicit evidence.
- No parent merge handoff redesign.

## Decisions

- Add explicit opt-in as a prerequisite rather than reusing `binding_status = bound`.
  - Rationale: existing binding is record-only and useful for relationship trace. Treating it as execution authorization would blur semantics.
  - Alternative considered: rename existing binding. Rejected because it would create a broad compatibility churn.

- Accept explicit opt-in from payload or metadata fields.
  - Rationale: SDK callers and future runtime config consumers can both provide the same machine-readable signal.
  - Supported fields: `explicit_executor_binding_opt_in`, `executor_binding_opt_in`, and metadata equivalents.

- Keep dispatch `will_dispatch = false`.
  - Rationale: this slice only proves readiness; actual worker dispatch remains separate and opt-in.

## Risks / Trade-offs

- Existing tests that assumed skeleton execution from record-only binding need explicit opt-in -> Mitigation: update tests to distinguish blocked default from opt-in execution.
- More gate fields increase summary size -> Mitigation: keep coverage compact and fail-closed.
- Opt-in could be mistaken for production authorization -> Mitigation: document that it is a readiness prerequisite only, not default worker enablement.
