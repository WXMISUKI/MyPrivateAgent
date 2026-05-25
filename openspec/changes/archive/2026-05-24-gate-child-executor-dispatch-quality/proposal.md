# Gate Child Executor Dispatch Quality

## Summary
Add runtime contract smoke and quality gate coverage for `child_executor_dispatch_contract`.

## Problem
`child_executor_dispatch_contract` is now exposed by the SDK and Runtime Surface, but the quality gate artifact does not yet summarize or fail-closed on its presence. A regression could drop dispatch readiness evidence while the Runtime Profile shell still exists.

## Goals
- Add a runtime contract smoke check for `child_executor_dispatch_contract`.
- Summarize the check as `runtime_contract_summary.child_executor_dispatch_coverage`.
- Normalize the coverage in Runtime Contract Gate.
- Guard the new summary field in Runtime Contract Snapshot and artifact schema.
- Keep the default evidence blocked and side-effect free.

## Non-Goals
- Do not implement real child executor dispatch.
- Do not change backend registry readiness.
- Do not allocate workers, queues, leases, or sandbox runtimes.
- Do not change existing child run skeleton, stub, replay, or merge behavior.
