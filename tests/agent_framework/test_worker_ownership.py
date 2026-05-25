from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import backend.agent_framework.worker_ownership as worker_ownership_module
from backend.database import Base
from backend.agent_framework.continuation_registry import InMemoryEmbeddedContinuationRegistry
from backend.agent_framework.persistence import InMemoryEmbeddedRunWorkspaceStore
from backend.agent_framework.recovery_operations import build_recovery_operation_record
from backend.agent_framework.runtime_dependencies import EmbeddedRuntimeDependencies, EmbeddedRuntimeFactory
from backend.models import RuntimeWorkerOwnershipRecord  # noqa: F401
from backend.agent_framework.worker_ownership import (
    InMemoryRuntimeWorkerOwnershipStore,
    PostgresAdvisoryLockExecutionSeam,
    SQLAlchemyRuntimeWorkerOwnershipStore,
    WorkerOwnershipRenewalSupervisor,
    WorkerOwnershipStoreFallback,
    WORKER_OWNERSHIP_REASON_LEASE_EXPIRED,
    WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN,
    WORKER_OWNERSHIP_REASON_WORKER_OWNERSHIP_LOST,
    WORKER_OWNERSHIP_STATUS_BLOCKED,
    WORKER_OWNERSHIP_STATUS_CLAIMED,
    WORKER_OWNERSHIP_STATUS_REFRESHED,
    WORKER_OWNERSHIP_STATUS_VALIDATED,
    build_worker_ownership_contract,
    build_worker_ownership_audit_evidence_contract,
    build_worker_ownership_auto_claim_entrypoint_allowlist_contract,
    build_worker_ownership_auto_claim_policy_contract,
    build_worker_ownership_explicit_auto_claim_enablement_gate_contract,
    build_worker_ownership_production_gate_composition_dry_run_contract,
    build_worker_ownership_production_enablement_runtime_config_consumer_contract,
    build_worker_ownership_production_enablement_strategy_contract,
    build_worker_ownership_production_default_enablement_input_source_contract,
    build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract,
    build_worker_ownership_postgres_vendor_lock_semantics_binding_contract,
    build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract,
    build_worker_ownership_postgres_rollout_artifact_consumer_contract,
    build_worker_ownership_operational_readiness_contract,
    build_worker_ownership_production_gate_contract,
    build_worker_ownership_rollout_confirmation_decision_contract,
    build_worker_ownership_rollout_confirmation_input_source_contract,
    build_worker_ownership_production_rollout_operationalization_contract,
    build_worker_ownership_renewal_supervisor_contract,
    build_worker_ownership_rollout_readiness_contract,
    build_worker_ownership_postgres_advisory_lock_execution_seam_contract,
    build_worker_ownership_postgres_vendor_lock_probe_contract,
    build_worker_ownership_vendor_lock_adapter_contract,
    build_worker_ownership_vendor_lock_target_decision_input_contract,
    build_worker_ownership_vendor_lock_semantics_contract,
    build_worker_ownership_vendor_lock_target_decision_contract,
    get_runtime_worker_ownership_store,
    set_worker_ownership_store_mode,
)


