"""Recovery audit production readiness evidence."""

from __future__ import annotations

from typing import Any, Dict


RECOVERY_AUDIT_PRODUCTION_GATE_CONTRACT_VERSION = "phase-ii-recovery-audit-production-gate-v1"


def build_recovery_audit_production_readiness_contract() -> Dict[str, Any]:
    return {
        "contract_version": RECOVERY_AUDIT_PRODUCTION_GATE_CONTRACT_VERSION,
        "ready": True,
        "operation_history_supported": True,
        "audit_summary_supported": True,
        "timeline_writer_available": True,
        "idempotent_trace_dedupe": True,
        "authorization_source": False,
        "required_evidence": [
            "compact_recovery_operation_record",
            "bounded_recovery_operation_history",
            "recovery_audit_summary",
            "opt_in_recovery_audit_timeline_writer",
            "dedupe_key",
        ],
        "non_goals": [
            "no_recovery_execution_authorization",
            "no_worker_lease_validation",
            "no_default_sdk_trace_write",
        ],
    }
