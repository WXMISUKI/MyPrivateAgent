# Proposal: Add Child Executor Context Budget Policy Contract

## Summary
Add a machine-readable, side-effect-free child executor context budget policy contract and wire it into child executor preflight, execution prerequisites, runtime smoke, quality gate, runtime contract gate, and snapshot evidence.

## Motivation
The explicit child executor opt-in binding gate now prevents record-only delegate binding from becoming execution authorization. The next prerequisite that still reads too loosely is `child_context_budget_defined`: today it can behave like a coarse presence check instead of explaining whether the selected context budget has bounded limits that a real executor handoff could honor.

This change keeps real child executor dispatch disabled by default, but makes the context budget blocker precise enough for future dispatcher and merge handoff work.

## Scope
- Add a read-only context budget policy builder for child executor preflight and execution prerequisites.
- Preserve existing requirement names while replacing opaque evidence with normalized policy evidence.
- Fail closed when no budget source or bounded budget limit is present.
- Extend runtime smoke and quality gate coverage to prove the default profile is blocked while an explicit opt-in sample with bounded budget is ready for this prerequisite.
- Update canonical specs and runtime docs.

## Non-Goals
- Do not start a real child executor.
- Do not add queue, sandbox, worker, or remote executor dispatch behavior.
- Do not enforce token accounting, scheduler cancellation, or runtime preemption.
- Do not change SDK recovery defaults or child result merge execution.
