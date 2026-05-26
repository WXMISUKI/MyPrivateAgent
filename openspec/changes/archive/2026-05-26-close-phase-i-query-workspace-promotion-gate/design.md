## Context

Phase I introduced a layered promotion model for query capabilities:

1. `recent summary`
2. `query detail`
3. `query history`
4. `query workspace`

The current channel state is now stable enough to close the phase:

- `main_chat` is the only full query workspace baseline.
- `subagent_lane` has recent summary and dedicated query detail, but must not advance to history/workspace without a new decision.
- `external_adapter` has recent summary only, and must not advance to detail/history/workspace without a new decision.
- Recent summary abstraction remains intentionally channel-specific.

## Goals / Non-Goals

**Goals:**

- Make Phase I closure explicit in specs and docs.
- Preserve the current channel promotion map as the default baseline.
- Define the rule for reopening deeper channel work.
- Point the roadmap toward Phase II implementation work.

**Non-Goals:**

- No code changes.
- No new Runtime Surface field.
- No new endpoint.
- No frontend changes.
- No generic read-model abstraction.

## Decisions

1. Phase I closes at the promotion-boundary level, not at full multi-channel workspace parity.

   Rationale: forcing parity would incorrectly push `subagent_lane` and `external_adapter` into history/workspace before their readiness supports it.

2. Future channel work must reopen with a dedicated promotion decision.

   Rationale: this keeps new implementation slices from using current momentum to skip layers.

3. Phase II becomes the default next planning frame.

   Rationale: roadmap already identifies runtime-core recovery implementation and delivery-surface slimming as the next higher-value direction once Phase I stops expanding channels.

## Risks / Trade-offs

- Closing Phase I may feel like stopping before every channel is feature-complete -> Mitigation: document that closure means boundary completion, not channel parity.
- Future agents may restart channel expansion by habit -> Mitigation: put the reopen rule in both OpenSpec and roadmap.
- Docs-only work can drift from implementation -> Mitigation: validate specs strictly and keep the closure note concise enough to remain maintainable.