class RuntimeWorkerOwnershipTests(unittest.TestCase):
    def _store_with_clock(self):
        clock = {"now": datetime(2026, 5, 23, 9, 0, 0, tzinfo=timezone.utc)}

        def _now():
            return clock["now"]

        return InMemoryRuntimeWorkerOwnershipStore(now_fn=_now), clock

    def test_contract_declares_in_memory_lease_and_fencing_boundary(self):
        contract = build_worker_ownership_contract()

        self.assertEqual(contract["contract_version"], "phase-ii-runtime-worker-ownership-v1")
        self.assertEqual(contract["adapter_kind"], "in_memory")
        self.assertFalse(contract["durable"])
        self.assertIn("claim_run", contract["operations"])
        self.assertIn("fencing_token", contract["lease_fields"])
        self.assertTrue(contract["non_executable_payload"])

    def test_operational_readiness_marks_memory_store_as_preview(self):
        readiness = build_worker_ownership_operational_readiness_contract(
            ownership_contract=build_worker_ownership_contract(),
            store_mode="memory_only",
        )

        self.assertEqual(readiness["contract_version"], "phase-ii-worker-ownership-operations-v1")
        self.assertFalse(readiness["production_ready"])
        self.assertEqual(readiness["readiness_status"], "preview_or_degraded")
        self.assertEqual(readiness["vendor_lock_posture"], "local_preview_only")
        self.assertEqual(readiness["recovery_entry_claim_mode"], "descriptor_evidence_only")
        self.assertFalse(readiness["migration_checklist"]["migration_ready"])
        self.assertEqual(readiness["production_gate"]["overall_status"], "blocked")
        self.assertFalse(readiness["production_gate"]["production_default_enabled"])
        self.assertIn("durable_ownership_store", readiness["production_gate"]["missing_sections"])

    def test_production_gate_blocks_sql_row_lease_without_vendor_lock_and_renewal(self):
        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
        )

        self.assertEqual(gate["contract_version"], "phase-ii-worker-ownership-production-gate-v1")
        self.assertEqual(gate["overall_status"], "blocked")
        self.assertFalse(gate["ready"])
        self.assertFalse(gate["production_default_enabled"])
        self.assertIn("vendor_lock_semantics", gate["missing_sections"])
        self.assertIn("fail_closed_default_decision", gate["missing_sections"])
        self.assertIn("heartbeat_renewal_supervisor", gate["missing_sections"])
        self.assertIn("no_default_recovery_entry_auto_claim", gate["non_goals"])

    def test_production_enablement_strategy_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_production_enablement_strategy_contract(
            section_readiness={
                "durable_ownership_store": True,
                "vendor_lock_semantics": False,
            },
            production_default_enabled_requested=False,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-production-enablement-strategy-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["production_default_enabled_requested"])
        self.assertFalse(contract["production_default_allowed"])
        self.assertIn("vendor_lock_semantics", contract["blocking_sections"])
        self.assertTrue(contract["policy"]["explicit_enablement_required"])
        self.assertTrue(contract["policy"]["fail_closed_when_blocked"])
        self.assertTrue(contract["policy"]["sql_row_lease_is_not_default_authority"])
        self.assertEqual(contract["input_source"]["overall_status"], "blocked")
        self.assertIn("input_source_kind", contract["input_source"]["missing_sections"])

    def test_production_default_enablement_input_source_defaults_to_blocked(self):
        contract = build_worker_ownership_production_default_enablement_input_source_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-production-default-enablement-input-source-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["input_source_kind"], "")
        self.assertEqual(contract["target_store_mode"], "")
        self.assertFalse(contract["production_default_enablement_authorized"])
        self.assertIn("input_source_kind", contract["missing_sections"])
        self.assertIn("rollout_artifact", contract["missing_sections"])
        self.assertIn("vendor_lock_decision", contract["missing_sections"])
        self.assertIn("no_default_production_ownership_enablement", contract["non_goals"])

    def test_production_default_enablement_input_source_can_be_ready_without_enabling(self):
        contract = build_worker_ownership_production_default_enablement_input_source_contract(
            input_source_kind="rollout_artifact",
            request_id="prod-enable-001",
            requested_by="runtime-ops",
            requested_at="2026-05-25T08:10:00Z",
            target_store_mode="strict_sql",
            rollout_artifact="rollout/worker-ownership/prod-enable-001",
            vendor_lock_decision_id="vendor-lock-postgres-001",
            renewal_lifecycle_reference="renewal-lifecycle-smoke-001",
            auto_claim_decision_reference="auto-claim-policy-001",
            audit_evidence_reference="ownership-audit-001",
            rollback_plan_reference="rollback-worker-ownership-001",
            fallback_policy_reference="fallback-worker-ownership-001",
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["input_source_kind"], "rollout_artifact")
        self.assertEqual(contract["target_store_mode"], "strict_sql")
        self.assertTrue(contract["production_default_enablement_authorized"])
        self.assertEqual(contract["missing_sections"], [])
        self.assertIn("no_rollout_execution", contract["non_goals"])

    def test_postgres_rollout_artifact_consumer_defaults_to_blocked(self):
        contract = build_worker_ownership_postgres_rollout_artifact_consumer_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-postgres-rollout-artifact-consumer-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["source_kind"], "")
        self.assertEqual(contract["target_backend"], "")
        self.assertEqual(contract["lock_adapter_kind"], "")
        self.assertEqual(contract["postgres_execution_seam_status"], "blocked")
        self.assertFalse(contract["will_enable_production_default"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertIn("source_kind", contract["missing_sections"])
        self.assertIn("artifact_id", contract["missing_sections"])
        self.assertIn("postgres_execution_seam", contract["missing_sections"])
        self.assertEqual(contract["enablement_input_source"]["overall_status"], "blocked")
        self.assertIn("no_advisory_lock_execution", contract["non_goals"])

    def test_postgres_rollout_artifact_consumer_can_bridge_ready_input_source(self):
        execution_seam = build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
            executor_bound=True,
            probe_once_supported=True,
            acquire_once_supported=True,
            renew_once_supported=True,
            release_once_supported=True,
            lock_key_derivation_ready=True,
            owner_identity_required=True,
            fencing_token_required=True,
            fail_closed=True,
        )

        contract = build_worker_ownership_postgres_rollout_artifact_consumer_contract(
            artifact={
                "source_kind": "rollout_artifact",
                "artifact_id": "pg-rollout-001",
                "approved_by": "runtime-ops",
                "approved_at": "2026-05-25T08:45:00Z",
                "target_store_mode": "strict_sql",
                "target_backend": "postgres",
                "lock_adapter_kind": "postgres_advisory_lock",
                "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
                "vendor_lock_decision_id": "vendor-lock-postgres-001",
                "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
                "auto_claim_decision_reference": "auto-claim-policy-001",
                "audit_evidence_reference": "ownership-audit-001",
                "rollback_plan_reference": "rollback-worker-ownership-001",
                "fallback_policy_reference": "fallback-worker-ownership-001",
            },
            postgres_execution_seam_contract=execution_seam,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["source_kind"], "rollout_artifact")
        self.assertEqual(contract["target_store_mode"], "strict_sql")
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertEqual(contract["lock_adapter_kind"], "postgres_advisory_lock")
        self.assertEqual(contract["postgres_execution_seam_status"], "ready")
        self.assertFalse(contract["will_enable_production_default"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertEqual(contract["missing_sections"], [])
        self.assertEqual(contract["enablement_input_source"]["overall_status"], "ready")
        self.assertEqual(
            contract["enablement_input_source"]["rollout_artifact"],
            "rollout/worker-ownership/pg-rollout-001",
        )
        self.assertTrue(contract["enablement_input_source"]["ready"])

    def test_postgres_rollout_artifact_consumer_requires_ready_execution_seam(self):
        contract = build_worker_ownership_postgres_rollout_artifact_consumer_contract(
            artifact={
                "source_kind": "rollout_artifact",
                "artifact_id": "pg-rollout-001",
                "approved_by": "runtime-ops",
                "approved_at": "2026-05-25T08:45:00Z",
                "target_store_mode": "strict_sql",
                "target_backend": "postgres",
                "lock_adapter_kind": "postgres_advisory_lock",
                "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
                "vendor_lock_decision_id": "vendor-lock-postgres-001",
                "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
                "auto_claim_decision_reference": "auto-claim-policy-001",
                "audit_evidence_reference": "ownership-audit-001",
                "rollback_plan_reference": "rollback-worker-ownership-001",
                "fallback_policy_reference": "fallback-worker-ownership-001",
            },
            postgres_execution_seam_contract=PostgresAdvisoryLockExecutionSeam().contract(),
        )

        self.assertEqual(contract["overall_status"], "blocked")
        self.assertIn("postgres_execution_seam", contract["missing_sections"])
        self.assertEqual(contract["postgres_execution_seam_status"], "blocked")
        self.assertEqual(contract["enablement_input_source"]["overall_status"], "ready")
        self.assertFalse(contract["will_enable_production_default"])

    def test_postgres_vendor_lock_target_artifact_binding_defaults_to_blocked(self):
        contract = (
            build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract()
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-target-artifact-binding-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["source_kind"], "")
        self.assertEqual(contract["target_backend"], "")
        self.assertEqual(contract["lock_adapter_kind"], "")
        self.assertEqual(contract["postgres_rollout_consumer_status"], "blocked")
        self.assertFalse(contract["will_enable_production_lock"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertIn("source_kind", contract["missing_sections"])
        self.assertIn("artifact_id", contract["missing_sections"])
        self.assertIn("source_reference", contract["missing_sections"])
        self.assertIn("postgres_rollout_consumer", contract["missing_sections"])
        self.assertIn("target_decision_input", contract["missing_sections"])
        self.assertIn("target_decision", contract["missing_sections"])
        self.assertEqual(contract["target_decision_input"]["overall_status"], "blocked")
        self.assertEqual(contract["target_decision"]["overall_status"], "blocked")
        self.assertIn("no_advisory_lock_execution", contract["non_goals"])

    def test_postgres_vendor_lock_target_artifact_binding_can_build_target_decision(self):
        execution_seam = build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
            executor_bound=True,
            probe_once_supported=True,
            acquire_once_supported=True,
            renew_once_supported=True,
            release_once_supported=True,
            lock_key_derivation_ready=True,
            owner_identity_required=True,
            fencing_token_required=True,
            fail_closed=True,
        )
        artifact = {
            "source_kind": "rollout_artifact",
            "artifact_id": "pg-rollout-001",
            "approved_by": "runtime-ops",
            "approved_at": "2026-05-25T08:45:00Z",
            "target_store_mode": "strict_sql",
            "target_backend": "postgres",
            "lock_adapter_kind": "postgres_advisory_lock",
            "lock_scope": "run",
            "fencing_strategy": "fencing_token",
            "ttl_renewal_strategy": "session_ttl_renewal",
            "failover_strategy": "connection_loss_releases_lock",
            "stale_owner_cleanup_strategy": "ttl_cleanup",
            "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
            "vendor_lock_decision_id": "vendor-lock-postgres-001",
            "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
            "auto_claim_decision_reference": "auto-claim-policy-001",
            "audit_evidence_reference": "ownership-audit-001",
            "rollback_plan_reference": "rollback-worker-ownership-001",
            "fallback_policy_reference": "fallback-worker-ownership-001",
        }
        consumer = build_worker_ownership_postgres_rollout_artifact_consumer_contract(
            artifact=artifact,
            postgres_execution_seam_contract=execution_seam,
        )

        contract = build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(
            artifact=artifact,
            postgres_rollout_consumer_contract=consumer,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["source_kind"], "rollout_artifact")
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertEqual(contract["lock_adapter_kind"], "postgres_advisory_lock")
        self.assertEqual(contract["postgres_rollout_consumer_status"], "ready")
        self.assertEqual(contract["target_decision_input"]["overall_status"], "ready")
        self.assertEqual(contract["target_decision"]["overall_status"], "ready")
        self.assertTrue(contract["target_decision"]["production_lock_allowed"])
        self.assertFalse(contract["will_enable_production_lock"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertEqual(contract["missing_sections"], [])

    def test_postgres_vendor_lock_target_artifact_binding_requires_ready_consumer(self):
        artifact = {
            "source_kind": "rollout_artifact",
            "artifact_id": "pg-rollout-001",
            "approved_by": "runtime-ops",
            "approved_at": "2026-05-25T08:45:00Z",
            "target_backend": "postgres",
            "lock_adapter_kind": "postgres_advisory_lock",
            "lock_scope": "run",
            "fencing_strategy": "fencing_token",
            "ttl_renewal_strategy": "session_ttl_renewal",
            "failover_strategy": "connection_loss_releases_lock",
            "stale_owner_cleanup_strategy": "ttl_cleanup",
            "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
        }
        consumer = build_worker_ownership_postgres_rollout_artifact_consumer_contract()

        contract = build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(
            artifact=artifact,
            postgres_rollout_consumer_contract=consumer,
        )

        self.assertEqual(contract["overall_status"], "blocked")
        self.assertIn("postgres_rollout_consumer", contract["missing_sections"])
        self.assertEqual(contract["postgres_rollout_consumer_status"], "blocked")
        self.assertIn("source_kind", contract["postgres_rollout_consumer_missing_sections"])
        self.assertEqual(contract["target_decision_input"]["overall_status"], "ready")
        self.assertEqual(contract["target_decision"]["overall_status"], "ready")
        self.assertFalse(contract["will_enable_production_lock"])

    def test_postgres_vendor_lock_semantics_binding_defaults_to_blocked(self):
        contract = build_worker_ownership_postgres_vendor_lock_semantics_binding_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-semantics-binding-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["target_binding_status"], "blocked")
        self.assertEqual(contract["postgres_execution_seam_status"], "blocked")
        self.assertEqual(contract["postgres_probe_status"], "blocked")
        self.assertEqual(contract["vendor_lock_adapter_status"], "blocked")
        self.assertEqual(contract["vendor_lock_semantics_status"], "blocked")
        self.assertFalse(contract["will_enable_production_lock"])
        self.assertFalse(contract["will_update_production_gate"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertIn("target_artifact_binding", contract["missing_sections"])
        self.assertIn("postgres_execution_seam", contract["missing_sections"])
        self.assertIn("postgres_probe", contract["missing_sections"])
        self.assertIn("vendor_lock_adapter", contract["missing_sections"])
        self.assertIn("vendor_lock_semantics", contract["missing_sections"])
        self.assertIn("no_production_gate_update", contract["non_goals"])

    def test_postgres_vendor_lock_semantics_binding_builds_ready_candidate(self):
        execution_seam = build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
            executor_bound=True,
            probe_once_supported=True,
            acquire_once_supported=True,
            renew_once_supported=True,
            release_once_supported=True,
            lock_key_derivation_ready=True,
            owner_identity_required=True,
            fencing_token_required=True,
            fail_closed=True,
        )
        artifact = {
            "source_kind": "rollout_artifact",
            "artifact_id": "pg-rollout-001",
            "approved_by": "runtime-ops",
            "approved_at": "2026-05-25T08:45:00Z",
            "target_store_mode": "strict_sql",
            "target_backend": "postgres",
            "lock_adapter_kind": "postgres_advisory_lock",
            "lock_scope": "run",
            "fencing_strategy": "fencing_token",
            "ttl_renewal_strategy": "session_ttl_renewal",
            "failover_strategy": "connection_loss_releases_lock",
            "stale_owner_cleanup_strategy": "ttl_cleanup",
            "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
            "vendor_lock_decision_id": "vendor-lock-postgres-001",
            "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
            "auto_claim_decision_reference": "auto-claim-policy-001",
            "audit_evidence_reference": "ownership-audit-001",
            "rollback_plan_reference": "rollback-worker-ownership-001",
            "fallback_policy_reference": "fallback-worker-ownership-001",
        }
        consumer = build_worker_ownership_postgres_rollout_artifact_consumer_contract(
            artifact=artifact,
            postgres_execution_seam_contract=execution_seam,
        )
        target_binding = (
            build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(
                artifact=artifact,
                postgres_rollout_consumer_contract=consumer,
            )
        )

        contract = build_worker_ownership_postgres_vendor_lock_semantics_binding_contract(
            target_artifact_binding_contract=target_binding,
            postgres_execution_seam_contract=execution_seam,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["target_binding_status"], "ready")
        self.assertEqual(contract["target_decision_status"], "ready")
        self.assertEqual(contract["postgres_execution_seam_status"], "ready")
        self.assertEqual(contract["postgres_probe_status"], "ready")
        self.assertEqual(contract["vendor_lock_adapter_status"], "ready")
        self.assertEqual(contract["vendor_lock_semantics_status"], "ready")
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertEqual(contract["lock_adapter_kind"], "postgres_advisory_lock")
        self.assertEqual(contract["vendor_lock_semantics"]["overall_status"], "ready")
        self.assertTrue(contract["vendor_lock_semantics"]["production_lock_allowed"])
        self.assertFalse(contract["will_enable_production_lock"])
        self.assertFalse(contract["will_update_production_gate"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertEqual(contract["missing_sections"], [])

    def test_postgres_vendor_lock_production_gate_wiring_decision_defaults_to_blocked(self):
        contract = (
            build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract()
        )

        self.assertEqual(
            contract["contract_version"],
            (
                "phase-ii-worker-ownership-postgres-vendor-lock-production-gate"
                "-wiring-decision-v1"
            ),
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["semantics_binding_status"], "blocked")
        self.assertEqual(contract["candidate_semantics_status"], "blocked")
        self.assertFalse(contract["decision_recorded"])
        self.assertFalse(contract["wiring_allowed"])
        self.assertFalse(contract["will_update_production_gate"])
        self.assertFalse(contract["will_enable_production_lock"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertIn("semantics_binding", contract["missing_sections"])
        self.assertIn("decision_recorded", contract["missing_sections"])
        self.assertIn("production_rollout_confirmed", contract["missing_sections"])
        self.assertIn("no_default_production_gate_update", contract["non_goals"])

    def test_postgres_vendor_lock_production_gate_wiring_decision_can_be_ready(self):
        execution_seam = build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
            executor_bound=True,
            probe_once_supported=True,
            acquire_once_supported=True,
            renew_once_supported=True,
            release_once_supported=True,
            lock_key_derivation_ready=True,
            owner_identity_required=True,
            fencing_token_required=True,
            fail_closed=True,
        )
        artifact = {
            "source_kind": "rollout_artifact",
            "artifact_id": "pg-rollout-001",
            "approved_by": "runtime-ops",
            "approved_at": "2026-05-25T08:45:00Z",
            "target_store_mode": "strict_sql",
            "target_backend": "postgres",
            "lock_adapter_kind": "postgres_advisory_lock",
            "lock_scope": "run",
            "fencing_strategy": "fencing_token",
            "ttl_renewal_strategy": "session_ttl_renewal",
            "failover_strategy": "connection_loss_releases_lock",
            "stale_owner_cleanup_strategy": "ttl_cleanup",
            "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
            "vendor_lock_decision_id": "vendor-lock-postgres-001",
            "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
            "auto_claim_decision_reference": "auto-claim-policy-001",
            "audit_evidence_reference": "ownership-audit-001",
            "rollback_plan_reference": "rollback-worker-ownership-001",
            "fallback_policy_reference": "fallback-worker-ownership-001",
        }
        consumer = build_worker_ownership_postgres_rollout_artifact_consumer_contract(
            artifact=artifact,
            postgres_execution_seam_contract=execution_seam,
        )
        target_binding = (
            build_worker_ownership_postgres_vendor_lock_target_artifact_binding_contract(
                artifact=artifact,
                postgres_rollout_consumer_contract=consumer,
            )
        )
        semantics_binding = build_worker_ownership_postgres_vendor_lock_semantics_binding_contract(
            target_artifact_binding_contract=target_binding,
            postgres_execution_seam_contract=execution_seam,
        )

        contract = (
            build_worker_ownership_postgres_vendor_lock_production_gate_wiring_decision_contract(
                semantics_binding_contract=semantics_binding,
                decision_recorded=True,
                decision_id="pg-wire-001",
                approved_by="runtime-ops",
                approved_at="2026-05-25T09:30:00Z",
                production_rollout_confirmed=True,
                rollback_plan_reference="rollback-worker-ownership-001",
                fallback_policy_reference="fallback-worker-ownership-001",
            )
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["semantics_binding_status"], "ready")
        self.assertEqual(contract["candidate_semantics_status"], "ready")
        self.assertTrue(contract["decision_recorded"])
        self.assertTrue(contract["wiring_allowed"])
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertEqual(contract["lock_adapter_kind"], "postgres_advisory_lock")
        self.assertFalse(contract["will_update_production_gate"])
        self.assertFalse(contract["will_enable_production_lock"])
        self.assertFalse(contract["executes_advisory_lock"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertEqual(contract["missing_sections"], [])

    def test_production_enablement_strategy_accepts_consumer_input_without_bypassing_request(self):
        section_readiness = {
            "durable_ownership_store": True,
            "vendor_lock_semantics": True,
            "heartbeat_renewal_supervisor": True,
            "migration_checklist": True,
            "rollout_checklist": True,
            "recovery_entry_auto_claim_policy": True,
            "stale_fencing_fail_closed": True,
            "ownership_audit_evidence": True,
        }
        execution_seam = build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
            executor_bound=True,
            probe_once_supported=True,
            acquire_once_supported=True,
            renew_once_supported=True,
            release_once_supported=True,
            lock_key_derivation_ready=True,
            owner_identity_required=True,
            fencing_token_required=True,
            fail_closed=True,
        )
        consumer = build_worker_ownership_postgres_rollout_artifact_consumer_contract(
            artifact={
                "source_kind": "rollout_artifact",
                "artifact_id": "pg-rollout-001",
                "approved_by": "runtime-ops",
                "approved_at": "2026-05-25T08:45:00Z",
                "target_store_mode": "strict_sql",
                "target_backend": "postgres",
                "lock_adapter_kind": "postgres_advisory_lock",
                "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
                "vendor_lock_decision_id": "vendor-lock-postgres-001",
                "renewal_lifecycle_reference": "renewal-lifecycle-smoke-001",
                "auto_claim_decision_reference": "auto-claim-policy-001",
                "audit_evidence_reference": "ownership-audit-001",
                "rollback_plan_reference": "rollback-worker-ownership-001",
                "fallback_policy_reference": "fallback-worker-ownership-001",
            },
            postgres_execution_seam_contract=execution_seam,
        )

        contract = build_worker_ownership_production_enablement_strategy_contract(
            section_readiness=section_readiness,
            production_default_enabled_requested=False,
            enablement_input_source_contract=consumer["enablement_input_source"],
        )

        self.assertEqual(consumer["overall_status"], "ready")
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["production_default_allowed"])
        self.assertEqual(contract["blocking_sections"], [])
        self.assertTrue(contract["policy"]["input_source_ready"])

    def test_production_enablement_strategy_requires_input_source_when_requested(self):
        section_readiness = {
            "durable_ownership_store": True,
            "vendor_lock_semantics": True,
            "heartbeat_renewal_supervisor": True,
            "migration_checklist": True,
            "rollout_checklist": True,
            "recovery_entry_auto_claim_policy": True,
            "stale_fencing_fail_closed": True,
            "ownership_audit_evidence": True,
        }

        contract = build_worker_ownership_production_enablement_strategy_contract(
            section_readiness=section_readiness,
            production_default_enabled_requested=True,
        )

        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["production_default_allowed"])
        self.assertIn("production_default_enablement_input_source", contract["blocking_sections"])
        self.assertEqual(contract["input_source"]["overall_status"], "blocked")
        self.assertFalse(contract["policy"]["input_source_ready"])

    def test_production_enablement_strategy_can_be_ready_with_input_source_and_all_sections(self):
        section_readiness = {
            "durable_ownership_store": True,
            "vendor_lock_semantics": True,
            "heartbeat_renewal_supervisor": True,
            "migration_checklist": True,
            "rollout_checklist": True,
            "recovery_entry_auto_claim_policy": True,
            "stale_fencing_fail_closed": True,
            "ownership_audit_evidence": True,
        }
        input_source = build_worker_ownership_production_default_enablement_input_source_contract(
            input_source_kind="rollout_artifact",
            request_id="prod-enable-001",
            requested_by="runtime-ops",
            requested_at="2026-05-25T08:10:00Z",
            target_store_mode="strict_sql",
            rollout_artifact="rollout/worker-ownership/prod-enable-001",
            vendor_lock_decision_id="vendor-lock-postgres-001",
            renewal_lifecycle_reference="renewal-lifecycle-smoke-001",
            auto_claim_decision_reference="auto-claim-policy-001",
            audit_evidence_reference="ownership-audit-001",
            rollback_plan_reference="rollback-worker-ownership-001",
            fallback_policy_reference="fallback-worker-ownership-001",
        )

        contract = build_worker_ownership_production_enablement_strategy_contract(
            section_readiness=section_readiness,
            production_default_enabled_requested=True,
            enablement_input_source_contract=input_source,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["production_default_allowed"])
        self.assertEqual(contract["blocking_sections"], [])
        self.assertEqual(contract["input_source"]["overall_status"], "ready")
        self.assertTrue(contract["policy"]["input_source_ready"])

    def test_production_gate_embeds_enablement_strategy_evidence(self):
        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
        )

        section = next(item for item in gate["sections"] if item["name"] == "fail_closed_default_decision")
        evidence = section["evidence"]
        self.assertEqual(section["status"], "blocked")
        self.assertFalse(section["ready"])
        self.assertEqual(evidence["enablement_strategy_status"], "blocked")
        self.assertFalse(evidence["production_default_enabled_requested"])
        self.assertFalse(evidence["production_default_allowed"])
        self.assertEqual(
            evidence["enablement_input_source_contract_version"],
            "phase-ii-worker-ownership-production-default-enablement-input-source-v1",
        )
        self.assertEqual(evidence["enablement_input_source_status"], "blocked")
        self.assertEqual(evidence["enablement_input_source_kind"], "")
        self.assertIn("input_source_kind", evidence["enablement_input_source_missing_sections"])
        self.assertTrue(evidence["explicit_enablement_required"])
        self.assertTrue(evidence["fail_closed_when_blocked"])
        self.assertTrue(evidence["sql_row_lease_is_not_default_authority"])
        self.assertIn("vendor_lock_semantics", evidence["blocking_sections"])
        self.assertFalse(gate["production_default_enabled"])

    def test_vendor_lock_semantics_contract_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_vendor_lock_semantics_contract(
            current_posture="sql_row_lease_fencing",
            sql_row_lease_fencing=True,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-vendor-lock-semantics-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["production_lock_allowed"])
        self.assertEqual(contract["current_posture"], "sql_row_lease_fencing")
        self.assertTrue(contract["policy"]["sql_row_lease_fencing"])
        self.assertFalse(contract["policy"]["sql_row_lease_is_vendor_lock"])
        self.assertEqual(contract["policy"]["target_decision"]["overall_status"], "blocked")
        self.assertIn("vendor_lock_adapter", contract["missing_sections"])
        self.assertIn("target_decision", contract["missing_sections"])
        self.assertIn("production_lock_allowment", contract["missing_sections"])
        self.assertIn("no_sql_row_lease_as_vendor_lock", contract["non_goals"])

    def test_vendor_lock_adapter_contract_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_vendor_lock_adapter_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-vendor-lock-adapter-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["adapter_kind"], "")
        self.assertEqual(contract["target_backend"], "")
        self.assertFalse(contract["acquire_supported"])
        self.assertFalse(contract["renew_supported"])
        self.assertFalse(contract["release_supported"])
        self.assertFalse(contract["probe_supported"])
        self.assertFalse(contract["production_lock_allowed"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertIn("adapter_kind", contract["missing_sections"])
        self.assertIn("target_backend", contract["missing_sections"])
        self.assertIn("acquire_support", contract["missing_sections"])
        self.assertIn("production_lock_allowment", contract["missing_sections"])
        self.assertIn("no_sql_row_lease_as_vendor_lock", contract["non_goals"])

    def test_vendor_lock_adapter_contract_can_be_ready_without_side_effects(self):
        probe = build_worker_ownership_postgres_vendor_lock_probe_contract(
            advisory_lock_family="pg_try_advisory_lock",
            lock_key_derivation="hash_run_id_to_bigint",
            lock_scope="session",
            fencing_token_binding="lease_fencing_token",
            ttl_renewal_strategy="heartbeat_validates_session_lock",
            failover_behavior="session_disconnect_releases_lock",
            stale_owner_cleanup_strategy="connection_pool_reaper",
            probe_safety="metadata_only",
        )
        contract = build_worker_ownership_vendor_lock_adapter_contract(
            adapter_kind="postgres_advisory_lock",
            target_backend="postgres",
            lock_scope="run",
            fencing_strategy="fencing_token",
            ttl_renewal_strategy="session_ttl_renewal",
            failover_strategy="connection_loss_releases_lock",
            stale_owner_cleanup_strategy="ttl_cleanup",
            acquire_supported=True,
            renew_supported=True,
            release_supported=True,
            probe_supported=True,
            production_lock_allowed=True,
            backend_probe=probe,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["adapter_kind"], "postgres_advisory_lock")
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertTrue(contract["acquire_supported"])
        self.assertTrue(contract["renew_supported"])
        self.assertTrue(contract["release_supported"])
        self.assertTrue(contract["probe_supported"])
        self.assertTrue(contract["production_lock_allowed"])
        self.assertEqual(contract["missing_sections"], [])
        self.assertIn("no_lock_acquisition_side_effect", contract["non_goals"])

    def test_postgres_vendor_lock_probe_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_postgres_vendor_lock_probe_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertEqual(contract["advisory_lock_family"], "")
        self.assertFalse(contract["executes_probe"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertIn("advisory_lock_family", contract["missing_sections"])
        self.assertIn("lock_key_derivation", contract["missing_sections"])
        self.assertIn("probe_safety", contract["missing_sections"])
        self.assertIn("no_postgres_connection", contract["non_goals"])

    def test_postgres_vendor_lock_probe_can_be_ready_without_execution(self):
        contract = build_worker_ownership_postgres_vendor_lock_probe_contract(
            advisory_lock_family="pg_try_advisory_lock",
            lock_key_derivation="hash_run_id_to_bigint",
            lock_scope="session",
            fencing_token_binding="lease_fencing_token",
            ttl_renewal_strategy="heartbeat_validates_session_lock",
            failover_behavior="session_disconnect_releases_lock",
            stale_owner_cleanup_strategy="connection_pool_reaper",
            probe_safety="metadata_only",
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["advisory_lock_family"], "pg_try_advisory_lock")
        self.assertEqual(contract["lock_scope"], "session")
        self.assertFalse(contract["executes_probe"])
        self.assertEqual(contract["missing_sections"], [])
        self.assertIn("no_advisory_lock_sql_execution", contract["non_goals"])

    def test_postgres_advisory_lock_execution_seam_defaults_to_blocked(self):
        seam = PostgresAdvisoryLockExecutionSeam()

        contract = seam.contract()
        probe = seam.probe_once()
        acquired = seam.acquire_once(
            run_id="run-1",
            worker_id="worker-a",
            lease_id="lease-1",
            fencing_token=7,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["executor_bound"])
        self.assertFalse(contract["enabled_by_default"])
        self.assertFalse(contract["production_lock_allowed"])
        self.assertIn("executor_binding", contract["missing_sections"])
        self.assertEqual(probe["status"], "blocked")
        self.assertFalse(probe["executed"])
        self.assertEqual(probe["reason"], "postgres_advisory_lock_executor_missing")
        self.assertEqual(acquired["status"], "blocked")
        self.assertFalse(acquired["acquired"])
        self.assertFalse(acquired["executed"])

    def test_postgres_advisory_lock_execution_seam_executes_only_with_injected_executor(self):
        envelopes = []

        def _executor(envelope):
            envelopes.append(dict(envelope))
            if envelope["operation"] == "probe":
                return {"ok": True}
            if envelope["operation"] == "acquire":
                return {"ok": True, "acquired": True}
            if envelope["operation"] == "renew":
                return {"ok": True, "renewed": True}
            if envelope["operation"] == "release":
                return {"ok": True, "released": True}
            return {"ok": False}

        seam = PostgresAdvisoryLockExecutionSeam(executor=_executor)

        probe = seam.probe_once()
        acquired = seam.acquire_once(
            run_id="run-1",
            worker_id="worker-a",
            lease_id="lease-1",
            fencing_token=7,
        )
        renewed = seam.renew_once(
            run_id="run-1",
            worker_id="worker-a",
            lease_id="lease-1",
            fencing_token=7,
        )
        released = seam.release_once(
            run_id="run-1",
            worker_id="worker-a",
            lease_id="lease-1",
            fencing_token=7,
        )

        self.assertEqual(seam.contract()["overall_status"], "ready")
        self.assertTrue(seam.contract()["executor_bound"])
        self.assertFalse(seam.contract()["production_lock_allowed"])
        self.assertEqual(probe["status"], "ready")
        self.assertTrue(probe["executed"])
        self.assertEqual(acquired["status"], "acquired")
        self.assertTrue(acquired["acquired"])
        self.assertTrue(acquired["executed"])
        self.assertIsInstance(acquired["lock_key"], int)
        self.assertEqual(renewed["status"], "renewed")
        self.assertTrue(renewed["renewed"])
        self.assertEqual(released["status"], "released")
        self.assertTrue(released["released"])
        self.assertEqual([item["operation"] for item in envelopes], ["probe", "acquire", "renew", "release"])
        self.assertEqual(envelopes[1]["run_id"], "run-1")
        self.assertEqual(envelopes[1]["worker_id"], "worker-a")
        self.assertEqual(envelopes[1]["lease_id"], "lease-1")
        self.assertEqual(envelopes[1]["fencing_token"], 7)
        self.assertEqual(envelopes[1]["sql"], "SELECT pg_try_advisory_lock(:lock_key)")

    def test_postgres_advisory_lock_execution_seam_fails_closed_before_executor(self):
        envelopes = []

        def _executor(envelope):
            envelopes.append(dict(envelope))
            return {"ok": True, "acquired": True}

        seam = PostgresAdvisoryLockExecutionSeam(executor=_executor)

        blocked = seam.acquire_once(
            run_id="",
            worker_id="worker-a",
            lease_id="lease-1",
            fencing_token=7,
        )

        self.assertEqual(blocked["status"], "blocked")
        self.assertFalse(blocked["acquired"])
        self.assertFalse(blocked["executed"])
        self.assertEqual(blocked["reason"], "postgres_advisory_lock_owner_identity_missing")
        self.assertEqual(envelopes, [])

    def test_postgres_advisory_lock_execution_seam_contract_builder_embeds_policy(self):
        contract = build_worker_ownership_postgres_advisory_lock_execution_seam_contract(
            executor_bound=True,
            probe_once_supported=True,
            acquire_once_supported=True,
            renew_once_supported=True,
            release_once_supported=True,
            lock_key_derivation_ready=True,
            owner_identity_required=True,
            fencing_token_required=True,
            fail_closed=True,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["executor_bound"])
        self.assertTrue(contract["policy"]["acquire_once_supported"])
        self.assertTrue(contract["policy"]["release_once_supported"])
        self.assertTrue(contract["policy"]["lock_key_derivation_ready"])
        self.assertFalse(contract["enabled_by_default"])
        self.assertFalse(contract["production_lock_allowed"])
        self.assertEqual(contract["missing_sections"], [])

    def test_postgres_vendor_lock_probe_embeds_execution_seam_evidence(self):
        contract = build_worker_ownership_postgres_vendor_lock_probe_contract()

        execution_seam = contract["execution_seam"]

        self.assertEqual(
            execution_seam["contract_version"],
            "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1",
        )
        self.assertEqual(execution_seam["overall_status"], "blocked")
        self.assertFalse(execution_seam["executor_bound"])
        self.assertFalse(execution_seam["enabled_by_default"])
        self.assertFalse(execution_seam["production_lock_allowed"])
        self.assertIn("executor_binding", execution_seam["missing_sections"])

    def test_vendor_lock_adapter_embeds_postgres_probe_contract(self):
        probe = build_worker_ownership_postgres_vendor_lock_probe_contract()
        contract = build_worker_ownership_vendor_lock_adapter_contract(
            adapter_kind="postgres_advisory_lock",
            target_backend="postgres",
            lock_scope="run",
            fencing_strategy="fencing_token",
            ttl_renewal_strategy="session_ttl_renewal",
            failover_strategy="connection_loss_releases_lock",
            stale_owner_cleanup_strategy="ttl_cleanup",
            acquire_supported=True,
            renew_supported=True,
            release_supported=True,
            probe_supported=True,
            production_lock_allowed=True,
            backend_probe=probe,
        )

        self.assertEqual(contract["overall_status"], "blocked")
        self.assertEqual(contract["backend_probe"]["overall_status"], "blocked")
        self.assertIn("backend_probe", contract["missing_sections"])

    def test_vendor_lock_target_decision_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_vendor_lock_target_decision_contract(
            target_backend="sql_row_lease_fencing",
            sql_row_lease_is_vendor_lock=False,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["decision_recorded"])
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertFalse(contract["production_lock_allowed"])
        self.assertEqual(contract["input_source"]["overall_status"], "blocked")
        self.assertIn("input_source", contract["missing_sections"])
        self.assertIn("decision_recorded", contract["missing_sections"])
        self.assertIn("target_backend", contract["missing_sections"])
        self.assertIn("production_lock_allowment", contract["missing_sections"])
        self.assertIn("no_sql_row_lease_as_vendor_lock", contract["non_goals"])

    def test_vendor_lock_target_decision_input_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_vendor_lock_target_decision_input_contract(
            target_backend="sql_row_lease_fencing",
            lock_adapter_kind="",
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-input-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["input_source_kind"], "")
        self.assertFalse(contract["sql_row_lease_is_vendor_lock"])
        self.assertIn("input_source_kind", contract["missing_sections"])
        self.assertIn("decision_id", contract["missing_sections"])
        self.assertIn("approved_by", contract["missing_sections"])
        self.assertIn("target_backend", contract["missing_sections"])
        self.assertIn("source_reference", contract["missing_sections"])

    def test_vendor_lock_target_decision_input_can_be_ready_without_implementation(self):
        contract = build_worker_ownership_vendor_lock_target_decision_input_contract(
            input_source_kind="ops_decision_record",
            decision_id="vendor-lock-target-001",
            approved_by="runtime-ops",
            approved_at="2026-05-25T06:30:00Z",
            target_backend="postgres",
            lock_adapter_kind="postgres_advisory_lock",
            sql_row_lease_is_vendor_lock=False,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["input_source_kind"], "ops_decision_record")
        self.assertEqual(contract["decision_id"], "vendor-lock-target-001")
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertEqual(contract["missing_sections"], [])
        self.assertIn("no_vendor_specific_lock_adapter", contract["non_goals"])

    def test_vendor_lock_target_decision_can_be_ready_without_implementation(self):
        input_source = build_worker_ownership_vendor_lock_target_decision_input_contract(
            input_source_kind="ops_decision_record",
            decision_id="vendor-lock-target-001",
            approved_by="runtime-ops",
            approved_at="2026-05-25T06:30:00Z",
            target_backend="postgres",
            lock_adapter_kind="postgres_advisory_lock",
        )
        contract = build_worker_ownership_vendor_lock_target_decision_contract(
            decision_recorded=True,
            target_backend="postgres",
            lock_adapter_kind="postgres_advisory_lock",
            lock_scope="run",
            fencing_strategy="fencing_token",
            ttl_renewal_strategy="lease_ttl_renewal",
            failover_strategy="connection_loss_releases_lock",
            stale_owner_cleanup_strategy="ttl_cleanup",
            sql_row_lease_is_vendor_lock=False,
            production_lock_allowed=True,
            input_source_contract=input_source,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["target_backend"], "postgres")
        self.assertEqual(contract["lock_adapter_kind"], "postgres_advisory_lock")
        self.assertEqual(contract["input_source"]["overall_status"], "ready")
        self.assertTrue(contract["production_lock_allowed"])
        self.assertEqual(contract["missing_sections"], [])
        self.assertIn("no_vendor_specific_lock_adapter", contract["non_goals"])

    def test_vendor_lock_semantics_embeds_target_decision_contract(self):
        input_source = build_worker_ownership_vendor_lock_target_decision_input_contract(
            input_source_kind="ops_decision_record",
            decision_id="vendor-lock-target-001",
            approved_by="runtime-ops",
            approved_at="2026-05-25T06:30:00Z",
            target_backend="postgres",
            lock_adapter_kind="postgres_advisory_lock",
        )
        target_decision = build_worker_ownership_vendor_lock_target_decision_contract(
            decision_recorded=True,
            target_backend="postgres",
            lock_adapter_kind="postgres_advisory_lock",
            lock_scope="run",
            fencing_strategy="fencing_token",
            ttl_renewal_strategy="lease_ttl_renewal",
            failover_strategy="connection_loss_releases_lock",
            stale_owner_cleanup_strategy="ttl_cleanup",
            production_lock_allowed=True,
            input_source_contract=input_source,
        )
        adapter_contract = build_worker_ownership_vendor_lock_adapter_contract(
            adapter_kind="postgres_advisory_lock",
            target_backend="postgres",
            lock_scope="run",
            fencing_strategy="fencing_token",
            ttl_renewal_strategy="lease_ttl_renewal",
            failover_strategy="connection_loss_releases_lock",
            stale_owner_cleanup_strategy="ttl_cleanup",
            acquire_supported=True,
            renew_supported=True,
            release_supported=True,
            probe_supported=True,
            production_lock_allowed=True,
            backend_probe=build_worker_ownership_postgres_vendor_lock_probe_contract(
                advisory_lock_family="pg_try_advisory_lock",
                lock_key_derivation="hash_run_id_to_bigint",
                lock_scope="session",
                fencing_token_binding="lease_fencing_token",
                ttl_renewal_strategy="heartbeat_validates_session_lock",
                failover_behavior="session_disconnect_releases_lock",
                stale_owner_cleanup_strategy="connection_pool_reaper",
                probe_safety="metadata_only",
            ),
        )
        contract = build_worker_ownership_vendor_lock_semantics_contract(
            current_posture="vendor_distributed_lock",
            sql_row_lease_fencing=True,
            vendor_lock_adapter_present=True,
            lock_scope_defined=True,
            fencing_guarantee_defined=True,
            failover_semantics_defined=True,
            ttl_renewal_semantics_defined=True,
            stale_owner_cleanup_defined=True,
            production_lock_allowed=True,
            lock_adapter_kind="postgres_advisory_lock",
            lock_scope="run",
            target_decision_contract=target_decision,
            adapter_contract=adapter_contract,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["production_lock_allowed"])
        self.assertEqual(
            contract["policy"]["adapter_contract"]["contract_version"],
            "phase-ii-worker-ownership-vendor-lock-adapter-v1",
        )
        self.assertEqual(contract["policy"]["adapter_contract"]["overall_status"], "ready")
        self.assertEqual(
            contract["policy"]["target_decision"]["contract_version"],
            "phase-ii-worker-ownership-vendor-lock-target-decision-v1",
        )
        self.assertEqual(contract["policy"]["target_decision"]["overall_status"], "ready")
        self.assertEqual(
            contract["policy"]["target_decision"]["input_source"]["overall_status"],
            "ready",
        )
        self.assertFalse(contract["policy"]["sql_row_lease_is_vendor_lock"])

    def test_production_gate_embeds_vendor_lock_blocker_evidence(self):
        vendor_lock = build_worker_ownership_vendor_lock_semantics_contract(
            current_posture="sql_row_lease_fencing",
            sql_row_lease_fencing=True,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            vendor_lock_semantics_contract=vendor_lock,
        )

        section = next(item for item in gate["sections"] if item["name"] == "vendor_lock_semantics")
        evidence = section["evidence"]
        self.assertEqual(section["status"], "blocked")
        self.assertFalse(section["ready"])
        self.assertEqual(evidence["vendor_lock_status"], "blocked")
        self.assertEqual(evidence["current_posture"], "sql_row_lease_fencing")
        self.assertTrue(evidence["sql_row_lease_fencing"])
        self.assertFalse(evidence["sql_row_lease_is_vendor_lock"])
        self.assertFalse(evidence["vendor_lock_adapter_present"])
        self.assertEqual(
            evidence["vendor_lock_adapter_contract_version"],
            "phase-ii-worker-ownership-vendor-lock-adapter-v1",
        )
        self.assertEqual(evidence["vendor_lock_adapter_status"], "blocked")
        self.assertEqual(evidence["vendor_lock_adapter_kind"], "")
        self.assertEqual(evidence["vendor_lock_adapter_target_backend"], "")
        self.assertFalse(evidence["vendor_lock_adapter_acquire_supported"])
        self.assertFalse(evidence["vendor_lock_adapter_renew_supported"])
        self.assertFalse(evidence["vendor_lock_adapter_release_supported"])
        self.assertFalse(evidence["vendor_lock_adapter_probe_supported"])
        self.assertFalse(evidence["vendor_lock_adapter_production_allowed"])
        self.assertFalse(evidence["vendor_lock_adapter_sql_row_lease_is_vendor_lock"])
        self.assertIn("adapter_kind", evidence["vendor_lock_adapter_missing_sections"])
        self.assertFalse(evidence["production_lock_allowed"])
        self.assertEqual(evidence["vendor_lock_target_decision_status"], "blocked")
        self.assertFalse(evidence["vendor_lock_target_decision_recorded"])
        self.assertFalse(evidence["vendor_lock_target_sql_row_lease_is_vendor_lock"])
        self.assertFalse(evidence["vendor_lock_target_production_allowed"])
        self.assertEqual(evidence["vendor_lock_target_input_source_status"], "blocked")
        self.assertEqual(evidence["vendor_lock_target_input_source_kind"], "")
        self.assertFalse(evidence["vendor_lock_target_input_sql_row_lease_is_vendor_lock"])
        self.assertIn("vendor_lock_adapter", evidence["vendor_lock_missing_sections"])
        self.assertIn("target_decision", evidence["vendor_lock_missing_sections"])
        self.assertIn("input_source", evidence["vendor_lock_target_missing_sections"])
        self.assertIn(
            "decision_recorded",
            evidence["vendor_lock_target_missing_sections"],
        )
        self.assertIn(
            "input_source_kind",
            evidence["vendor_lock_target_input_missing_sections"],
        )
        self.assertIn("vendor_lock_semantics", gate["missing_sections"])

    def test_production_gate_requires_vendor_lock_production_allowment(self):
        vendor_lock = build_worker_ownership_vendor_lock_semantics_contract(
            current_posture="vendor_distributed_lock",
            sql_row_lease_fencing=True,
            vendor_lock_adapter_present=True,
            lock_scope_defined=True,
            fencing_guarantee_defined=True,
            failover_semantics_defined=True,
            ttl_renewal_semantics_defined=True,
            stale_owner_cleanup_defined=True,
            production_lock_allowed=False,
            lock_adapter_kind="postgres_advisory_lock",
            lock_scope="run",
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            vendor_lock_semantics_contract=vendor_lock,
        )

        section = next(item for item in gate["sections"] if item["name"] == "vendor_lock_semantics")
        self.assertEqual(vendor_lock["overall_status"], "blocked")
        self.assertIn("production_lock_allowment", vendor_lock["missing_sections"])
        self.assertFalse(section["ready"])
        self.assertIn("vendor_lock_semantics", gate["missing_sections"])
        self.assertFalse(gate["production_default_enabled"])

    def test_production_gate_embeds_postgres_probe_blocker_evidence(self):
        adapter_contract = build_worker_ownership_vendor_lock_adapter_contract(
            adapter_kind="postgres_advisory_lock",
            target_backend="postgres",
            lock_scope="run",
            fencing_strategy="fencing_token",
            ttl_renewal_strategy="session_ttl_renewal",
            failover_strategy="connection_loss_releases_lock",
            stale_owner_cleanup_strategy="ttl_cleanup",
            acquire_supported=True,
            renew_supported=True,
            release_supported=True,
            probe_supported=True,
            production_lock_allowed=True,
        )
        vendor_lock = build_worker_ownership_vendor_lock_semantics_contract(
            current_posture="vendor_distributed_lock",
            sql_row_lease_fencing=True,
            vendor_lock_adapter_present=True,
            lock_scope_defined=True,
            fencing_guarantee_defined=True,
            failover_semantics_defined=True,
            ttl_renewal_semantics_defined=True,
            stale_owner_cleanup_defined=True,
            production_lock_allowed=True,
            lock_adapter_kind="postgres_advisory_lock",
            lock_scope="run",
            adapter_contract=adapter_contract,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            vendor_lock_semantics_contract=vendor_lock,
        )

        section = next(item for item in gate["sections"] if item["name"] == "vendor_lock_semantics")
        evidence = section["evidence"]
        self.assertEqual(section["status"], "blocked")
        self.assertEqual(
            evidence["vendor_lock_postgres_probe_contract_version"],
            "phase-ii-worker-ownership-postgres-vendor-lock-probe-v1",
        )
        self.assertEqual(evidence["vendor_lock_postgres_probe_status"], "blocked")
        self.assertFalse(evidence["vendor_lock_postgres_probe_executes"])
        self.assertFalse(evidence["vendor_lock_postgres_sql_row_lease_is_vendor_lock"])
        self.assertEqual(
            evidence["vendor_lock_postgres_execution_seam_contract_version"],
            "phase-ii-worker-ownership-postgres-advisory-lock-execution-seam-v1",
        )
        self.assertEqual(evidence["vendor_lock_postgres_execution_seam_status"], "blocked")
        self.assertFalse(evidence["vendor_lock_postgres_executor_bound"])
        self.assertFalse(evidence["vendor_lock_postgres_execution_enabled_by_default"])
        self.assertFalse(evidence["vendor_lock_postgres_execution_production_allowed"])
        self.assertFalse(evidence["vendor_lock_postgres_acquire_once_supported"])
        self.assertIn(
            "executor_binding",
            evidence["vendor_lock_postgres_execution_missing_sections"],
        )
        self.assertIn(
            "advisory_lock_family",
            evidence["vendor_lock_postgres_probe_missing_sections"],
        )
        self.assertIn("vendor_lock_semantics", gate["missing_sections"])

    def test_renewal_supervisor_contract_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_renewal_supervisor_contract(
            heartbeat_operation_present=True,
            renew_once_supported=True,
            owner_identity_required=True,
            ttl_interval_policy_present=True,
            lease_loss_fail_closed=True,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-renewal-supervisor-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["supervisor_enabled_by_default"])
        self.assertIn("background_supervisor", contract["missing_sections"])
        self.assertIn("background_supervisor", contract["missing_sections"])
        self.assertNotIn("renewal_owner_identity", contract["missing_sections"])
        self.assertNotIn("ttl_interval_policy", contract["missing_sections"])
        self.assertTrue(contract["policy"]["heartbeat_operation_present"])
        self.assertTrue(contract["policy"]["renew_once_supported"])
        self.assertTrue(contract["policy"]["owner_identity_required"])
        self.assertTrue(contract["policy"]["ttl_interval_policy_ready"])
        self.assertFalse(contract["policy"]["controlled_lifecycle_supported"])
        self.assertFalse(contract["policy"]["starts_by_default"])
        self.assertFalse(contract["policy"]["active"])
        self.assertTrue(contract["policy"]["lease_loss_fail_closed"])
        self.assertIn("no_background_lease_renewal_loop", contract["non_goals"])

    def test_renewal_supervisor_renew_once_refreshes_valid_lease(self):
        store, clock = self._store_with_clock()
        claim = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)
        original_expires_at = claim["lease_expires_at"]
        clock["now"] = clock["now"] + timedelta(seconds=10)
        supervisor = WorkerOwnershipRenewalSupervisor(
            store=store,
            lease_ttl_seconds=45,
            renew_interval_seconds=15,
        )

        renewed = supervisor.renew_once(
            run_id="run-1",
            worker_id="worker-a",
            lease_id=claim["lease_id"],
            fencing_token=claim["fencing_token"],
        )

        self.assertTrue(renewed["renewed"])
        self.assertEqual(renewed["renewal_status"], "renewed")
        self.assertEqual(renewed["lease_status"], WORKER_OWNERSHIP_STATUS_REFRESHED)
        self.assertEqual(renewed["worker_id"], "worker-a")
        self.assertEqual(renewed["fencing_token"], claim["fencing_token"])
        self.assertNotEqual(renewed["lease_expires_at"], original_expires_at)
        self.assertFalse(renewed["background_supervisor_started"])

    def test_renewal_supervisor_renew_once_fails_closed_on_stale_fencing(self):
        store, _clock = self._store_with_clock()
        claim = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)
        supervisor = WorkerOwnershipRenewalSupervisor(store=store)

        blocked = supervisor.renew_once(
            run_id="run-1",
            worker_id="worker-a",
            lease_id=claim["lease_id"],
            fencing_token=claim["fencing_token"] + 1,
        )

        self.assertFalse(blocked["renewed"])
        self.assertEqual(blocked["renewal_status"], "blocked")
        self.assertEqual(blocked["reason"], WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN)
        self.assertEqual(blocked["blocked_reason"], "stale_worker_fencing_token")
        self.assertFalse(blocked["background_supervisor_started"])

    def test_renewal_supervisor_renew_once_fails_closed_without_store(self):
        supervisor = WorkerOwnershipRenewalSupervisor(store=None)

        blocked = supervisor.renew_once(
            run_id="run-1",
            worker_id="worker-a",
            lease_id="lease-1",
            fencing_token=1,
        )

        self.assertFalse(blocked["renewed"])
        self.assertEqual(blocked["renewal_status"], "blocked")
        self.assertEqual(blocked["reason"], "worker_ownership_store_missing")
        self.assertEqual(blocked["blocked_reason"], "renewal_store_missing")
        self.assertFalse(blocked["background_supervisor_started"])

    def test_renewal_supervisor_lifecycle_defaults_to_inactive(self):
        store, _clock = self._store_with_clock()
        supervisor = WorkerOwnershipRenewalSupervisor(store=store)

        status = supervisor.status()

        self.assertFalse(status["active"])
        self.assertFalse(status["starts_by_default"])
        self.assertTrue(status["controlled_lifecycle_supported"])
        self.assertTrue(status["stop_supported"])
        self.assertEqual(status["last_renewal_status"], "")
        self.assertEqual(status["renewal_count"], 0)

    def test_renewal_supervisor_start_and_stop_control_lifecycle(self):
        store, clock = self._store_with_clock()
        claim = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)
        supervisor = WorkerOwnershipRenewalSupervisor(
            store=store,
            lease_ttl_seconds=45,
            renew_interval_seconds=30,
        )
        clock["now"] = clock["now"] + timedelta(seconds=5)

        started = supervisor.start(
            run_id="run-1",
            worker_id="worker-a",
            lease_id=claim["lease_id"],
            fencing_token=claim["fencing_token"],
        )

        self.assertTrue(started["active"])
        self.assertEqual(started["last_renewal_status"], "renewed")
        self.assertEqual(started["renewal_count"], 1)
        self.assertFalse(started["starts_by_default"])
        self.assertTrue(started["failure_fail_closed"])
        stopped = supervisor.stop()
        self.assertFalse(stopped["active"])
        self.assertEqual(stopped["last_renewal_status"], "renewed")
        self.assertEqual(stopped["renewal_count"], 1)

    def test_renewal_supervisor_start_fails_closed_on_stale_fencing(self):
        store, _clock = self._store_with_clock()
        claim = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)
        supervisor = WorkerOwnershipRenewalSupervisor(store=store)

        status = supervisor.start(
            run_id="run-1",
            worker_id="worker-a",
            lease_id=claim["lease_id"],
            fencing_token=claim["fencing_token"] + 1,
        )

        self.assertFalse(status["active"])
        self.assertEqual(status["last_renewal_status"], "blocked")
        self.assertEqual(status["last_blocked_reason"], "stale_worker_fencing_token")
        self.assertEqual(status["last_failure_reason"], WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN)
        self.assertEqual(status["renewal_count"], 0)

    def test_production_gate_embeds_renewal_supervisor_blocker_evidence(self):
        renewal = build_worker_ownership_renewal_supervisor_contract(
            heartbeat_operation_present=True,
            renew_once_supported=True,
            owner_identity_required=True,
            controlled_lifecycle_supported=True,
            starts_by_default=False,
            active=False,
            stop_supported=True,
            failure_fail_closed=True,
            ttl_interval_policy_present=True,
            lease_loss_fail_closed=True,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            renewal_supervisor_contract=renewal,
        )

        section = next(
            item for item in gate["sections"] if item["name"] == "heartbeat_renewal_supervisor"
        )
        evidence = section["evidence"]
        self.assertEqual(section["status"], "blocked")
        self.assertFalse(section["ready"])
        self.assertEqual(evidence["renewal_supervisor_status"], "blocked")
        self.assertFalse(evidence["supervisor_enabled_by_default"])
        self.assertTrue(evidence["heartbeat_operation_present"])
        self.assertTrue(evidence["renew_once_supported"])
        self.assertTrue(evidence["owner_identity_required"])
        self.assertTrue(evidence["ttl_interval_policy_ready"])
        self.assertTrue(evidence["controlled_lifecycle_supported"])
        self.assertFalse(evidence["starts_by_default"])
        self.assertFalse(evidence["active"])
        self.assertTrue(evidence["stop_supported"])
        self.assertTrue(evidence["failure_fail_closed"])
        self.assertTrue(evidence["lease_loss_fail_closed"])
        self.assertIn("background_supervisor", evidence["renewal_supervisor_missing_sections"])
        self.assertIn("heartbeat_renewal_supervisor", gate["missing_sections"])

    def test_production_gate_requires_renewal_supervisor_default_enablement(self):
        renewal = build_worker_ownership_renewal_supervisor_contract(
            heartbeat_operation_present=True,
            background_supervisor_present=True,
            renewal_owner_identity_present=True,
            ttl_interval_policy_present=True,
            lease_loss_fail_closed=True,
            supervisor_enabled_by_default=False,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            renewal_supervisor_contract=renewal,
        )

        section = next(
            item for item in gate["sections"] if item["name"] == "heartbeat_renewal_supervisor"
        )
        self.assertEqual(renewal["overall_status"], "ready")
        self.assertFalse(section["ready"])
        self.assertIn("heartbeat_renewal_supervisor", gate["missing_sections"])
        self.assertFalse(gate["production_default_enabled"])

    def test_rollout_readiness_contract_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_rollout_readiness_contract(
            migration_ready=True,
            stale_fencing_verified=True,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-rollout-readiness-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["production_rollout_confirmed"])
        self.assertTrue(contract["checklist"]["migration_ready"])
        self.assertTrue(contract["checklist"]["stale_fencing_verified"])
        self.assertIn("strict_mode_rollout", contract["missing_sections"])
        self.assertIn("fallback_policy", contract["missing_sections"])
        self.assertIn("rollback_plan", contract["missing_sections"])
        self.assertIn("no_deployment_state_mutation", contract["non_goals"])

    def test_rollout_operationalization_contract_defaults_to_blocked(self):
        contract = build_worker_ownership_production_rollout_operationalization_contract(
            renewal_lifecycle_verified=True,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-production-rollout-operationalization-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["production_rollout_confirmed"])
        self.assertEqual(contract["rollout_mode"], "readiness_only")
        self.assertTrue(contract["required_artifacts"])
        self.assertIn("rollback_plan", contract["missing_artifacts"])
        self.assertEqual(contract["rollback_plan_status"], "missing")
        self.assertEqual(contract["fallback_policy_status"], "missing")
        self.assertEqual(
            contract["renewal_lifecycle_verification_status"],
            "verified",
        )
        self.assertEqual(contract["auto_claim_decision_status"], "missing")
        self.assertEqual(contract["rollout_confirmation_decision_status"], "blocked")
        self.assertFalse(contract["rollout_decision_recorded"])
        self.assertIn("rollout_confirmation_decision", contract["missing_artifacts"])
        self.assertIn(
            "decision_recorded",
            contract["rollout_confirmation_missing_sections"],
        )
        self.assertIn("no_deployment_state_mutation", contract["non_goals"])

    def test_rollout_confirmation_decision_contract_defaults_to_blocked(self):
        contract = build_worker_ownership_rollout_confirmation_decision_contract(
            renewal_lifecycle_verified=True,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-decision-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["production_rollout_confirmed"])
        self.assertFalse(contract["decision_recorded"])
        self.assertIn("decision_recorded", contract["missing_sections"])
        self.assertIn("decision_id", contract["missing_sections"])
        self.assertIn("approved_by", contract["missing_sections"])
        self.assertIn("target_store_mode", contract["missing_sections"])
        self.assertIn("input_source", contract["missing_sections"])
        self.assertEqual(contract["input_source"]["overall_status"], "blocked")
        self.assertIn("no_deployment_state_mutation", contract["non_goals"])

    def test_rollout_confirmation_input_source_defaults_to_blocked(self):
        contract = build_worker_ownership_rollout_confirmation_input_source_contract(
            target_store_mode="sql_row_lease_fencing"
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-rollout-confirmation-input-source-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertEqual(contract["target_store_mode"], "sql_row_lease_fencing")
        self.assertTrue(contract["sql_row_lease_is_rollout_authority"])
        self.assertIn("input_source_kind", contract["missing_sections"])
        self.assertIn("decision_id", contract["missing_sections"])
        self.assertIn("target_store_mode", contract["missing_sections"])
        self.assertIn("sql_row_lease_not_rollout_authority", contract["missing_sections"])
        self.assertIn("no_production_ownership_enablement", contract["non_goals"])

    def test_rollout_confirmation_input_source_can_be_ready(self):
        contract = build_worker_ownership_rollout_confirmation_input_source_contract(
            input_source_kind="change_ticket",
            decision_id="CHG-2026-05-25-001",
            approved_by="platform-owner",
            approved_at="2026-05-25T13:30:00+08:00",
            target_store_mode="strict_sql",
            rollback_plan_reference="runbook://worker-ownership/rollback",
            fallback_policy_reference="runbook://worker-ownership/fallback",
            renewal_lifecycle_reference="smoke://renewal-lifecycle/verified",
            auto_claim_decision_reference="decision://auto-claim/disabled",
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertEqual(contract["input_source_kind"], "change_ticket")
        self.assertEqual(contract["decision_id"], "CHG-2026-05-25-001")
        self.assertEqual(contract["target_store_mode"], "strict_sql")
        self.assertFalse(contract["sql_row_lease_is_rollout_authority"])
        self.assertEqual(contract["missing_sections"], [])

    def test_rollout_confirmation_decision_contract_can_be_ready(self):
        input_source = build_worker_ownership_rollout_confirmation_input_source_contract(
            input_source_kind="ops_decision_record",
            decision_id="rollout-2026-05-25-001",
            approved_by="platform-owner",
            approved_at="2026-05-25T13:30:00+08:00",
            target_store_mode="strict_sql",
            rollback_plan_reference="runbook://worker-ownership/rollback",
            fallback_policy_reference="runbook://worker-ownership/fallback",
            renewal_lifecycle_reference="smoke://renewal-lifecycle/verified",
            auto_claim_decision_reference="decision://auto-claim/disabled",
        )
        contract = build_worker_ownership_rollout_confirmation_decision_contract(
            production_rollout_confirmed=True,
            decision_recorded=True,
            decision_id="rollout-2026-05-25-001",
            approved_by="platform-owner",
            approved_at="2026-05-25T13:30:00+08:00",
            target_store_mode="strict_sql",
            rollback_plan_acknowledged=True,
            fallback_policy_acknowledged=True,
            renewal_lifecycle_verified=True,
            auto_claim_decision_recorded=True,
            input_source_contract=input_source,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertTrue(contract["production_rollout_confirmed"])
        self.assertTrue(contract["decision_recorded"])
        self.assertEqual(contract["decision_id"], "rollout-2026-05-25-001")
        self.assertEqual(contract["approved_by"], "platform-owner")
        self.assertEqual(contract["target_store_mode"], "strict_sql")
        self.assertEqual(contract["input_source"]["overall_status"], "ready")
        self.assertEqual(contract["missing_sections"], [])

    def test_rollout_operationalization_embeds_confirmation_decision(self):
        input_source = build_worker_ownership_rollout_confirmation_input_source_contract(
            input_source_kind="ops_decision_record",
            decision_id="rollout-2026-05-25-001",
            approved_by="platform-owner",
            approved_at="2026-05-25T13:30:00+08:00",
            target_store_mode="strict_sql",
            rollback_plan_reference="runbook://worker-ownership/rollback",
            fallback_policy_reference="runbook://worker-ownership/fallback",
            renewal_lifecycle_reference="smoke://renewal-lifecycle/verified",
            auto_claim_decision_reference="decision://auto-claim/disabled",
        )
        decision = build_worker_ownership_rollout_confirmation_decision_contract(
            production_rollout_confirmed=True,
            decision_recorded=True,
            decision_id="rollout-2026-05-25-001",
            approved_by="platform-owner",
            approved_at="2026-05-25T13:30:00+08:00",
            target_store_mode="strict_sql",
            rollback_plan_acknowledged=True,
            fallback_policy_acknowledged=True,
            renewal_lifecycle_verified=True,
            auto_claim_decision_recorded=True,
            input_source_contract=input_source,
        )

        contract = build_worker_ownership_production_rollout_operationalization_contract(
            strict_mode_rollout_confirmed=True,
            fallback_policy_confirmed=True,
            migration_ready=True,
            renewal_lifecycle_verified=True,
            stale_fencing_verified=True,
            auto_claim_decision_recorded=True,
            audit_evidence_ready=True,
            rollback_plan_ready=True,
            production_rollout_confirmed=True,
            confirmation_decision_contract=decision,
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["production_rollout_confirmed"])
        self.assertEqual(contract["rollout_confirmation_decision_status"], "ready")
        self.assertTrue(contract["rollout_decision_recorded"])
        self.assertEqual(contract["rollout_decision_id"], "rollout-2026-05-25-001")
        self.assertEqual(contract["rollout_target_store_mode"], "strict_sql")
        self.assertEqual(contract["rollout_confirmation_input_source_status"], "ready")
        self.assertEqual(contract["rollout_confirmation_missing_sections"], [])

    def test_production_gate_embeds_rollout_readiness_blocker_evidence(self):
        rollout = build_worker_ownership_rollout_readiness_contract(
            migration_ready=True,
            stale_fencing_verified=True,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            rollout_readiness_contract=rollout,
        )

        section = next(item for item in gate["sections"] if item["name"] == "rollout_checklist")
        evidence = section["evidence"]
        self.assertEqual(section["status"], "blocked")
        self.assertFalse(section["ready"])
        self.assertEqual(evidence["rollout_readiness_status"], "blocked")
        self.assertFalse(evidence["production_rollout_confirmed"])
        self.assertTrue(evidence["migration_ready"])
        self.assertTrue(evidence["stale_fencing_verified"])
        self.assertFalse(evidence["rollback_plan_ready"])
        self.assertEqual(evidence["rollout_operationalization_status"], "blocked")
        self.assertEqual(evidence["rollback_plan_status"], "missing")
        self.assertEqual(evidence["fallback_policy_status"], "missing")
        self.assertEqual(evidence["auto_claim_decision_status"], "missing")
        self.assertEqual(
            evidence["renewal_lifecycle_verification_status"],
            "missing",
        )
        self.assertEqual(evidence["rollout_confirmation_decision_status"], "blocked")
        self.assertEqual(
            evidence["rollout_confirmation_input_source_status"],
            "blocked",
        )
        self.assertIn(
            "input_source_kind",
            evidence["rollout_confirmation_input_missing_sections"],
        )
        self.assertFalse(evidence["rollout_decision_recorded"])
        self.assertEqual(evidence["rollout_target_store_mode"], "")
        self.assertIn(
            "decision_recorded",
            evidence["rollout_confirmation_missing_sections"],
        )
        self.assertFalse(evidence["rollout_confirmation_production_rollout_confirmed"])
        self.assertIn("strict_mode_rollout", evidence["rollout_missing_sections"])
        self.assertIn("rollout_checklist", gate["missing_sections"])

    def test_production_gate_requires_rollout_confirmation(self):
        rollout = build_worker_ownership_rollout_readiness_contract(
            strict_mode_rollout_confirmed=True,
            fallback_policy_confirmed=True,
            migration_ready=True,
            renewal_verification_ready=True,
            stale_fencing_verified=True,
            auto_claim_decision_recorded=True,
            audit_evidence_ready=True,
            rollback_plan_ready=True,
            production_rollout_confirmed=False,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            rollout_readiness_contract=rollout,
        )

        section = next(item for item in gate["sections"] if item["name"] == "rollout_checklist")
        self.assertEqual(rollout["overall_status"], "ready")
        self.assertFalse(section["ready"])
        self.assertIn("rollout_checklist", gate["missing_sections"])
        self.assertFalse(gate["production_default_enabled"])

    def test_auto_claim_policy_contract_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_auto_claim_policy_contract(
            descriptor_evidence_fallback=True,
            lease_validation_required=True,
        )

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-auto-claim-policy-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["auto_claim_enabled_by_default"])
        self.assertTrue(contract["policy"]["descriptor_evidence_fallback"])
        self.assertTrue(contract["policy"]["lease_validation_required"])
        self.assertTrue(contract["policy"]["entrypoint_allowlist_ready"])
        self.assertEqual(contract["policy"]["entrypoint_allowlist"]["overall_status"], "ready")
        self.assertIn(
            "submit_approval.approved",
            contract["policy"]["entrypoint_allowlist"]["allowed_entrypoints"],
        )
        self.assertIn("explicit_runtime_configuration", contract["missing_sections"])
        self.assertNotIn("entrypoint_allowlist", contract["missing_sections"])
        self.assertIn("no_default_recovery_entry_auto_claim", contract["non_goals"])

    def test_auto_claim_entrypoint_allowlist_contract_defaults_to_ready_without_enablement(self):
        contract = build_worker_ownership_auto_claim_entrypoint_allowlist_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1",
        )
        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["ready"])
        self.assertIn("submit_approval.approved", contract["allowed_entrypoints"])
        self.assertIn("resume_run.continue_loop", contract["allowed_entrypoints"])
        self.assertEqual(contract["missing_entrypoints"], [])
        self.assertFalse(contract["default_auto_claim_enabled"])
        self.assertTrue(contract["requires_production_gate_ready"])
        self.assertIn("no_claim_run_side_effect", contract["non_goals"])

    def test_explicit_auto_claim_enablement_gate_defaults_to_blocked(self):
        contract = build_worker_ownership_explicit_auto_claim_enablement_gate_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["will_auto_claim"])
        self.assertEqual(contract["blocked_reason"], "explicit_runtime_configuration_missing")
        self.assertIn("explicit_runtime_configuration", contract["missing_sections"])
        self.assertIn("production_gate_ready", contract["missing_sections"])
        self.assertIn("no_claim_run_side_effect", contract["non_goals"])

    def test_explicit_auto_claim_enablement_gate_blocks_non_allowlisted_entrypoint(self):
        contract = build_worker_ownership_explicit_auto_claim_enablement_gate_contract(
            explicit_runtime_configuration=True,
            production_gate_ready=True,
            durable_ownership_ready=True,
            descriptor_evidence_fallback=True,
            idempotency_evidence_ready=True,
            audit_evidence_ready=True,
            lease_validation_ready=True,
            rollout_auto_claim_decision_recorded=True,
            requested_entrypoint="unknown.entrypoint",
        )

        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["will_auto_claim"])
        self.assertEqual(contract["blocked_reason"], "entrypoint_not_allowlisted")
        self.assertIn("entrypoint_allowlisted", contract["missing_sections"])

    def test_explicit_auto_claim_enablement_gate_can_be_ready_when_all_inputs_ready(self):
        contract = build_worker_ownership_explicit_auto_claim_enablement_gate_contract(
            explicit_runtime_configuration=True,
            production_gate_ready=True,
            durable_ownership_ready=True,
            descriptor_evidence_fallback=True,
            idempotency_evidence_ready=True,
            audit_evidence_ready=True,
            lease_validation_ready=True,
            rollout_auto_claim_decision_recorded=True,
            requested_entrypoint="submit_approval.approved",
        )

        self.assertEqual(contract["overall_status"], "ready")
        self.assertTrue(contract["will_auto_claim"])
        self.assertEqual(contract["missing_sections"], [])
        self.assertEqual(contract["blocked_reason"], "")

    def test_production_gate_embeds_auto_claim_policy_blocker_evidence(self):
        policy = build_worker_ownership_auto_claim_policy_contract(
            descriptor_evidence_fallback=True,
            lease_validation_required=True,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            auto_claim_policy_contract=policy,
        )

        section = next(
            item for item in gate["sections"] if item["name"] == "recovery_entry_auto_claim_policy"
        )
        evidence = section["evidence"]
        self.assertEqual(section["status"], "blocked")
        self.assertFalse(section["ready"])
        self.assertEqual(evidence["auto_claim_policy_status"], "blocked")
        self.assertFalse(evidence["auto_claim_enabled_by_default"])
        self.assertTrue(evidence["descriptor_evidence_fallback"])
        self.assertTrue(evidence["lease_validation_required"])
        self.assertTrue(evidence["entrypoint_allowlist_ready"])
        self.assertEqual(
            evidence["auto_claim_entrypoint_allowlist_contract_version"],
            "phase-ii-worker-ownership-auto-claim-entrypoint-allowlist-v1",
        )
        self.assertEqual(evidence["auto_claim_entrypoint_allowlist_status"], "ready")
        self.assertIn("submit_approval.approved", evidence["auto_claim_allowed_entrypoints"])
        self.assertIn("resume_run.continue_loop", evidence["auto_claim_allowed_entrypoints"])
        self.assertEqual(evidence["auto_claim_missing_entrypoints"], [])
        self.assertFalse(evidence["auto_claim_default_auto_claim_enabled"])
        self.assertTrue(evidence["auto_claim_requires_production_gate_ready"])
        self.assertEqual(
            evidence["auto_claim_enablement_gate_contract_version"],
            "phase-ii-worker-ownership-explicit-auto-claim-enablement-gate-v1",
        )
        self.assertEqual(evidence["auto_claim_enablement_gate_status"], "blocked")
        self.assertFalse(evidence["auto_claim_will_auto_claim"])
        self.assertIn(
            "explicit_runtime_configuration",
            evidence["auto_claim_enablement_missing_sections"],
        )
        self.assertEqual(
            evidence["auto_claim_enablement_blocked_reason"],
            "explicit_runtime_configuration_missing",
        )
        self.assertIn("explicit_runtime_configuration", evidence["auto_claim_missing_sections"])
        self.assertIn("recovery_entry_auto_claim_policy", gate["missing_sections"])

    def test_production_gate_requires_auto_claim_default_enablement(self):
        policy = build_worker_ownership_auto_claim_policy_contract(
            explicit_runtime_configuration=True,
            production_gate_ready_required=True,
            durable_ownership_required=True,
            descriptor_evidence_fallback=True,
            idempotency_evidence_ready=True,
            audit_evidence_ready=True,
            entrypoint_allowlist_ready=True,
            lease_validation_required=True,
            auto_claim_enabled_by_default=False,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            auto_claim_policy_contract=policy,
        )

        section = next(
            item for item in gate["sections"] if item["name"] == "recovery_entry_auto_claim_policy"
        )
        self.assertEqual(policy["overall_status"], "ready")
        self.assertFalse(section["ready"])
        self.assertIn("recovery_entry_auto_claim_policy", gate["missing_sections"])
        self.assertFalse(gate["production_default_enabled"])

    def test_ownership_audit_evidence_contract_defaults_to_blocked_readiness(self):
        contract = build_worker_ownership_audit_evidence_contract()

        self.assertEqual(
            contract["contract_version"],
            "phase-ii-worker-ownership-audit-evidence-v1",
        )
        self.assertEqual(contract["overall_status"], "blocked")
        self.assertFalse(contract["ready"])
        self.assertFalse(contract["authorization_source"])
        self.assertTrue(contract["evidence"]["compact_ownership_evidence"])
        self.assertFalse(contract["evidence"]["operation_history_ready"])
        self.assertFalse(contract["evidence"]["timeline_writer_ready"])
        self.assertIn("operation_history", contract["missing_sections"])
        self.assertIn("idempotent_dedupe", contract["missing_sections"])
        self.assertIn("no_audit_as_authorization_source", contract["non_goals"])

    def test_production_gate_embeds_ownership_audit_blocker_evidence(self):
        audit = build_worker_ownership_audit_evidence_contract()

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            audit_evidence_contract=audit,
        )

        section = next(item for item in gate["sections"] if item["name"] == "ownership_audit_evidence")
        evidence = section["evidence"]
        self.assertEqual(section["status"], "blocked")
        self.assertFalse(section["ready"])
        self.assertEqual(evidence["ownership_audit_status"], "blocked")
        self.assertTrue(evidence["compact_ownership_evidence"])
        self.assertFalse(evidence["operation_history_ready"])
        self.assertFalse(evidence["timeline_writer_ready"])
        self.assertFalse(evidence["authorization_source"])
        self.assertIn("operation_history", evidence["ownership_audit_missing_sections"])
        self.assertIn("ownership_audit_evidence", gate["missing_sections"])

    def test_production_gate_rejects_audit_evidence_as_authorization_source(self):
        audit = build_worker_ownership_audit_evidence_contract(
            compact_ownership_evidence=True,
            operation_history_ready=True,
            recovery_operation_link_ready=True,
            timeline_writer_ready=True,
            idempotent_dedupe_ready=True,
            authorization_source=True,
        )

        gate = build_worker_ownership_production_gate_contract(
            ownership_contract=build_worker_ownership_contract(adapter_kind="sqlalchemy", durable=True),
            store_mode="strict_sql",
            migration_ready=True,
            audit_evidence_contract=audit,
        )

        section = next(item for item in gate["sections"] if item["name"] == "ownership_audit_evidence")
        self.assertEqual(audit["overall_status"], "blocked")
        self.assertIn("non_authorization_source", audit["missing_sections"])
        self.assertFalse(section["ready"])
        self.assertTrue(section["evidence"]["authorization_source"])
        self.assertIn("ownership_audit_evidence", gate["missing_sections"])
        self.assertFalse(gate["production_default_enabled"])

    def test_first_claim_succeeds_and_parallel_worker_claim_fails_closed(self):
        store, _clock = self._store_with_clock()

        first = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)
        second = store.claim_run("run-1", "worker-b", lease_ttl_seconds=30)

        self.assertTrue(first["owned"])
        self.assertEqual(first["lease_status"], WORKER_OWNERSHIP_STATUS_CLAIMED)
        self.assertEqual(first["run_id"], "run-1")
        self.assertEqual(first["worker_id"], "worker-a")
        self.assertGreater(first["fencing_token"], 0)
        self.assertFalse(second["owned"])
        self.assertEqual(second["lease_status"], WORKER_OWNERSHIP_STATUS_BLOCKED)
        self.assertEqual(second["reason"], WORKER_OWNERSHIP_REASON_WORKER_OWNERSHIP_LOST)
        self.assertEqual(second["worker_id"], "worker-a")

    def test_heartbeat_extends_expiration_and_preserves_fencing_token(self):
        store, clock = self._store_with_clock()
        first = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)
        first_expiration = first["lease_expires_at"]
        clock["now"] = clock["now"] + timedelta(seconds=10)

        heartbeat = store.heartbeat(
            "run-1",
            "worker-a",
            first["lease_id"],
            lease_ttl_seconds=60,
        )

        self.assertTrue(heartbeat["owned"])
        self.assertEqual(heartbeat["lease_status"], WORKER_OWNERSHIP_STATUS_REFRESHED)
        self.assertEqual(heartbeat["lease_id"], first["lease_id"])
        self.assertEqual(heartbeat["fencing_token"], first["fencing_token"])
        self.assertGreater(heartbeat["lease_expires_at"], first_expiration)

    def test_expired_lease_can_be_replaced_with_higher_fencing_token(self):
        store, clock = self._store_with_clock()
        first = store.claim_run("run-1", "worker-a", lease_ttl_seconds=5)
        clock["now"] = clock["now"] + timedelta(seconds=6)

        expired_validation = store.validate_ownership(
            "run-1",
            "worker-a",
            first["lease_id"],
            first["fencing_token"],
        )
        replacement = store.claim_run("run-1", "worker-b", lease_ttl_seconds=30)

        self.assertFalse(expired_validation["owned"])
        self.assertEqual(expired_validation["reason"], WORKER_OWNERSHIP_REASON_LEASE_EXPIRED)
        self.assertTrue(replacement["owned"])
        self.assertEqual(replacement["worker_id"], "worker-b")
        self.assertGreater(replacement["fencing_token"], first["fencing_token"])

    def test_stale_fencing_token_validation_fails_closed(self):
        store, _clock = self._store_with_clock()
        claim = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)

        validation = store.validate_ownership(
            "run-1",
            "worker-a",
            claim["lease_id"],
            claim["fencing_token"] - 1,
        )

        self.assertFalse(validation["owned"])
        self.assertEqual(validation["lease_status"], WORKER_OWNERSHIP_STATUS_BLOCKED)
        self.assertEqual(validation["reason"], WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN)

    def test_valid_ownership_returns_compact_validated_evidence(self):
        store, _clock = self._store_with_clock()
        claim = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)

        validation = store.validate_ownership(
            "run-1",
            "worker-a",
            claim["lease_id"],
            claim["fencing_token"],
        )

        self.assertTrue(validation["owned"])
        self.assertEqual(validation["lease_status"], WORKER_OWNERSHIP_STATUS_VALIDATED)
        self.assertEqual(validation["lease_id"], claim["lease_id"])

    def test_recovery_operation_record_preserves_default_unimplemented_ownership(self):
        record = build_recovery_operation_record(
            run_id="run-1",
            entrypoint="submit_approval.approved",
            operation_status="recovered",
            recovery_reason="ready_via_registry",
            continuation_kind="tool_approval",
            continuation_id="approval-1",
            workspace_backend={"backend_kind": "sqlalchemy", "backend_mode": "strict", "durable": True},
            recorded_at="2026-05-23T09:00:00+00:00",
        )

        self.assertFalse(record["worker_ownership"]["implemented"])
        self.assertEqual(
            record["worker_ownership"]["blocked_reason"],
            "worker_ownership_not_implemented",
        )

    def test_recovery_operation_record_compacts_supplied_worker_ownership(self):
        store, _clock = self._store_with_clock()
        ownership = store.claim_run("run-1", "worker-a", lease_ttl_seconds=30)
        ownership["handler"] = lambda: None

        record = build_recovery_operation_record(
            run_id="run-1",
            entrypoint="submit_approval.approved",
            operation_status="recovered",
            recovery_reason="ready_via_registry",
            continuation_kind="tool_approval",
            continuation_id="approval-1",
            workspace_backend={"backend_kind": "sqlalchemy", "backend_mode": "strict", "durable": True},
            recorded_at="2026-05-23T09:00:00+00:00",
            worker_ownership=ownership,
        )

        compact = record["worker_ownership"]
        self.assertTrue(compact["implemented"])
        self.assertEqual(compact["worker_id"], "worker-a")
        self.assertEqual(compact["lease_id"], ownership["lease_id"])
        self.assertEqual(compact["fencing_token"], ownership["fencing_token"])
        self.assertEqual(compact["lease_status"], WORKER_OWNERSHIP_STATUS_CLAIMED)
        self.assertNotIn("handler", compact)

    def test_default_runtime_worker_ownership_store_mode_is_memory_only(self):
        with patch.object(worker_ownership_module, "_runtime_worker_ownership_store", None):
            with patch.object(worker_ownership_module, "_runtime_worker_ownership_store_mode", None):
                with patch.object(worker_ownership_module, "WORKER_OWNERSHIP_STORE_MODE", "memory_only"):
                    store = get_runtime_worker_ownership_store()

        self.assertIsInstance(store, InMemoryRuntimeWorkerOwnershipStore)
        self.assertEqual(worker_ownership_module.get_worker_ownership_store_mode(), "memory_only")

    def test_set_worker_ownership_store_mode_resets_singleton(self):
        original_mode = worker_ownership_module.WORKER_OWNERSHIP_STORE_MODE
        try:
            with patch.object(worker_ownership_module, "_runtime_worker_ownership_store", object()):
                with patch.object(worker_ownership_module, "_runtime_worker_ownership_store_mode", "memory_only"):
                    mode = set_worker_ownership_store_mode("prefer_sql_with_fallback")

                    self.assertEqual(mode, "prefer_sql_with_fallback")
                    self.assertIsNone(worker_ownership_module._runtime_worker_ownership_store)
                    self.assertIsNone(worker_ownership_module._runtime_worker_ownership_store_mode)
        finally:
            set_worker_ownership_store_mode(original_mode)

    def test_runtime_worker_ownership_strict_sql_initialization_fails_closed(self):
        with patch.object(worker_ownership_module, "_runtime_worker_ownership_store", None):
            with patch.object(worker_ownership_module, "_runtime_worker_ownership_store_mode", None):
                with patch.object(worker_ownership_module, "WORKER_OWNERSHIP_STORE_MODE", "strict_sql"):
                    with patch.object(
                        worker_ownership_module.SQLAlchemyRuntimeWorkerOwnershipStore,
                        "__init__",
                        side_effect=RuntimeError("db unavailable"),
                    ):
                        with self.assertRaisesRegex(RuntimeError, "strict_sql mode requires a working SQL backend"):
                            get_runtime_worker_ownership_store()

    def test_runtime_worker_ownership_prefer_sql_can_fallback_to_memory(self):
        with patch.object(worker_ownership_module, "_runtime_worker_ownership_store", None):
            with patch.object(worker_ownership_module, "_runtime_worker_ownership_store_mode", None):
                with patch.object(worker_ownership_module, "WORKER_OWNERSHIP_STORE_MODE", "prefer_sql_with_fallback"):
                    with patch.object(
                        worker_ownership_module.SQLAlchemyRuntimeWorkerOwnershipStore,
                        "__init__",
                        side_effect=RuntimeError("db unavailable"),
                    ):
                        store = get_runtime_worker_ownership_store()

        self.assertIsInstance(store, WorkerOwnershipStoreFallback)
        contract = store.build_contract()
        self.assertEqual(contract["adapter_kind"], "in_memory")
        self.assertEqual(contract["configured_mode"], "prefer_sql_with_fallback")
        self.assertTrue(contract["fallback_active"])
        self.assertIn("db unavailable", contract["fallback_reason"])

    def test_production_gate_composition_dry_run_defaults_to_blocked(self):
        dry_run = build_worker_ownership_production_gate_composition_dry_run_contract()

        self.assertEqual(
            dry_run["contract_version"],
            "phase-ii-worker-ownership-production-gate-composition-dry-run-v1",
        )
        self.assertEqual(dry_run["overall_status"], "blocked")
        self.assertFalse(dry_run["all_required_sections_ready"])
        self.assertFalse(dry_run["production_default_would_be_allowed"])
        self.assertIn("vendor_lock_wiring_decision", dry_run["missing_sections"])
        self.assertIn("heartbeat_renewal_supervisor", dry_run["missing_sections"])
        self.assertIn("rollout_confirmation", dry_run["missing_sections"])
        self.assertIn("recovery_entry_auto_claim_enablement", dry_run["missing_sections"])
        self.assertIn("ownership_audit_evidence", dry_run["missing_sections"])
        self.assertIn(
            "production_default_enablement_input_source",
            dry_run["missing_sections"],
        )
        self.assertFalse(dry_run["will_enable_production_default"])
        self.assertFalse(dry_run["executes_lock"])
        self.assertFalse(dry_run["starts_background_worker"])
        self.assertFalse(dry_run["runs_recovery_auto_claim"])

    def test_production_gate_composition_dry_run_can_be_ready_without_side_effects(self):
        dry_run = build_worker_ownership_production_gate_composition_dry_run_contract(
            vendor_lock_wiring_decision_contract={
                "overall_status": "ready",
                "wiring_allowed": True,
                "will_update_production_gate": False,
                "will_enable_production_lock": False,
                "executes_advisory_lock": False,
            },
            renewal_supervisor_contract=build_worker_ownership_renewal_supervisor_contract(
                heartbeat_operation_present=True,
                renew_once_supported=True,
                owner_identity_required=True,
                controlled_lifecycle_supported=True,
                starts_by_default=False,
                active=False,
                stop_supported=True,
                failure_fail_closed=True,
                background_supervisor_present=True,
                renewal_owner_identity_present=True,
                ttl_interval_policy_present=True,
                lease_loss_fail_closed=True,
                supervisor_enabled_by_default=True,
            ),
            rollout_confirmation_decision_contract={
                "overall_status": "ready",
                "production_rollout_confirmed": True,
            },
            auto_claim_enablement_gate_contract={
                "overall_status": "ready",
                "will_auto_claim": True,
            },
            ownership_audit_evidence_contract=build_worker_ownership_audit_evidence_contract(
                compact_ownership_evidence=True,
                operation_history_ready=True,
                recovery_operation_link_ready=True,
                timeline_writer_ready=True,
                idempotent_dedupe_ready=True,
                authorization_source=False,
            ),
            production_default_enablement_input_source_contract=(
                build_worker_ownership_production_default_enablement_input_source_contract(
                    input_source_kind="rollout_artifact",
                    request_id="enable-prod-001",
                    requested_by="runtime-ops",
                    requested_at="2026-05-25T10:00:00Z",
                    target_store_mode="strict_sql",
                    rollout_artifact="worker-ownership-rollout-001",
                    vendor_lock_decision_id="pg-wire-001",
                    renewal_lifecycle_reference="renewal-lifecycle-001",
                    auto_claim_decision_reference="auto-claim-001",
                    audit_evidence_reference="audit-001",
                    rollback_plan_reference="rollback-001",
                    fallback_policy_reference="fallback-001",
                )
            ),
        )

        self.assertEqual(dry_run["overall_status"], "ready")
        self.assertTrue(dry_run["all_required_sections_ready"])
        self.assertTrue(dry_run["production_default_would_be_allowed"])
        self.assertEqual(dry_run["missing_sections"], [])
        self.assertFalse(dry_run["will_enable_production_default"])
        self.assertFalse(dry_run["executes_lock"])
        self.assertFalse(dry_run["starts_background_worker"])
        self.assertFalse(dry_run["runs_recovery_auto_claim"])
        self.assertTrue(dry_run["evidence"]["vendor_lock_wiring_allowed"])
        self.assertTrue(
            dry_run["evidence"]["renewal_supervisor_enabled_by_default"]
        )

    def test_production_enablement_runtime_config_consumer_defaults_to_blocked(self):
        consumer = (
            build_worker_ownership_production_enablement_runtime_config_consumer_contract()
        )

        self.assertEqual(
            consumer["contract_version"],
            (
                "phase-ii-worker-ownership-production-enablement-runtime-config"
                "-consumer-v1"
            ),
        )
        self.assertEqual(consumer["overall_status"], "blocked")
        self.assertFalse(consumer["ready"])
        self.assertIn("source_kind", consumer["missing_sections"])
        self.assertIn("config_id", consumer["missing_sections"])
        self.assertIn("enablement_input_source", consumer["missing_sections"])
        self.assertIn("composition_dry_run", consumer["missing_sections"])
        self.assertEqual(
            consumer["enablement_input_source"]["overall_status"], "blocked"
        )
        self.assertEqual(consumer["composition_dry_run"]["overall_status"], "blocked")
        self.assertFalse(consumer["will_enable_production_default"])
        self.assertFalse(consumer["executes_lock"])
        self.assertFalse(consumer["starts_background_worker"])
        self.assertFalse(consumer["runs_recovery_auto_claim"])

    def test_production_enablement_runtime_config_consumer_can_be_ready_without_side_effects(
        self,
    ):
        input_source = build_worker_ownership_production_default_enablement_input_source_contract(
            input_source_kind="config",
            request_id="prod-enable-config-001",
            requested_by="runtime-ops",
            requested_at="2026-05-25T12:00:00Z",
            target_store_mode="strict_sql",
            rollout_artifact="rollout/worker-ownership/pg-rollout-001",
            vendor_lock_decision_id="pg-wire-001",
            renewal_lifecycle_reference="renewal-supervisor-controlled-v1",
            auto_claim_decision_reference="auto-claim-decision-001",
            audit_evidence_reference="ownership-audit-001",
            rollback_plan_reference="rollback-worker-ownership-001",
            fallback_policy_reference="fallback-worker-ownership-001",
        )
        dry_run = build_worker_ownership_production_gate_composition_dry_run_contract(
            vendor_lock_wiring_decision_contract={
                "overall_status": "ready",
                "wiring_allowed": True,
                "will_update_production_gate": False,
                "will_enable_production_lock": False,
                "executes_advisory_lock": False,
            },
            renewal_supervisor_contract={
                "overall_status": "ready",
                "supervisor_enabled_by_default": True,
                "policy": {
                    "controlled_lifecycle_supported": True,
                    "failure_fail_closed": True,
                },
            },
            rollout_confirmation_decision_contract={
                "overall_status": "ready",
                "production_rollout_confirmed": True,
            },
            auto_claim_enablement_gate_contract={
                "overall_status": "ready",
                "will_auto_claim": True,
            },
            ownership_audit_evidence_contract={
                "overall_status": "ready",
                "authorization_source": False,
            },
            production_default_enablement_input_source_contract=input_source,
        )

        consumer = build_worker_ownership_production_enablement_runtime_config_consumer_contract(
            config={
                "source_kind": "runtime_config",
                "config_id": "prod-enable-config-001",
                "approved_by": "runtime-ops",
                "approved_at": "2026-05-25T12:00:00Z",
                "target_store_mode": "strict_sql",
                "target_backend": "postgres",
                "lock_adapter_kind": "postgres_advisory_lock",
                "rollout_artifact": "rollout/worker-ownership/pg-rollout-001",
                "vendor_lock_decision_id": "pg-wire-001",
                "renewal_lifecycle_reference": "renewal-supervisor-controlled-v1",
                "auto_claim_decision_reference": "auto-claim-decision-001",
                "audit_evidence_reference": "ownership-audit-001",
                "rollback_plan_reference": "rollback-worker-ownership-001",
                "fallback_policy_reference": "fallback-worker-ownership-001",
            },
            composition_dry_run_contract=dry_run,
        )

        self.assertEqual(consumer["overall_status"], "ready")
        self.assertEqual(consumer["missing_sections"], [])
        self.assertEqual(consumer["source_kind"], "runtime_config")
        self.assertEqual(consumer["target_backend"], "postgres")
        self.assertEqual(consumer["lock_adapter_kind"], "postgres_advisory_lock")
        self.assertEqual(
            consumer["enablement_input_source"]["overall_status"], "ready"
        )
        self.assertEqual(consumer["composition_dry_run"]["overall_status"], "ready")
        self.assertTrue(consumer["composition_dry_run_would_allow"])
        self.assertFalse(consumer["will_enable_production_default"])
        self.assertFalse(consumer["executes_lock"])
        self.assertFalse(consumer["starts_background_worker"])
        self.assertFalse(consumer["runs_recovery_auto_claim"])


class SQLAlchemyRuntimeWorkerOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.clock = {"now": datetime(2026, 5, 23, 10, 0, 0, tzinfo=timezone.utc)}

        def _now():
            return self.clock["now"]

        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.store = SQLAlchemyRuntimeWorkerOwnershipStore(self.SessionLocal, now_fn=_now)
        self.second_store = SQLAlchemyRuntimeWorkerOwnershipStore(self.SessionLocal, now_fn=_now)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_sqlalchemy_contract_declares_durable_adapter(self):
        contract = self.store.build_contract()

        self.assertEqual(contract["adapter_kind"], "sqlalchemy")
        self.assertTrue(contract["durable"])
        self.assertIn("claim_run", contract["operations"])
        self.assertIn("validate_ownership", contract["operations"])

    def test_sqlalchemy_operational_readiness_reports_durable_row_lease_posture(self):
        readiness = build_worker_ownership_operational_readiness_contract(
            ownership_contract=self.store.build_contract(),
            store_mode="strict_sql",
            auto_claim_enabled=True,
        )

        self.assertTrue(readiness["production_ready"])
        self.assertEqual(readiness["readiness_status"], "production_ready")
        self.assertEqual(readiness["vendor_lock_posture"], "sql_row_lease_fencing")
        self.assertEqual(readiness["recovery_entry_claim_mode"], "opt_in_auto_claim")
        self.assertTrue(readiness["migration_checklist"]["migration_ready"])
        self.assertEqual(readiness["production_gate"]["overall_status"], "blocked")
        self.assertIn("vendor_lock_semantics", readiness["production_gate"]["missing_sections"])
        self.assertFalse(readiness["production_gate"]["production_default_enabled"])

    def test_sqlalchemy_claim_survives_new_store_instance_and_blocks_competing_worker(self):
        claim = self.store.claim_run("run-sql-1", "worker-a", lease_ttl_seconds=30)

        persisted = self.second_store.get_lease("run-sql-1")
        competing = self.second_store.claim_run("run-sql-1", "worker-b", lease_ttl_seconds=30)

        self.assertTrue(claim["owned"])
        self.assertTrue(claim["durable"])
        self.assertEqual(claim["adapter_kind"], "sqlalchemy")
        self.assertEqual(persisted["lease_id"], claim["lease_id"])
        self.assertFalse(competing["owned"])
        self.assertEqual(competing["reason"], WORKER_OWNERSHIP_REASON_WORKER_OWNERSHIP_LOST)
        self.assertEqual(competing["worker_id"], "worker-a")

    def test_sqlalchemy_expired_lease_can_be_replaced_with_higher_fencing_token(self):
        first = self.store.claim_run("run-sql-1", "worker-a", lease_ttl_seconds=5)
        self.clock["now"] = self.clock["now"] + timedelta(seconds=6)

        expired = self.second_store.validate_ownership(
            "run-sql-1",
            "worker-a",
            first["lease_id"],
            first["fencing_token"],
        )
        replacement = self.second_store.claim_run("run-sql-1", "worker-b", lease_ttl_seconds=30)

        self.assertFalse(expired["owned"])
        self.assertEqual(expired["reason"], WORKER_OWNERSHIP_REASON_LEASE_EXPIRED)
        self.assertTrue(replacement["owned"])
        self.assertEqual(replacement["worker_id"], "worker-b")
        self.assertGreater(replacement["fencing_token"], first["fencing_token"])

    def test_sqlalchemy_heartbeat_extends_expiration_and_preserves_fencing(self):
        claim = self.store.claim_run("run-sql-1", "worker-a", lease_ttl_seconds=30)
        first_expiration = claim["lease_expires_at"]
        self.clock["now"] = self.clock["now"] + timedelta(seconds=10)

        heartbeat = self.second_store.heartbeat(
            "run-sql-1",
            "worker-a",
            claim["lease_id"],
            lease_ttl_seconds=60,
        )

        self.assertTrue(heartbeat["owned"])
        self.assertEqual(heartbeat["lease_status"], WORKER_OWNERSHIP_STATUS_REFRESHED)
        self.assertEqual(heartbeat["fencing_token"], claim["fencing_token"])
        self.assertGreater(heartbeat["lease_expires_at"], first_expiration)

    def test_sqlalchemy_stale_fencing_token_fails_closed(self):
        claim = self.store.claim_run("run-sql-1", "worker-a", lease_ttl_seconds=30)

        validation = self.second_store.validate_ownership(
            "run-sql-1",
            "worker-a",
            claim["lease_id"],
            claim["fencing_token"] - 1,
        )

        self.assertFalse(validation["owned"])
        self.assertEqual(validation["lease_status"], WORKER_OWNERSHIP_STATUS_BLOCKED)
        self.assertEqual(validation["reason"], WORKER_OWNERSHIP_REASON_STALE_FENCING_TOKEN)

    def test_runtime_factory_contract_uses_sqlalchemy_ownership_contract_when_injected(self):
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=InMemoryEmbeddedRunWorkspaceStore(),
                continuation_registry=InMemoryEmbeddedContinuationRegistry(),
                worker_ownership_store=self.store,
            )
        )

        contract = factory.build_runtime_contract()

        self.assertTrue(contract["worker_ownership"]["available"])
        self.assertEqual(contract["worker_ownership"]["adapter_kind"], "sqlalchemy")
        self.assertTrue(contract["worker_ownership"]["durable"])
        self.assertEqual(contract["worker_ownership"]["enforcement_mode"], "opt_in_descriptor_evidence")
        readiness = contract["worker_ownership"]["operational_readiness"]
        self.assertEqual(readiness["contract_version"], "phase-ii-worker-ownership-operations-v1")
        self.assertTrue(readiness["production_ready"])
        self.assertEqual(readiness["vendor_lock_posture"], "sql_row_lease_fencing")
        production_gate = contract["worker_ownership"]["production_gate"]
        self.assertEqual(production_gate["contract_version"], "phase-ii-worker-ownership-production-gate-v1")
        self.assertEqual(production_gate["overall_status"], "blocked")
        self.assertIn("vendor_lock_semantics", production_gate["missing_sections"])

    def test_runtime_factory_contract_defaults_config_consumer_to_blocked(self):
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=InMemoryEmbeddedRunWorkspaceStore(),
                continuation_registry=InMemoryEmbeddedContinuationRegistry(),
                worker_ownership_store=self.store,
            )
        )

        contract = factory.build_runtime_contract()
        consumer = contract["worker_ownership"][
            "production_enablement_runtime_config_consumer"
        ]

        self.assertEqual(consumer["overall_status"], "blocked")
        self.assertIn("source_kind", consumer["missing_sections"])
        self.assertIn("config_id", consumer["missing_sections"])
        self.assertFalse(consumer["will_enable_production_default"])
        self.assertFalse(consumer["executes_lock"])
        self.assertFalse(consumer["starts_background_worker"])
        self.assertFalse(consumer["runs_recovery_auto_claim"])

    def test_runtime_factory_contract_binds_production_enablement_config_consumer(
        self,
    ):
        input_source = build_worker_ownership_production_default_enablement_input_source_contract(
            input_source_kind="config",
            request_id="prod-enable-factory-001",
            requested_by="runtime-ops",
            requested_at="2026-05-25T13:00:00Z",
            target_store_mode="strict_sql",
            rollout_artifact="rollout/worker-ownership/pg-rollout-factory",
            vendor_lock_decision_id="pg-wire-factory",
            renewal_lifecycle_reference="renewal-factory",
            auto_claim_decision_reference="auto-claim-factory",
            audit_evidence_reference="audit-factory",
            rollback_plan_reference="rollback-factory",
            fallback_policy_reference="fallback-factory",
        )
        dry_run = build_worker_ownership_production_gate_composition_dry_run_contract(
            vendor_lock_wiring_decision_contract={
                "overall_status": "ready",
                "wiring_allowed": True,
                "will_update_production_gate": False,
                "will_enable_production_lock": False,
                "executes_advisory_lock": False,
            },
            renewal_supervisor_contract={
                "overall_status": "ready",
                "supervisor_enabled_by_default": True,
                "policy": {
                    "controlled_lifecycle_supported": True,
                    "failure_fail_closed": True,
                },
            },
            rollout_confirmation_decision_contract={
                "overall_status": "ready",
                "production_rollout_confirmed": True,
            },
            auto_claim_enablement_gate_contract={
                "overall_status": "ready",
                "will_auto_claim": True,
            },
            ownership_audit_evidence_contract={
                "overall_status": "ready",
                "authorization_source": False,
            },
            production_default_enablement_input_source_contract=input_source,
        )
        factory = EmbeddedRuntimeFactory(
            dependencies=EmbeddedRuntimeDependencies(
                workspace_store=InMemoryEmbeddedRunWorkspaceStore(),
                continuation_registry=InMemoryEmbeddedContinuationRegistry(),
                worker_ownership_store=self.store,
            ),
            worker_ownership_production_enablement_config={
                "source_kind": "runtime_config",
                "config_id": "prod-enable-factory-001",
                "approved_by": "runtime-ops",
                "approved_at": "2026-05-25T13:00:00Z",
                "target_store_mode": "strict_sql",
                "target_backend": "postgres",
                "lock_adapter_kind": "postgres_advisory_lock",
                "rollout_artifact": "rollout/worker-ownership/pg-rollout-factory",
                "vendor_lock_decision_id": "pg-wire-factory",
                "renewal_lifecycle_reference": "renewal-factory",
                "auto_claim_decision_reference": "auto-claim-factory",
                "audit_evidence_reference": "audit-factory",
                "rollback_plan_reference": "rollback-factory",
                "fallback_policy_reference": "fallback-factory",
                "composition_dry_run": dry_run,
            },
        )

        contract = factory.build_runtime_contract()
        consumer = contract["worker_ownership"][
            "production_enablement_runtime_config_consumer"
        ]

        self.assertEqual(consumer["overall_status"], "ready")
        self.assertEqual(consumer["config_id"], "prod-enable-factory-001")
        self.assertEqual(consumer["enablement_input_source"]["overall_status"], "ready")
        self.assertEqual(consumer["composition_dry_run"]["overall_status"], "ready")
        self.assertFalse(consumer["will_enable_production_default"])
        self.assertFalse(consumer["executes_lock"])
        self.assertFalse(consumer["starts_background_worker"])
        self.assertFalse(consumer["runs_recovery_auto_claim"])


if __name__ == "__main__":
    unittest.main()
