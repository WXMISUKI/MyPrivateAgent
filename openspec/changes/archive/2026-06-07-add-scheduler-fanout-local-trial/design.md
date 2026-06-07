## Context

`SchedulerService` already has the important building blocks:

```text
prepare_execution(...)
  -> scheduler_run_id
  -> child_contexts / child_run_id
mark_child_running(...)
mark_child_completed(...)
mark_child_failed(...)
merge_child_outputs(...)
```

This change does not create a new scheduler. It adds a deterministic local trial around the existing service so the project can prove a minimal Phase A fan-out / collect / merge loop before considering real child executor dispatch.

## Goals

- Provide one local trial for scheduler fan-out readiness.
- Reuse existing scheduler service methods.
- Produce a compact `go / review / blocked` report.
- Verify `child_run_id`, `scheduler_run_id`, `merge_status`, and `merged_output`.
- Make partial failure visible and non-silent.

## Non-Goals

- Do not invoke real child executor backends.
- Do not start worker processes or sandbox adapters.
- Do not enable production dispatch.
- Do not schedule retries.
- Do not call a real LLM.
- Do not call `/api/chat`.
- Do not add frontend UI.
- Do not replace `SchedulerService`.

## Approach

Add a thin `SchedulerFanoutLocalTrialService`.

The service builds an in-memory plan and one active plan item with explicit child roles:

```text
planner + backend + frontend + qa/docs roles
```

It then:

1. Calls `SchedulerService.prepare_execution(...)`.
2. Iterates child contexts.
3. Marks each child running.
4. Applies deterministic outcomes:
   - success mode: all children completed.
   - partial-failure mode: one selected child failed, the others completed.
   - blocked mode: no valid fan-out is available.
5. Calls `SchedulerService.merge_child_outputs(...)`.
6. Builds a compact report.

## Decision Rules

- `go`: fan-out prepared, child count is at least two, all children complete, merge status is `completed`, and merged output exists.
- `review`: fan-out prepared and merge status is `partial_failed` or `incomplete`.
- `blocked`: fan-out cannot be prepared, child identifiers are missing, merge output is missing, or an unexpected exception occurs.

CLI exit code:

- `0` for `go`
- `2` for `review`
- `1` for `blocked`

## Boundary

The report must include boundary fields proving:

- dispatcher invocation is not performed
- worker startup is not performed
- sandbox backend invocation is not performed
- retry scheduler is not performed
- LLM invocation is not performed
- `/api/chat` invocation is not performed
- default runtime behavior is not changed

## Output

The report includes:

- contract version
- generated timestamp
- decision, reason code, recommended next action
- objective, item title, requested child roles
- scheduler run summary
- child summaries
- merge summary
- blockers and warnings
- boundary
