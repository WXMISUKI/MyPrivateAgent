# Gate Recovery Retry Evidence Quality

## Summary
Add runtime contract smoke and quality gate coverage for explicit recovery retry evidence.

## Problem
SDK recovery entrypoints can now record compact retry evidence when callers pass explicit retry attempt metadata, but the runtime contract quality artifact does not yet prove or summarize that path. A regression could silently drop retry evidence from fail-closed recovery operations while retry policy still advertises evidence support.

## Goals
- Add a runtime contract smoke check for `recovery_retry_evidence`.
- Summarize the check as `runtime_contract_summary.recovery_retry_evidence_coverage`.
- Normalize the coverage in Runtime Contract Gate for new and legacy quality reports.
- Guard the new summary field in Runtime Contract Snapshot and artifact schema.
- Preserve the current non-executable retry posture.

## Non-Goals
- Do not implement automatic retry scheduling or execution.
- Do not change retry policy `implemented = false`.
- Do not introduce a second retry event model.
- Do not change worker ownership enforcement semantics.
