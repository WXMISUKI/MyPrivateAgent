# Proposal: Add Child Result Merge Handoff Contract

## Summary
Add a machine-readable, side-effect-free child result merge handoff contract and wire it into child executor preflight, execution prerequisites, runtime smoke, quality gate, runtime contract gate, and snapshot evidence.

## Motivation
The child executor path now has explicit opt-in binding and bounded context budget policy evidence. The remaining pre-execution prerequisite that is still too coarse is `child_result_merge_semantics_defined`: it currently accepts merge strategy presence but does not explain whether the parent merge handoff has a supported strategy, intent policy, artifact envelope expectations, section requirements, and replay/parent metadata compatibility.

This change keeps child execution and dispatch defaults unchanged, but makes merge handoff readiness precise enough for future result merge and real executor work.

## Scope
- Add a read-only child result merge handoff contract.
- Preserve the stable `child_result_merge_semantics_defined` requirement name.
- Fail closed when merge strategy is missing, unsupported, or does not map to known handoff behavior.
- Expose default blocked and opt-in ready merge handoff evidence in runtime smoke and quality gates.
- Update canonical specs and runtime docs.

## Non-Goals
- Do not start a real child executor.
- Do not change merge execution behavior for existing skeleton outputs.
- Do not add a new API endpoint.
- Do not implement remote worker result streaming or durable merge replay execution.
