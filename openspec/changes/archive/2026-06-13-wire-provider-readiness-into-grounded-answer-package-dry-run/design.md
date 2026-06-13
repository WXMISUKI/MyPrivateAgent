## Context

The package dry-run is downstream of the grounded-answer trial surface and upstream of any composition trial or answer generation. The trial surface already carries `provider_readiness`, so the package dry-run should preserve that compact readiness as package evidence instead of asking downstream consumers to inspect nested promotion details.

## Goals / Non-Goals

**Goals:**

- Preserve trial `provider_readiness` in the package dry-run output.
- Keep package status mapped from trial status: `go -> ready`, `review -> review`, `blocked -> blocked`.
- Include provider readiness blockers, warnings, and promotion boundaries in the bounded package.
- Keep existing package dry-run behavior compatible when older trial reports lack `provider_readiness`.

**Non-Goals:**

- No provider invocation.
- No default chat retrieval injection.
- No model call, answer generation, or answer preview.
- No GraphRAG execution.
- No source binding, memory, audit, trace, or approval mutation.

## Decisions

1. Treat `provider_readiness` as package evidence, not an authorization source.

   Rationale: authorization still belongs to promotion/trial decisions. The package only preserves the bounded input evidence for downstream composition.

2. Keep status mapping driven by trial status.

   Rationale: package dry-run is downstream; it should not re-adjudicate provider readiness and risk drifting from the trial surface.

3. Preserve compatibility for older trial reports.

   Rationale: callers that do not yet supply `provider_readiness` should continue to receive deterministic packages based on existing trial fields.

## Risks / Trade-offs

- Downstream consumers could mistake packaged readiness for answer permission -> expose promotion boundaries in the package and keep docs explicit.
- Package shape grows slightly -> add only compact provider readiness, not raw documents or provider payloads.
- If trial status and provider readiness disagree, package follows trial status -> this keeps one source of truth and avoids hidden re-evaluation.
