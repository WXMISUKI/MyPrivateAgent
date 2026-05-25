# Design: SDK Auto-Claim Enablement Gate Enforcement

## SDK Surface

`EmbeddedAgentRuntimeSDK` gains explicit constructor options:

- `worker_ownership_auto_claim_gate_enforced: bool = False`
- `worker_ownership_auto_claim_production_gate_ready: bool = False`
- `worker_ownership_auto_claim_idempotency_evidence_ready: bool = False`
- `worker_ownership_auto_claim_audit_evidence_ready: bool = False`
- `worker_ownership_auto_claim_rollout_decision_recorded: bool = False`

These are deliberately verbose and default-false so callers cannot accidentally treat opt-in auto-claim as production-safe.

## Enforcement

When no descriptor/recovery ownership evidence exists:

- If `worker_ownership_auto_claim_enabled` is false, SDK preserves descriptor-evidence-only behavior.
- If auto-claim is enabled but gate enforcement is false, SDK preserves the existing legacy opt-in seam.
- If both auto-claim and gate enforcement are enabled, SDK builds `build_worker_ownership_explicit_auto_claim_enablement_gate_contract(...)`.
- A blocked gate returns worker ownership evidence with `owned = false`, `lease_status = blocked`, `reason = worker_ownership_lost`, `blocked_reason = auto_claim_enablement_gate_blocked`, and nested `auto_claim_enablement_gate`.
- A ready gate allows the existing `claim_run` call.

## Entry Points

The SDK passes the concrete recovery entrypoint to the gate:

- `submit_approval.approved`
- `resume_run.continue_loop`

Unknown or non-allowlisted entrypoints fail closed when gate enforcement is enabled.
