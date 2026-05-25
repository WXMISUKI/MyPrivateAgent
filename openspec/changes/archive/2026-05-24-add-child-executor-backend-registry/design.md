## Context

Child executor preflight currently treats `worker_runtime_backend` as ready when a payload or metadata value is present. That is useful as an early contract, but it cannot distinguish a recognized backend from arbitrary text. The execution prerequisites contract needs a backend-owned truth source before the project can safely move toward real executor binding.

## Goals / Non-Goals

**Goals:**

- Add a small in-process backend registry contract.
- Make preflight and execution prerequisites consume registry evidence.
- Keep the default runtime blocked because no real dispatch-capable backend is enabled.
- Expose registry evidence through SDK and Runtime Surface contracts.

**Non-Goals:**

- No executor dispatch.
- No sandboxing, queues, remote workers, or background scheduler.
- No database migration.

## Decisions

1. Implement a lightweight registry module in `backend/agent_framework`.

   Rationale: the seam belongs to the embedded runtime contract layer. Keeping it in `agent_framework` lets SDK, facade, Runtime Surface, and smoke tests reuse the same truth source.

2. Separate "known backend" from "dispatch ready".

   Rationale: a backend may be recognized as a future candidate while still not dispatch-ready. This keeps default behavior safe and avoids implying that `embedded_sdk_worker` can already execute real child work.

3. Add registry evidence to preflight requirement checks.

   Rationale: preflight is the existing source for promotion readiness, and execution prerequisites derive from preflight. Updating the requirement check avoids parallel readiness interpretations.

## Risks / Trade-offs

- Existing tests that used `worker_runtime_backend` as sufficient readiness may need updating -> Mitigate by asserting the new blocker and keeping behavior fail-closed.
- Registry may look like an executor implementation -> Mitigate by explicit `dispatch_ready = false` defaults and docs.
- Future executor backends may need dynamic registration -> Out of scope; start with static contract and add registration only when a real backend exists.
