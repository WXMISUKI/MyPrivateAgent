## Context

Phase H made `main_chat` the canonical baseline for query detail, query history, and query workspace. Phase I is no longer about copying that product shell into every channel; it is about deciding which channel may advance to which read-model layer.

Current truth sources already say:

- `main_chat` is the only full query workspace baseline.
- `subagent_lane` has recent summary and dedicated detail evidence, but must not jump to history/workspace.
- `external_adapter` is a recent summary candidate, but its implementation is not the default next step.
- `recent summary` should keep channel-specific builders for now while sharing a stable field set.

The gap is that these decisions are spread across roadmap, specs, and notes. A future implementation slice needs one canonical promotion record shape before resuming channel work.

## Goals / Non-Goals

**Goals:**

- Define a required promotion record for any channel implementation resume decision.
- Record current channel decisions for `main_chat`, `subagent_lane`, and `external_adapter`.
- Keep Phase I focused on boundary clarity before new channel implementation.
- Give future changes a small checklist: current layer, target layer, evidence, blockers, decision, next action, and non-goals.

**Non-Goals:**

- Implement a new recent summary, query detail, history, or workspace endpoint.
- Promote `external_adapter` into recent summary implementation.
- Promote `subagent_lane` into query history or query workspace.
- Extract a generic recent summary assembler.
- Change frontend routing, runtime profile shape, database schema, or query trace persistence.

## Decisions

1. Promotion records are spec-level evidence, not runtime payloads.

   Rationale: the decision is a planning and governance guardrail. Turning it into runtime output now would create a contract before we know which channels need operational introspection.

   Alternative considered: add promotion records to Runtime Surface. Rejected for this slice because it would mix Phase I planning semantics with runtime profile payload shape.

2. Promotion records must identify the shallowest allowed next layer.

   Rationale: this prevents a channel from moving from readiness or recent summary straight into history/workspace because an implementation detail was convenient.

   Alternative considered: record only allowed/blocked. Rejected because it does not preserve the layer-by-layer promotion rule.

3. Current `external_adapter` decision remains `spec_only`.

   Rationale: roadmap and recent summary abstraction notes both say not to default into a symmetric implementation until the resume decision is explicit.

   Alternative considered: start `external_adapter recent summary` now. Rejected because it would test implementation symmetry before the promotion record discipline is fixed.

4. Current `subagent_lane` decision blocks history/workspace.

   Rationale: it has recent summary and dedicated detail work, but history/workspace need separate decisions and must not inherit the `main_chat` shell.

## Risks / Trade-offs

- Spec-only work may feel less visible than a new UI feature -> Mitigation: keep the output concrete with canonical records and clear next allowed actions.
- Records can become stale if future changes do not update them -> Mitigation: require implementation resume decisions in `channel-promotion-gate` before future channel slices.
- Over-formalizing could slow small improvements -> Mitigation: only require records for layer promotion or implementation resume, not for purely local copy or display cleanup.
