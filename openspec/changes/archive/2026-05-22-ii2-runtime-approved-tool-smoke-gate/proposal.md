# ii2-runtime-approved-tool-smoke-gate

## Summary

Promote the approved ToolRuntimeService execution bridge into the runtime contract smoke gate.

## Motivation

The backend now supports a full flow where a facade runtime-service tool with `permission_level = ask` pauses for SDK approval, then executes once after approval via an explicit approved policy override. This is a core runtime contract, not just a unit behavior. It should be covered by `runtime_contract_smoke.py` so quality gate artifacts can detect regressions.

## Scope

- Add a smoke check for facade + ToolRuntimeService approved ask-tool execution.
- Include a deny-with-override guard in the same smoke check.
- Update runtime contract smoke tests and docs.

## Non-Goals

- Do not add frontend checks.
- Do not execute external tools or network calls.
- Do not broaden the smoke script beyond backend runtime contracts.
