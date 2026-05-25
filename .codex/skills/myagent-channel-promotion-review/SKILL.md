---
name: myagent-channel-promotion-review
description: Review MyPrivateAgent query channel promotion readiness and choose the allowed next layer. Use when evaluating main_chat, subagent_lane, external_adapter, or a new query channel for recent summary, query detail, query history, or query workspace promotion.
---

# MyPrivateAgent Channel Promotion Review

Use this skill when deciding whether a query channel may advance from readiness to `recent summary`, `query detail`, `query history`, or `query workspace`.

## Truth Sources

Read these first, in order:

1. `openspec/specs/channel-promotion-gate/spec.md`
2. `openspec/specs/query-workspace-generalization/spec.md`
3. `openspec/specs/query-run-read-model/spec.md`
4. `docs/architecture/runtime_contracts.md`
5. `docs/architecture/recent_summary_abstraction_note.md`
6. `docs/roadmap/next_phase_hardening.md`

If an active OpenSpec change exists for the channel, read it before recommending implementation.

## Review Workflow

1. Identify the channel:
   - Known channels: `main_chat`, `subagent_lane`, `external_adapter`
   - For new channels, first classify the runtime source, lifecycle stages, and stable identity fields.
2. Determine the current layer:
   - `readiness`
   - `recent_summary`
   - `query_detail`
   - `query_history`
   - `query_workspace`
3. Apply promotion gates in order:
   - Do not skip layers.
   - Do not copy the `main_chat` workspace shell into another channel.
   - Do not promote to history/workspace without a dedicated detail contract.
4. Check minimum readiness:
   - Stable `query_id`
   - Stable lifecycle or latest-stage summary semantics
   - Backend read model exists or is proposed
   - Frontend does not need to infer query identity from raw timeline events
5. Decide whether a new OpenSpec change is required:
   - Required for new contracts, new read models, new governance views, or semantic changes.
   - Not required for documentation-only status clarification under existing specs.
6. State the next slice:
   - Current allowed layer
   - Blocked layers and reasons
   - Affected backend/frontend/docs paths
   - Minimal verification command

## Current Baseline

- `main_chat`: canonical baseline; current layer is `query_workspace`.
- `subagent_lane`: has recent summary and dedicated query detail; still must not jump to history/workspace without a separate change.
- `external_adapter`: recent summary candidate; do not promote to detail/history/workspace until a real summary sample and detail readiness exist.

## Output Shape

Return a concise review:

```text
Channel: <channel>
Current layer: <layer>
Allowed next step: <step>
Blocked layers: <layers and reasons>
OpenSpec required: <yes/no, why>
Implementation slice: <smallest safe slice>
Verification: <focused command or docs-only check>
```

## Stop Rules

- Stop at documentation/spec review when channel boundaries are still unclear.
- Stop before implementation when the next step would introduce a contract or read model without an OpenSpec change.
- Prefer one channel and one layer per slice.
