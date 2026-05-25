## Context

Worker ownership production rollout currently exposes readiness, operationalization, and confirmation decision evidence. The remaining ambiguity is the source of that rollout confirmation decision: operators and gates can see that a decision is missing or blocked, but not whether the missing item is a decision record, deployment artifact, change ticket, manual approval, or config-bound rollout record.

## Goals / Non-Goals

**Goals:**
- Add a side-effect-free input source contract for rollout confirmation decisions.
- Require the input source to be ready before a rollout confirmation decision can become ready.
- Expose the nested source evidence through rollout operationalization, production gate, runtime smoke, Quality Gate, and Runtime Contract Gate.
- Preserve the fail-closed default posture.

**Non-Goals:**
- No API endpoint.
- No database migration.
- No production rollout execution.
- No production default worker ownership enablement.
- No recovery auto-claim default behavior.
- No vendor-specific distributed lock adapter.

## Decisions

- Add a dedicated builder instead of folding fields into the existing decision builder. This keeps the source of the decision separate from the decision content and mirrors the vendor lock target decision input source pattern.
- Support source kinds `config`, `ops_decision_record`, `deployment_artifact`, `change_ticket`, and `manual_approval`. These cover the operational records this project already distinguishes without binding to a vendor ticketing system.
- Keep readiness strict: source kind, decision id, approver, approval time, target store mode, rollback/fallback references, renewal lifecycle reference, and auto-claim decision reference must all be present.
- Treat `sql_row_lease` and `sql_row_lease_fencing` as invalid rollout input authority. SQL row lease/fencing remains ownership storage posture, not production rollout confirmation.

## Risks / Trade-offs

- [Risk] The contract adds more evidence fields to an already large runtime summary. -> Mitigation: add fields only in existing rollout sections and normalize through existing quality gate coverage.
- [Risk] A recorded source could be mistaken for production enablement. -> Mitigation: keep `production_rollout_confirmed` and production gate readiness independent, and add non-goals plus tests that assert blocked defaults.
- [Risk] Source kind names may evolve. -> Mitigation: keep the builder side-effect-free and allow future OpenSpec slices to add source kinds without changing SDK behavior.
