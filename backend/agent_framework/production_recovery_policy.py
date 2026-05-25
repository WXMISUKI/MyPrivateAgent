"""Production recovery registry/checkpoint policy readiness contract."""

from __future__ import annotations

from typing import Any, Dict


PRODUCTION_RECOVERY_REGISTRY_CHECKPOINT_POLICY_VERSION = (
    "phase-ii-production-recovery-registry-checkpoint-policy-v1"
)


def build_production_recovery_registry_checkpoint_policy_contract() -> Dict[str, Any]:
    """Describe side-effect-free policy readiness for production recovery gates."""

    registry_binding_policy = {
        "requires_binding_identity": True,
        "requires_registry_resolution": True,
        "unresolved_binding_fails_closed": True,
        "callable_deserialization_allowed": False,
    }
    checkpoint_resume_cursor_policy = {
        "checkpoint_required": True,
        "resume_cursor_required": True,
        "state_gated_cursor_required": True,
        "stale_or_resolved_state_fails_closed": True,
    }
    ready = (
        registry_binding_policy["requires_binding_identity"]
        and registry_binding_policy["requires_registry_resolution"]
        and registry_binding_policy["unresolved_binding_fails_closed"]
        and not registry_binding_policy["callable_deserialization_allowed"]
        and all(value is True for value in checkpoint_resume_cursor_policy.values())
    )
    return {
        "contract_version": PRODUCTION_RECOVERY_REGISTRY_CHECKPOINT_POLICY_VERSION,
        "ready": ready,
        "registry_binding_policy_ready": True,
        "checkpoint_resume_cursor_policy_ready": True,
        "authorization_source": False,
        "registry_binding_policy": registry_binding_policy,
        "checkpoint_resume_cursor_policy": checkpoint_resume_cursor_policy,
        "required_evidence": [
            "stable_continuation_binding_identity",
            "registry_backed_reattach_resolution",
            "checkpoint_contract",
            "resume_cursor_contract",
            "state_gated_recovery_reason",
        ],
        "non_goals": [
            "no_cross_process_recovery_executor",
            "no_callable_deserialization",
            "no_default_loader_execution",
            "no_worker_lease_validation",
        ],
    }
