"""Contract builders used by RuntimeSurfaceService."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict


class RuntimeRecoveryContractBuilder:
    """Assemble runtime recovery contracts from normalized probe/factory inputs."""

    STATE_GATED_BLOCKED_REASONS = {"approval_already_resolved"}
    RECOVERY_OPERATION_FIELDS = {
        "contract_version",
        "operation_id",
        "run_id",
        "entrypoint",
        "operation_status",
        "recovery_reason",
        "blocked_reason",
        "checkpoint_id",
        "resume_cursor_id",
        "continuation_ref",
        "workspace_backend",
        "persistence_posture",
        "worker_ownership",
        "retry",
        "recorded_at",
    }

    @staticmethod
    def derive_recovery_mode(recovery_reasons: set[str] | list[str] | tuple[str, ...]) -> str:
        normalized_reasons = {
            str(reason or "").strip()
            for reason in recovery_reasons
            if str(reason or "").strip()
        }
        if "ready_via_registry" in normalized_reasons:
            return "registry_backed"
        if "ready_in_process" in normalized_reasons:
            return "in_process"
        return "unavailable"

    @classmethod
    def build_recovery_capabilities_summary(
        cls,
        recovery_reasons: set[str] | list[str] | tuple[str, ...],
    ) -> Dict[str, Any]:
        recovery_mode = cls.derive_recovery_mode(recovery_reasons)
        return {
            "recovery_mode": recovery_mode,
            "requires_durable_workspace": recovery_mode == "registry_backed",
            "requires_registry_bindings": recovery_mode == "registry_backed",
        }

    @staticmethod
    def _index_recovery_entrypoints(
        entrypoints: list[Dict[str, Any]] | None,
    ) -> dict[tuple[str, str], dict[str, Any]]:
        indexed: dict[tuple[str, str], dict[str, Any]] = {}
        for item in entrypoints or []:
            if not isinstance(item, dict):
                continue
            method = str(item.get("method") or "").strip()
            mode = str(item.get("mode") or "").strip()
            if not method:
                continue
            indexed[(method, mode)] = dict(item)
        return indexed

    @classmethod
    def build_recovery_alignment_summary(
        cls,
        *,
        expected_entrypoints: list[Dict[str, Any]] | None,
        actual_entrypoints: list[Dict[str, Any]] | None = None,
        current_entrypoints: list[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        expected_index = cls._index_recovery_entrypoints(expected_entrypoints)
        actual_index = cls._index_recovery_entrypoints(actual_entrypoints)
        current_index = cls._index_recovery_entrypoints(current_entrypoints)
        all_keys = list(expected_index.keys())
        for key in list(actual_index.keys()) + list(current_index.keys()):
            if key not in all_keys:
                all_keys.append(key)

        entries: list[Dict[str, Any]] = []
        actual_aligned = True
        current_aligned = True
        for method, mode in all_keys:
            expected = dict(expected_index.get((method, mode)) or {})
            actual = dict(actual_index.get((method, mode)) or {})
            current = dict(current_index.get((method, mode)) or {})
            expected_available = bool(expected.get("available"))
            actual_available = bool(actual.get("available")) if actual else None
            current_available = bool(current.get("available")) if current else None
            actual_alignment = "unavailable"
            if actual:
                actual_blocked_reason = str(actual.get("blocked_reason") or "").strip()
                if actual_available == expected_available:
                    actual_alignment = "aligned"
                elif cls._is_state_gated_blocked_reason(actual_blocked_reason):
                    actual_alignment = "state_gated"
                else:
                    actual_alignment = "mismatch"
                actual_aligned = actual_aligned and actual_alignment in {"aligned", "state_gated"}
            current_alignment = "unavailable"
            if current:
                current_blocked_reason = str(current.get("blocked_reason") or "").strip()
                if current_available == expected_available:
                    current_alignment = "aligned"
                elif cls._is_state_gated_blocked_reason(current_blocked_reason):
                    current_alignment = "state_gated"
                else:
                    current_alignment = "mismatch"
                current_aligned = current_aligned and current_alignment in {"aligned", "state_gated"}
            entries.append({
                "method": method,
                "mode": mode,
                "expected_available": expected_available,
                "expected_recovery_reason": str(expected.get("recovery_reason") or "").strip(),
                "expected_blocked_reason": str(expected.get("blocked_reason") or "").strip(),
                "actual_available": actual_available,
                "actual_recovery_reason": str(actual.get("recovery_reason") or "").strip(),
                "actual_blocked_reason": str(actual.get("blocked_reason") or "").strip(),
                "actual_alignment": actual_alignment,
                "current_available": current_available,
                "current_recovery_reason": str(current.get("recovery_reason") or "").strip(),
                "current_blocked_reason": str(current.get("blocked_reason") or "").strip(),
                "current_alignment": current_alignment,
            })
        return {
            "contract_version": "phase-ii-recovery-alignment-summary-v1",
            "expected_entrypoint_count": len(expected_index),
            "actual_entrypoint_count": len(actual_index),
            "current_entrypoint_count": len(current_index),
            "actual_alignment_status": (
                "aligned" if actual_index and actual_aligned else ("mismatch" if actual_index else "unavailable")
            ),
            "current_alignment_status": (
                "aligned" if current_index and current_aligned else ("mismatch" if current_index else "unavailable")
            ),
            "entries": entries,
        }

    @classmethod
    def _is_state_gated_blocked_reason(cls, blocked_reason: str) -> bool:
        normalized_reason = str(blocked_reason or "").strip()
        return normalized_reason.startswith("run_not_") or normalized_reason in cls.STATE_GATED_BLOCKED_REASONS

    @classmethod
    def normalize_recovery_operation(cls, operation: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if not isinstance(operation, dict) or not operation:
            return {}
        normalized = {
            field_name: operation.get(field_name)
            for field_name in cls.RECOVERY_OPERATION_FIELDS
            if field_name in operation
        }
        normalized["contract_version"] = str(normalized.get("contract_version") or "").strip()
        normalized["operation_id"] = str(normalized.get("operation_id") or "").strip()
        normalized["run_id"] = str(normalized.get("run_id") or "").strip()
        normalized["entrypoint"] = str(normalized.get("entrypoint") or "").strip()
        normalized["operation_status"] = str(normalized.get("operation_status") or "").strip()
        normalized["recovery_reason"] = str(normalized.get("recovery_reason") or "").strip()
        normalized["blocked_reason"] = str(normalized.get("blocked_reason") or "").strip()
        normalized["checkpoint_id"] = str(normalized.get("checkpoint_id") or "").strip()
        normalized["resume_cursor_id"] = str(normalized.get("resume_cursor_id") or "").strip()
        normalized["continuation_ref"] = dict(normalized.get("continuation_ref") or {})
        normalized["workspace_backend"] = dict(normalized.get("workspace_backend") or {})
        normalized["persistence_posture"] = str(normalized.get("persistence_posture") or "").strip()
        normalized["worker_ownership"] = dict(normalized.get("worker_ownership") or {})
        retry = dict(normalized.get("retry") or {})
        normalized["retry"] = {
            "contract_version": str(retry.get("contract_version") or "").strip(),
            "attempt_number": int(retry.get("attempt_number") or 0),
            "max_attempts": int(retry.get("max_attempts") or 0),
            "previous_operation_id": str(retry.get("previous_operation_id") or "").strip(),
            "idempotency_key": str(retry.get("idempotency_key") or "").strip(),
            "recovery_reason": str(retry.get("recovery_reason") or "").strip(),
            "retryable": bool(retry.get("retryable")),
            "terminal": bool(retry.get("terminal")),
            "status": str(retry.get("status") or "").strip(),
        } if retry else {}
        for optional_key in ("backoff_strategy", "next_delay_seconds", "blocked_reason"):
            if optional_key in retry:
                normalized["retry"][optional_key] = retry[optional_key]
        normalized["recorded_at"] = str(normalized.get("recorded_at") or "").strip()
        return normalized

    @staticmethod
    def _count_by_field(items: list[Dict[str, Any]], field_name: str) -> Dict[str, int]:
        counter = Counter()
        for item in items:
            value = str(item.get(field_name) or "").strip()
            if value:
                counter[value] += 1
        return dict(counter)

    @staticmethod
    def _count_retry_statuses(operations: list[Dict[str, Any]]) -> Dict[str, int]:
        counter = Counter()
        for operation in operations:
            retry = dict(operation.get("retry") or {})
            retry_status = str(retry.get("status") or "").strip()
            if retry_status:
                counter[retry_status] += 1
        return dict(counter)

    @staticmethod
    def _find_latest_retry_terminal_reason(operations: list[Dict[str, Any]]) -> str:
        for operation in reversed(operations):
            retry = dict(operation.get("retry") or {})
            retry_status = str(retry.get("status") or "").strip()
            retry_terminal = bool(retry.get("terminal"))
            if retry_terminal or retry_status in {"terminal", "exhausted"}:
                return (
                    str(retry.get("recovery_reason") or "").strip()
                    or str(operation.get("recovery_reason") or "").strip()
                    or str(operation.get("blocked_reason") or "").strip()
                )
        return ""

    @staticmethod
    def _find_latest_terminal_reason(operations: list[Dict[str, Any]]) -> str:
        for operation in reversed(operations):
            retry_reason = RuntimeRecoveryContractBuilder._find_latest_retry_terminal_reason([operation])
            if retry_reason:
                return retry_reason
            operation_status = str(operation.get("operation_status") or "").strip()
            if operation_status in {"blocked", "failed"}:
                return (
                    str(operation.get("recovery_reason") or "").strip()
                    or str(operation.get("blocked_reason") or "").strip()
                )
        return ""

    @classmethod
    def build_recovery_audit_summary(
        cls,
        operations: list[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        normalized_operations = [
            cls.normalize_recovery_operation(operation)
            for operation in (operations or [])
            if isinstance(operation, dict)
        ]
        normalized_operations = [
            operation for operation in normalized_operations if operation
        ]
        latest = dict(normalized_operations[-1] if normalized_operations else {})
        latest_retry = dict(latest.get("retry") or {})
        latest_ownership = dict(latest.get("worker_ownership") or {})
        retry_status_counts = cls._count_retry_statuses(normalized_operations)
        retry_count = sum(retry_status_counts.values())
        latest_retry_terminal_reason = cls._find_latest_retry_terminal_reason(normalized_operations)
        latest_terminal_reason = cls._find_latest_terminal_reason(normalized_operations)
        return {
            "contract_version": "phase-ii-recovery-audit-summary-v1",
            "operation_count": len(normalized_operations),
            "latest_status": str(latest.get("operation_status") or "").strip(),
            "latest_entrypoint": str(latest.get("entrypoint") or "").strip(),
            "latest_reason": str(latest.get("recovery_reason") or "").strip(),
            "status_counts": cls._count_by_field(normalized_operations, "operation_status"),
            "entrypoint_counts": cls._count_by_field(normalized_operations, "entrypoint"),
            "reason_counts": cls._count_by_field(normalized_operations, "recovery_reason"),
            "retry_count": retry_count,
            "retry_status_counts": retry_status_counts,
            "latest_retry_status": str(latest_retry.get("status") or "").strip(),
            "latest_retry_terminal_reason": latest_retry_terminal_reason,
            "ownership_implemented": bool(latest_ownership.get("implemented")),
            "latest_ownership_status": str(latest_ownership.get("lease_status") or "").strip(),
            "terminal": bool(latest_terminal_reason),
            "latest_terminal_reason": latest_terminal_reason,
            "authorization_source": False,
        }

    @staticmethod
    def build_expected_recovery_entrypoints(factory_contract: Dict[str, Any] | None = None) -> list[Dict[str, Any]]:
        normalized_contract = dict(factory_contract or {})
        default_recovery_expectation = dict(normalized_contract.get("default_recovery_expectation") or {})
        cross_process_candidate = bool(default_recovery_expectation.get("cross_process_candidate"))
        cross_process_block_reason = str(default_recovery_expectation.get("cross_process_block_reason") or "").strip()
        registry_recovery_reason = "ready_via_registry" if cross_process_candidate else ""
        return [
            {
                "method": "probe_run_recovery",
                "available": True,
                "recovery_reason": "",
                "blocked_reason": "",
            },
            {
                "method": "submit_approval",
                "mode": "approved",
                "available": cross_process_candidate,
                "recovery_reason": registry_recovery_reason,
                "blocked_reason": "" if cross_process_candidate else cross_process_block_reason,
            },
            {
                "method": "resume_run",
                "mode": "default",
                "available": True,
                "recovery_reason": "",
                "blocked_reason": "",
            },
            {
                "method": "resume_run",
                "mode": "continue_loop",
                "available": cross_process_candidate,
                "recovery_reason": registry_recovery_reason,
                "blocked_reason": "" if cross_process_candidate else cross_process_block_reason,
            },
        ]

    @classmethod
    def build_run_recovery_contract(cls, probe: Dict[str, Any] | None = None) -> Dict[str, Any]:
        normalized_probe = dict(probe or {})
        tool_continuation = dict(normalized_probe.get("tool_continuation") or {})
        loop_continuation = dict(normalized_probe.get("loop_continuation") or {})
        approval_request = dict(normalized_probe.get("approval_request") or {})
        recovery_entrypoints = [
            dict(item)
            for item in (normalized_probe.get("recovery_entrypoints") or [])
            if isinstance(item, dict)
        ]
        checkpoint = dict(normalized_probe.get("checkpoint") or {})
        resume_cursor = dict(normalized_probe.get("resume_cursor") or {})
        recovery_operation_boundary = dict(normalized_probe.get("recovery_operation_boundary") or {})
        latest_recovery_operation = cls.normalize_recovery_operation(
            dict(normalized_probe.get("latest_recovery_operation") or {})
        )
        recovery_operation_history = [
            cls.normalize_recovery_operation(dict(item))
            for item in (normalized_probe.get("recovery_operations") or [])
            if isinstance(item, dict)
        ][-20:]
        recovery_operation_history = [
            item for item in recovery_operation_history if item
        ]
        workspace_backend = dict(
            checkpoint.get("workspace_backend")
            or tool_continuation.get("workspace_backend")
            or loop_continuation.get("workspace_backend")
            or {}
        )
        has_probe = bool(normalized_probe)
        recovery_capabilities = cls.build_recovery_capabilities_summary({
            str(tool_continuation.get("recovery_reason") or "").strip(),
            str(loop_continuation.get("recovery_reason") or "").strip(),
        })
        return {
            "contract_version": "phase-ii-run-recovery-v1",
            "available": has_probe,
            "run_id": str(normalized_probe.get("run_id") or "").strip(),
            "run_state": str(normalized_probe.get("run_state") or "").strip(),
            "recoverable": bool(normalized_probe.get("recoverable")) if has_probe else False,
            "approval_request": approval_request,
            "tool_continuation": tool_continuation,
            "loop_continuation": loop_continuation,
            "checkpoint": checkpoint,
            "resume_cursor": resume_cursor,
            "recovery_operation_boundary": recovery_operation_boundary,
            "latest_recovery_operation": latest_recovery_operation,
            "recovery_operation_history": recovery_operation_history,
            "recovery_operation_count": len(recovery_operation_history),
            "recovery_audit_summary": cls.build_recovery_audit_summary(recovery_operation_history),
            "recovery_capabilities": recovery_capabilities,
            "recovery_entrypoints": recovery_entrypoints,
            "workspace_backend": workspace_backend,
            "reason": (
                str(normalized_probe.get("error") or "").strip()
                if str(normalized_probe.get("error") or "").strip()
                else ("probe_unavailable" if not has_probe else "")
            ),
        }

    @staticmethod
    def build_default_runtime_recovery_contract(factory_contract: Dict[str, Any] | None = None) -> Dict[str, Any]:
        normalized_contract = dict(factory_contract or {})
        default_runtime_profile = dict(normalized_contract.get("default_runtime_profile") or {})
        default_recovery_capabilities = dict(normalized_contract.get("default_recovery_capabilities") or {})
        default_recovery_expectation = dict(normalized_contract.get("default_recovery_expectation") or {})
        workspace_backend = dict(normalized_contract.get("workspace_backend") or {})
        persistence_interface = dict(normalized_contract.get("persistence_interface") or {})
        recovery_entrypoints = RuntimeRecoveryContractBuilder.build_expected_recovery_entrypoints(normalized_contract)
        return {
            "contract_version": "phase-ii-default-runtime-recovery-v1",
            "recovery_mode": str(default_recovery_capabilities.get("recovery_mode") or "").strip(),
            "recovery_posture": str(default_runtime_profile.get("recovery_posture") or "").strip(),
            "persistence_posture": str(persistence_interface.get("persistence_posture") or default_runtime_profile.get("persistence_posture") or "").strip(),
            "requires_durable_workspace": bool(default_recovery_capabilities.get("requires_durable_workspace")),
            "requires_registry_bindings": bool(default_recovery_capabilities.get("requires_registry_bindings")),
            "expected_cross_process_candidate": bool(default_recovery_expectation.get("cross_process_candidate")),
            "cross_process_block_reason": str(default_recovery_expectation.get("cross_process_block_reason") or "").strip(),
            "workspace_backend_kind": str(workspace_backend.get("backend_kind") or "").strip(),
            "workspace_backend_mode": str(workspace_backend.get("backend_mode") or "").strip(),
            "persistence_interface": persistence_interface,
            "recovery_entrypoints": recovery_entrypoints,
        }

    @classmethod
    def build_bootstrap_validation_contract(
        cls,
        *,
        expected: Dict[str, Any],
        requested_mode: str,
        probe: Dict[str, Any],
    ) -> Dict[str, Any]:
        workspace_backend = dict(
            (probe.get("tool_continuation") or {}).get("workspace_backend")
            or (probe.get("loop_continuation") or {}).get("workspace_backend")
            or {}
        )
        persistence_interface = dict(probe.get("persistence_interface") or {})
        expected_recoverable = bool(expected.get("cross_process_candidate"))
        actual_recoverable = bool(probe.get("recoverable"))
        validation_ok = expected_recoverable == actual_recoverable
        recovery_capabilities = cls.build_recovery_capabilities_summary({
            str((probe.get("tool_continuation") or {}).get("recovery_reason") or "").strip(),
            str((probe.get("loop_continuation") or {}).get("recovery_reason") or "").strip(),
        })
        recovery_entrypoints = [
            dict(item)
            for item in (probe.get("recovery_entrypoints") or [])
            if isinstance(item, dict)
        ]
        return {
            "contract_version": "phase-ii-embedded-runtime-bootstrap-validation-v1",
            "expected_recoverable": expected_recoverable,
            "actual_recoverable": actual_recoverable,
            "expected_cross_process_block_reason": str(expected.get("cross_process_block_reason") or "").strip(),
            "tool_recovery_reason": str((probe.get("tool_continuation") or {}).get("recovery_reason") or "").strip(),
            "loop_recovery_reason": str((probe.get("loop_continuation") or {}).get("recovery_reason") or "").strip(),
            "recovery_capabilities": recovery_capabilities,
            "recovery_entrypoints": recovery_entrypoints,
            "workspace_backend_kind": str(workspace_backend.get("backend_kind") or "").strip(),
            "workspace_backend_mode": str(workspace_backend.get("backend_mode") or requested_mode).strip(),
            "persistence_posture": str(persistence_interface.get("persistence_posture") or "").strip(),
            "persistence_interface": persistence_interface,
            "validation_status": "passed" if validation_ok else "failed",
            "failure_reason": "" if validation_ok else "bootstrap_recovery_validation_mismatch",
        }


class EmbeddedRuntimeContractBundleBuilder:
    """Assemble embedded runtime factory/bootstrap/default-recovery contract views."""

    @staticmethod
    def build_profile_bundle(factory_contract: Dict[str, Any]) -> Dict[str, Any]:
        normalized_factory_contract = dict(factory_contract or {})
        return {
            "embedded_runtime_factory": normalized_factory_contract,
            "embedded_runtime_bootstrap": dict(normalized_factory_contract),
            "default_runtime_recovery": RuntimeRecoveryContractBuilder.build_default_runtime_recovery_contract(
                normalized_factory_contract
            ),
        }

    @staticmethod
    def build_bootstrap_contract(
        factory_contract: Dict[str, Any],
        *,
        bootstrap_recovery_validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        contract = dict(factory_contract or {})
        contract["bootstrap_recovery_validation"] = dict(bootstrap_recovery_validation or {})
        contract["recovery_alignment_summary"] = RuntimeRecoveryContractBuilder.build_recovery_alignment_summary(
            expected_entrypoints=RuntimeRecoveryContractBuilder.build_expected_recovery_entrypoints(contract),
            actual_entrypoints=list((bootstrap_recovery_validation or {}).get("recovery_entrypoints") or []),
        )
        return contract

    @staticmethod
    def build_post_update_verification(
        *,
        previous_contract: Dict[str, Any],
        current_contract: Dict[str, Any],
        requested_workspace_mode: str,
    ) -> Dict[str, Any]:
        previous_profile = dict(previous_contract.get("default_runtime_profile") or {})
        current_profile = dict(current_contract.get("default_runtime_profile") or {})
        previous_workspace_backend = dict(previous_contract.get("workspace_backend") or {})
        workspace_backend = dict(current_contract.get("workspace_backend") or {})
        previous_recovery_expectation = dict(previous_contract.get("default_recovery_expectation") or {})
        current_recovery_expectation = dict(current_contract.get("default_recovery_expectation") or {})
        return {
            "effective_change": previous_profile != current_profile,
            "previous_runtime_mode": str(previous_profile.get("default_runtime_mode") or "").strip(),
            "current_runtime_mode": str(current_profile.get("default_runtime_mode") or "").strip(),
            "previous_recovery_posture": str(previous_profile.get("recovery_posture") or "").strip(),
            "current_recovery_posture": str(current_profile.get("recovery_posture") or "").strip(),
            "current_workspace_backend_kind": str(workspace_backend.get("backend_kind") or "").strip(),
            "current_workspace_backend_mode": str(workspace_backend.get("backend_mode") or "").strip(),
            "runtime_mode_changed": (
                str(previous_profile.get("default_runtime_mode") or "").strip()
                != str(current_profile.get("default_runtime_mode") or "").strip()
            ),
            "recovery_posture_changed": (
                str(previous_profile.get("recovery_posture") or "").strip()
                != str(current_profile.get("recovery_posture") or "").strip()
            ),
            "workspace_backend_changed": (
                str(previous_workspace_backend.get("backend_kind") or "").strip()
                != str(workspace_backend.get("backend_kind") or "").strip()
                or str(previous_workspace_backend.get("backend_mode") or "").strip()
                != str(workspace_backend.get("backend_mode") or "").strip()
            ),
            "durable_capability_changed": (
                bool(previous_workspace_backend.get("durable")) != bool(workspace_backend.get("durable"))
            ),
            "previous_cross_process_candidate": bool(previous_recovery_expectation.get("cross_process_candidate")),
            "current_cross_process_candidate": bool(current_recovery_expectation.get("cross_process_candidate")),
            "cross_process_candidate_changed": (
                bool(previous_recovery_expectation.get("cross_process_candidate"))
                != bool(current_recovery_expectation.get("cross_process_candidate"))
            ),
            "previous_cross_process_block_reason": str(previous_recovery_expectation.get("cross_process_block_reason") or "").strip(),
            "current_cross_process_block_reason": str(current_recovery_expectation.get("cross_process_block_reason") or "").strip(),
            "previous_default_recovery_expectation": previous_recovery_expectation,
            "current_default_recovery_expectation": current_recovery_expectation,
            "applied_workspace_store_mode": str(current_profile.get("embedded_workspace_store_mode") or "").strip(),
            "workspace_mode_applied": (
                not requested_workspace_mode
                or (
                    str(current_profile.get("embedded_workspace_store_mode") or "").strip() == requested_workspace_mode
                    and str(workspace_backend.get("backend_mode") or "").strip() == requested_workspace_mode
                )
            ),
            "recovery_contract_aligned": (
                bool(current_recovery_expectation.get("cross_process_candidate"))
                == (bool(workspace_backend.get("durable")) and not bool(workspace_backend.get("fallback_active")))
            ),
        }


class ProviderCatalogBuilder:
    """Assemble model/provider catalog state for the runtime profile."""

    @staticmethod
    def _resolve_enabled_provider_ids(provider_ids: list[str], effective_config: Dict[str, Any]) -> set[str]:
        configured = [
            str(item or "").strip()
            for item in (effective_config.get("enabled_providers") or [])
            if str(item or "").strip()
        ]
        if not configured:
            return set(provider_ids)
        return {provider_id for provider_id in configured if provider_id in provider_ids}

    @staticmethod
    def _resolve_override_provider_ids(override_config: Dict[str, Any]) -> set[str]:
        return {
            str(item or "").strip()
            for item in (override_config.get("enabled_providers") or [])
            if str(item or "").strip()
        }

    @classmethod
    def build_catalog(
        cls,
        *,
        all_models: list[Dict[str, Any]],
        effective_config: Dict[str, Any],
        config_layers: Dict[str, Any],
        override_config: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        provider_ids = sorted({str(item.get("provider") or "unknown") for item in all_models})
        enabled_provider_ids = cls._resolve_enabled_provider_ids(provider_ids, effective_config)
        override_provider_ids = cls._resolve_override_provider_ids(dict(override_config or {}))
        providers: Dict[str, Dict[str, Any]] = {}

        for item in all_models:
            provider_id = str(item.get("provider") or "unknown")
            provider_entry = providers.setdefault(
                provider_id,
                {
                    "provider_id": provider_id,
                    "display_name": item.get("provider_label") or provider_id,
                    "type": item.get("type") or "unknown",
                    "base_url": item.get("base_url"),
                    "configured": False,
                    "models": [],
                    "enabled": provider_id in enabled_provider_ids,
                    "enabled_source": "override" if provider_id in override_provider_ids else "default",
                    "model_sources": [],
                    "actual_models": [],
                },
            )
            provider_entry["configured"] = provider_entry["configured"] or bool(item.get("configured", False))
            provider_entry["models"].append(item["name"])
            provider_entry.setdefault("available_model_count", 0)
            provider_entry.setdefault("configured_model_count", 0)
            provider_entry.setdefault("total_model_count", 0)
            source_name = str(item.get("source") or "unknown")
            if source_name and source_name not in provider_entry["model_sources"]:
                provider_entry["model_sources"].append(source_name)
            actual_model = str(item.get("actual_model") or "").strip()
            if actual_model and actual_model not in provider_entry["actual_models"]:
                provider_entry["actual_models"].append(actual_model)
            if item.get("available"):
                provider_entry["available_model_count"] += 1
            if item.get("configured"):
                provider_entry["configured_model_count"] += 1
            provider_entry["total_model_count"] += 1

        resolved_config_layers = dict(config_layers or {})
        resolved_config_layers["provider_resolution"] = {
            "available_provider_ids": provider_ids,
            "enabled_provider_ids": sorted(enabled_provider_ids),
            "disabled_provider_ids": sorted(set(provider_ids) - set(enabled_provider_ids)),
            "default_behavior": "all_enabled" if not override_provider_ids else "override_selected",
        }
        return {
            "models": [
                item
                for item in all_models
                if str(item.get("provider") or "unknown") in enabled_provider_ids
            ],
            "providers": list(providers.values()),
            "config_layers": resolved_config_layers,
        }


class RuntimeSurfaceProfileAssembler:
    """Assemble the top-level runtime profile contract for RuntimeSurfaceService."""

    @classmethod
    def assemble(
        cls,
        service: Any,
        *,
        db: Any = None,
        conversation_id: int | None = None,
        plan_id: int | None = None,
        item_id: int | None = None,
        query_id: str | None = None,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        child_run_id: str | None = None,
        scheduler_run_id: str | None = None,
        auth_mode_default: str = "",
        default_model_default: str = "",
    ) -> Dict[str, Any]:
        effective_config = service.config_service.get_effective_config()
        all_models = service._list_all_models()
        provider_catalog = ProviderCatalogBuilder.build_catalog(
            all_models=all_models,
            effective_config=effective_config,
            config_layers=service.config_service.get_config_layers(),
            override_config=service.config_service.load_overrides(),
        )
        models = provider_catalog["models"]
        providers = provider_catalog["providers"]
        config_layers = provider_catalog["config_layers"]

        main_chat_trace_overview = service._build_main_chat_trace_overview_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        runtime_scope = service._build_runtime_scope_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            run_id=run_id,
            parent_run_id=parent_run_id,
            child_run_id=child_run_id,
            scheduler_run_id=scheduler_run_id,
        )
        main_chat_query_detail = service._build_main_chat_query_detail_contract(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
            query_id=query_id,
        )
        channel_promotion_gate = service.get_channel_promotion_gate(
            db=db,
            conversation_id=conversation_id,
            plan_id=plan_id,
            item_id=item_id,
        )
        recovery_target_run_id = (
            str(parent_run_id or "").strip()
            or str(runtime_scope.get("scheduler_run_id") or "").strip()
            or str(runtime_scope.get("run_id") or "").strip()
        )
        run_recovery = service.get_run_recovery(run_id=recovery_target_run_id) if recovery_target_run_id else service._build_run_recovery_contract()
        command_contract = service.command_registry_service.build_runtime_contract()
        child_executor_preflight = service._build_child_executor_preflight_contract(command_contract)
        child_executor_promotion_gate = service._build_child_executor_promotion_gate_contract(command_contract, child_executor_preflight)
        child_executor_dispatch_contract = service._build_child_executor_dispatch_contract(command_contract, child_executor_promotion_gate)
        embedded_runtime_factory = service.runtime_factory.build_runtime_contract()
        embedded_runtime_bundle = EmbeddedRuntimeContractBundleBuilder.build_profile_bundle(embedded_runtime_factory)

        profile = {
            "agent_mode": "general_demo",
            "auth_mode": effective_config.get("auth_mode", auth_mode_default),
            "default_model": effective_config.get("default_model", default_model_default),
            "failover_thresholds": effective_config.get("failover_thresholds") or {"medium": 0.2, "high": 0.4},
            "runtime_core": service._build_runtime_core_contract(runtime_scope=runtime_scope),
            "child_executor_preflight": child_executor_preflight,
            "child_executor_backend_registry": child_executor_preflight.get("backend_registry") or {},
            "child_executor_promotion_gate": child_executor_promotion_gate,
            "child_executor_dispatch_contract": child_executor_dispatch_contract,
            "default_runtime_recovery": embedded_runtime_bundle["default_runtime_recovery"],
            "governance_overview": service._build_governance_overview_contract(
                main_chat_trace_overview=main_chat_trace_overview,
                runtime_scope=runtime_scope,
                run_recovery=run_recovery,
                default_runtime_recovery=embedded_runtime_bundle["default_runtime_recovery"],
                child_executor_preflight=child_executor_preflight,
                child_executor_promotion_gate=child_executor_promotion_gate,
                child_executor_dispatch_contract=child_executor_dispatch_contract,
            ),
            "run_recovery": run_recovery,
            "main_chat_trace_overview": main_chat_trace_overview,
            "main_chat_query_detail": main_chat_query_detail,
            "channel_promotion_gate": channel_promotion_gate,
            "tool_runtime": service.tool_runtime_service.build_runtime_contract(),
            "mcp_runtime": service.mcp_runtime_service.build_runtime_contract(),
            "adapter_health": service.tool_runtime_service.build_adapter_health_contract(),
            "models": models,
            "providers": providers,
            "capability_contract": service.capability_profile_service.build_runtime_contract(),
            "skill_contract": service.skill_runtime_service.build_runtime_contract(),
            "memory_contract": service.agent_memory_service.build_runtime_contract(),
            "subagent_contract": service.subagent_runtime_service.build_runtime_contract(),
            "hook_contract": service.agent_hook_service.build_runtime_contract(),
            "command_contract": command_contract,
            "embedded_runtime_factory": embedded_runtime_bundle["embedded_runtime_factory"],
            "embedded_runtime_bootstrap": embedded_runtime_bundle["embedded_runtime_bootstrap"],
            "embedded_runtime_boundaries": service._build_embedded_runtime_boundaries_contract(command_contract),
            "runtime_contract_gate": service.contract_gate_service.build_runtime_contract(),
            "self_improvement_ledger": service.self_improvement_ledger_service.build_runtime_contract(db=db),
            "query_control_plane": service.query_control_plane_service.build_runtime_contract(),
            "config_layers": config_layers,
            "auth_mode_contract": {
                "current_mode": effective_config.get("auth_mode", auth_mode_default),
                "demo_guest_description": "免登录直达，适合通用框架演示、能力盘点与本地调试。",
                "business_auth_description": "登录页作为正式入口，适合后续接入真实鉴权、组织和权限体系。",
            },
        }
        profile["contract_snapshot"] = service.contract_snapshot_service.build_snapshot(profile)
        return profile


class MainChatQueryReadModelBuilder:
    """Assemble dedicated main_chat query detail/history read models."""

    @staticmethod
    def build_detail_contract(query_id: str | None = None) -> Dict[str, Any]:
        return {
            "contract_version": "phase-g-main-chat-query-detail-v1",
            "connected": False,
            "read_model_layer": "query_detail",
            "source_channel": "main_chat",
            "identity_kind": "query_id",
            "query_id": str(query_id or "").strip(),
            "recording_state": "unavailable",
            "stage_chain": [],
            "dedupe_keys": [],
            "dedupe_key_count": 0,
            "recent_events": [],
            "recent_event_count": 0,
            "latest_snapshot_id": "",
            "latest_warning_summary": "",
            "latest_stage": "",
            "latest_summary": "",
            "stage_count": 0,
            "warning_count": 0,
            "event_count": 0,
            "reason": "",
        }

    @staticmethod
    def build_history_contract(page: int, page_size: int) -> Dict[str, Any]:
        return {
            "contract_version": "phase-h-main-chat-query-history-v1",
            "connected": False,
            "read_model_layer": "query_history",
            "source_channel": "main_chat",
            "identity_kind": "query_id",
            "pagination_mode": "page_plus_cursor",
            "recording_state": "unavailable",
            "items": [],
            "page": max(1, int(page or 1)),
            "page_size": max(1, min(int(page_size or 20), 100)),
            "total_items": 0,
            "has_more": False,
            "next_cursor": "",
            "reason": "",
        }

    @staticmethod
    def filter_main_chat_events(events: Any) -> list[dict[str, Any]]:
        main_chat_events: list[dict[str, Any]] = []
        for entry in events or []:
            payload = entry.get("payload") if isinstance(entry, dict) else {}
            if not isinstance(payload, dict):
                continue
            if str(payload.get("channel") or "").strip() != "main_chat":
                continue
            main_chat_events.append(dict(entry))
        return main_chat_events

    @staticmethod
    def summarize_query_control_channel_queries(events: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        recent_queries_map: dict[str, dict[str, Any]] = {}
        for entry in events or []:
            entry_payload = dict(entry.get("payload") or {})
            query_id = str(entry_payload.get("query_id") or "").strip()
            if not query_id:
                continue
            stage = str(entry_payload.get("stage") or "").strip()
            severity = str(entry.get("severity") or "info").strip().lower()
            query_entry = recent_queries_map.setdefault(query_id, {
                "query_id": query_id,
                "latest_stage": "",
                "latest_summary": "",
                "latest_timestamp": "",
                "latest_snapshot_id": "",
                "stage_counts": {},
                "last_success_stage": "",
                "last_warning_stage": "",
                "recording_state": "recorded",
            })
            query_stage_counter = Counter(query_entry.get("stage_counts") or {})
            if stage:
                query_stage_counter[stage] += 1
                if severity == "warning":
                    query_entry["last_warning_stage"] = stage
                else:
                    query_entry["last_success_stage"] = stage
                query_entry["latest_stage"] = stage
            query_entry["latest_summary"] = str(entry.get("summary") or "").strip()
            query_entry["latest_timestamp"] = str(entry.get("timestamp") or "").strip()
            query_entry["latest_snapshot_id"] = str(((entry_payload.get("snapshot_ref") or {}).get("snapshot_id")) or "").strip()
            query_entry["stage_counts"] = dict(query_stage_counter)
        return sorted(
            recent_queries_map.values(),
            key=lambda item: str(item.get("latest_timestamp") or ""),
            reverse=True,
        )

    @classmethod
    def build_detail_from_events(
        cls,
        *,
        query_id: str | None,
        events: list[dict[str, Any]] | None,
    ) -> Dict[str, Any]:
        detail = cls.build_detail_contract(query_id)
        normalized_query_id = str(query_id or "").strip()
        if not normalized_query_id:
            detail["reason"] = "query_id_missing"
            return detail

        detail["connected"] = True
        detail["query_id"] = normalized_query_id
        query_events = []
        for entry in cls.filter_main_chat_events(events):
            payload = dict(entry.get("payload") or {})
            if str(payload.get("query_id") or "").strip() != normalized_query_id:
                continue
            query_events.append(dict(entry))

        detail["event_count"] = len(query_events)
        if not query_events:
            detail["recording_state"] = "no_records"
            detail["reason"] = "query_id_not_found"
            return detail

        ordered_events = sorted(query_events, key=lambda entry: str(entry.get("timestamp") or ""))
        stage_chain: list[str] = []
        dedupe_keys: list[str] = []
        recent_events: list[dict[str, Any]] = []
        latest_snapshot_id = ""
        latest_warning_summary = ""
        latest_stage = ""
        latest_summary = ""
        warning_count = 0
        for entry in ordered_events:
            payload = dict(entry.get("payload") or {})
            stage = str(payload.get("stage") or "").strip()
            if stage and (not stage_chain or stage_chain[-1] != stage):
                stage_chain.append(stage)
                latest_stage = stage
            if str(entry.get("summary") or "").strip():
                latest_summary = str(entry.get("summary") or "").strip()
            dedupe_key = str(payload.get("dedupe_key") or "").strip()
            if dedupe_key and dedupe_key not in dedupe_keys:
                dedupe_keys.append(dedupe_key)
            snapshot_id = str(((payload.get("snapshot_ref") or {}).get("snapshot_id")) or "").strip()
            if snapshot_id:
                latest_snapshot_id = snapshot_id
            if str(entry.get("severity") or "info").strip().lower() == "warning":
                latest_warning_summary = str(entry.get("summary") or "").strip()
                warning_count += 1
            recent_events.append({
                "timestamp": str(entry.get("timestamp") or "").strip(),
                "stage": stage,
                "summary": str(entry.get("summary") or "").strip(),
                "severity": str(entry.get("severity") or "info").strip() or "info",
                "snapshot_id": snapshot_id,
                "dedupe_key": dedupe_key,
            })

        detail["recording_state"] = "recorded"
        detail["stage_chain"] = stage_chain
        detail["dedupe_keys"] = dedupe_keys
        detail["dedupe_key_count"] = len(dedupe_keys)
        detail["recent_events"] = recent_events[-5:]
        detail["recent_event_count"] = len(detail["recent_events"])
        detail["latest_snapshot_id"] = latest_snapshot_id
        detail["latest_warning_summary"] = latest_warning_summary
        detail["latest_stage"] = latest_stage
        detail["latest_summary"] = latest_summary
        detail["stage_count"] = len(stage_chain)
        detail["warning_count"] = warning_count
        return detail

    @classmethod
    def build_history_from_events(
        cls,
        *,
        events: list[dict[str, Any]] | None,
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        history = cls.build_history_contract(page, page_size)
        main_chat_events = cls.filter_main_chat_events(events)
        history["connected"] = True
        if not main_chat_events:
            history["recording_state"] = "no_records"
            history["reason"] = "no_main_chat_query_control_trace"
            return history

        summaries = cls.summarize_query_control_channel_queries(main_chat_events)
        total_items = len(summaries)
        page_value = history["page"]
        page_size_value = history["page_size"]
        start = (page_value - 1) * page_size_value
        end = start + page_size_value
        items = summaries[start:end]

        history["recording_state"] = "recorded"
        history["items"] = items
        history["total_items"] = total_items
        history["has_more"] = end < total_items
        if history["has_more"] and items:
            last_item = items[-1]
            history["next_cursor"] = f"{last_item.get('latest_timestamp', '')}|{last_item.get('query_id', '')}"
        return history


class MainChatGovernanceOverviewBuilder:
    """Assemble main_chat trace overview and governance projection contracts."""

    @staticmethod
    def build_trace_overview_contract() -> Dict[str, Any]:
        return {
            "contract_version": "phase-g-main-chat-trace-overview-v1",
            "connected": False,
            "has_runtime_target": False,
            "trace_event_count": 0,
            "stage_counts": {},
            "last_success_stage": "",
            "last_warning_stage": "",
            "recent_queries": [],
            "latest_stage": "",
            "latest_query_id": "",
            "latest_summary": "",
            "latest_detail": "",
            "latest_timestamp": "",
            "latest_snapshot_id": "",
            "latest_dedupe_key": "",
            "recording_state": "unavailable",
            "reason": "",
        }

    @staticmethod
    def build_governance_main_chat_contract(trace_overview: Dict[str, Any] | None = None) -> Dict[str, Any]:
        normalized = dict(trace_overview or {})
        return {
            "recording_state": str(normalized.get("recording_state") or "unavailable").strip() or "unavailable",
            "trace_event_count": int(normalized.get("trace_event_count") or 0),
            "latest_stage": str(normalized.get("latest_stage") or "").strip(),
            "stage_counts": dict(normalized.get("stage_counts") or {}),
            "last_success_stage": str(normalized.get("last_success_stage") or "").strip(),
            "last_warning_stage": str(normalized.get("last_warning_stage") or "").strip(),
            "recent_queries": list(normalized.get("recent_queries") or []),
            "latest_query_id": str(normalized.get("latest_query_id") or "").strip(),
            "latest_summary": str(normalized.get("latest_summary") or "").strip(),
            "latest_timestamp": str(normalized.get("latest_timestamp") or "").strip(),
            "latest_snapshot_id": str(normalized.get("latest_snapshot_id") or "").strip(),
            "reason": str(normalized.get("reason") or "").strip(),
        }

    @classmethod
    def build_trace_overview_from_events(
        cls,
        *,
        events: list[dict[str, Any]] | None,
    ) -> Dict[str, Any]:
        overview = cls.build_trace_overview_contract()
        main_chat_events = MainChatQueryReadModelBuilder.filter_main_chat_events(events)
        overview["connected"] = True
        overview["has_runtime_target"] = True
        overview["trace_event_count"] = len(main_chat_events)
        if not main_chat_events:
            overview["recording_state"] = "no_records"
            overview["reason"] = "no_main_chat_query_control_trace"
            return overview

        stage_counter = Counter()
        last_success_stage = ""
        last_warning_stage = ""
        for entry in main_chat_events:
            entry_payload = dict(entry.get("payload") or {})
            stage = str(entry_payload.get("stage") or "").strip()
            severity = str(entry.get("severity") or "info").strip().lower()
            if stage:
                stage_counter[stage] += 1
                if severity == "warning":
                    last_warning_stage = stage
                else:
                    last_success_stage = stage

        latest = main_chat_events[-1]
        payload = dict(latest.get("payload") or {})
        overview["recording_state"] = "recorded"
        overview["stage_counts"] = dict(stage_counter)
        overview["last_success_stage"] = last_success_stage
        overview["last_warning_stage"] = last_warning_stage
        overview["recent_queries"] = MainChatQueryReadModelBuilder.summarize_query_control_channel_queries(main_chat_events)[:5]
        overview["latest_stage"] = str(payload.get("stage") or "").strip()
        overview["latest_query_id"] = str(payload.get("query_id") or "").strip()
        overview["latest_summary"] = str(latest.get("summary") or "").strip()
        overview["latest_detail"] = str(latest.get("detail") or "").strip()
        overview["latest_timestamp"] = str(latest.get("timestamp") or "").strip()
        overview["latest_snapshot_id"] = str(((payload.get("snapshot_ref") or {}).get("snapshot_id")) or "").strip()
        overview["latest_dedupe_key"] = str(payload.get("dedupe_key") or "").strip()
        return overview


class SubagentLaneRecentSummaryBuilder:
    """Assemble subagent_lane recent summary read model contracts."""

    @staticmethod
    def build_summary_contract() -> Dict[str, Any]:
        return {
            "contract_version": "phase-h-subagent-lane-recent-summary-v1",
            "connected": False,
            "recording_state": "unavailable",
            "items": [],
            "latest_query_id": "",
            "latest_stage": "",
            "latest_summary": "",
            "latest_timestamp": "",
            "total_items": 0,
            "reason": "",
        }

    @staticmethod
    def filter_subagent_lane_events(events: Any) -> list[dict[str, Any]]:
        subagent_events: list[dict[str, Any]] = []
        for entry in events or []:
            payload = entry.get("payload") if isinstance(entry, dict) else {}
            if not isinstance(payload, dict):
                continue
            if str(payload.get("channel") or "").strip() != "subagent_lane":
                continue
            subagent_events.append(dict(entry))
        return subagent_events

    @classmethod
    def build_summary_from_events(
        cls,
        *,
        events: list[dict[str, Any]] | None,
    ) -> Dict[str, Any]:
        summary = cls.build_summary_contract()
        subagent_events = cls.filter_subagent_lane_events(events)
        summary["connected"] = True
        if not subagent_events:
            summary["recording_state"] = "no_records"
            summary["reason"] = "no_subagent_lane_query_control_trace"
            return summary

        items = MainChatQueryReadModelBuilder.summarize_query_control_channel_queries(subagent_events)
        latest = dict(items[0] if items else {})
        summary["recording_state"] = "recorded"
        summary["items"] = items[:5]
        summary["total_items"] = len(items)
        summary["latest_query_id"] = str(latest.get("query_id") or "").strip()
        summary["latest_stage"] = str(latest.get("latest_stage") or "").strip()
        summary["latest_summary"] = str(latest.get("latest_summary") or "").strip()
        summary["latest_timestamp"] = str(latest.get("latest_timestamp") or "").strip()
        return summary


class SubagentLaneQueryDetailReadinessBuilder:
    """Assess whether subagent_lane can safely advance to query detail."""

    @staticmethod
    def build_readiness_contract() -> Dict[str, Any]:
        return {
            "contract_version": "phase-h-subagent-lane-query-detail-readiness-v1",
            "channel": "subagent_lane",
            "readiness_status": "blocked",
            "recent_summary_status": "unavailable",
            "ready_for_detail": False,
            "required_capabilities": {
                "stable_query_id": False,
                "stage_chain_candidate": False,
                "recent_summary_recorded": False,
                "separates_child_run_events": False,
            },
            "blocking_reasons": ["recent_summary_not_recorded"],
            "recommended_next_change": "",
        }

    @classmethod
    def build_readiness_from_summary(cls, summary: Dict[str, Any] | None) -> Dict[str, Any]:
        readiness = cls.build_readiness_contract()
        normalized_summary = dict(summary or {})
        items = [
            dict(item)
            for item in normalized_summary.get("items") or []
            if isinstance(item, dict)
        ]
        recent_summary_status = str(normalized_summary.get("recording_state") or "unavailable").strip() or "unavailable"
        query_ids = [
            str(item.get("query_id") or "").strip()
            for item in items
            if str(item.get("query_id") or "").strip()
        ]
        stages = [
            str(item.get("latest_stage") or "").strip()
            for item in items
            if str(item.get("latest_stage") or "").strip()
        ]
        stable_query_id = bool(query_ids)
        stage_chain_candidate = bool(stages)
        recent_summary_recorded = recent_summary_status == "recorded"
        separates_child_run_events = any(
            any(marker in query_id for marker in ("child", "run"))
            for query_id in query_ids
        )

        capabilities = {
            "stable_query_id": stable_query_id,
            "stage_chain_candidate": stage_chain_candidate,
            "recent_summary_recorded": recent_summary_recorded,
            "separates_child_run_events": separates_child_run_events,
        }
        blocking_reasons = [
            reason
            for key, reason in (
                ("recent_summary_recorded", "recent_summary_not_recorded"),
                ("stable_query_id", "stable_query_id_missing"),
                ("stage_chain_candidate", "stage_chain_candidate_missing"),
                ("separates_child_run_events", "child_run_identity_not_separated"),
            )
            if not capabilities[key]
        ]

        readiness["recent_summary_status"] = recent_summary_status
        readiness["required_capabilities"] = capabilities
        readiness["blocking_reasons"] = blocking_reasons
        readiness["ready_for_detail"] = not blocking_reasons
        readiness["readiness_status"] = "ready" if readiness["ready_for_detail"] else "blocked"
        readiness["recommended_next_change"] = (
            "subagent-lane-query-detail-contract"
            if readiness["ready_for_detail"]
            else ""
        )
        return readiness


class ChannelPromotionGateBuilder:
    """Assemble a canonical promotion gate contract across runtime channels."""

    LAYER_ORDER = [
        "readiness",
        "recent_summary",
        "query_detail",
        "query_history",
        "query_workspace",
    ]

    @classmethod
    def build_contract(
        cls,
        *,
        subagent_lane_readiness: Dict[str, Any] | None = None,
        external_adapter_readiness: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        subagent = cls._build_subagent_lane_channel(subagent_lane_readiness)
        external = cls._build_external_adapter_channel(external_adapter_readiness)
        main_chat = cls._build_main_chat_channel()
        channels = [main_chat, subagent, external]
        channels_by_id = {channel["channel"]: channel for channel in channels}
        blocked_channels = [
            channel["channel"]
            for channel in channels
            if channel.get("promotion_status") != "baseline"
            and channel.get("blocked_layers")
        ]
        return {
            "contract_version": "phase-h-channel-promotion-gate-v1",
            "overall_status": "guarded" if blocked_channels else "ready",
            "layer_order": list(cls.LAYER_ORDER),
            "channels": channels,
            "channels_by_id": channels_by_id,
            "over_promotion_guard": {
                "blocked_channels": blocked_channels,
                "blocked_layers": {
                    "query_detail": ["external_adapter"],
                    "query_history": ["subagent_lane", "external_adapter"],
                    "query_workspace": ["subagent_lane", "external_adapter"],
                },
                "reason": "promotion_must_follow_readiness_then_summary_then_detail_then_history_then_workspace",
            },
        }

    @staticmethod
    def _build_main_chat_channel() -> Dict[str, Any]:
        return {
            "channel": "main_chat",
            "baseline": True,
            "readiness_status": "ready",
            "current_layer": "query_workspace",
            "promotion_status": "baseline",
            "allowed_layers": [],
            "blocked_layers": [],
            "blocking_reasons": [],
            "evidence": {
                "canonical_baseline": True,
                "runtime_surface_primary": True,
            },
        }

    @staticmethod
    def _build_subagent_lane_channel(readiness: Dict[str, Any] | None) -> Dict[str, Any]:
        normalized = dict(readiness or {})
        ready_for_detail = bool(normalized.get("ready_for_detail"))
        blocking_reasons = [
            str(reason or "").strip()
            for reason in (normalized.get("blocking_reasons") or [])
            if str(reason or "").strip()
        ]
        return {
            "channel": "subagent_lane",
            "baseline": False,
            "readiness_status": str(normalized.get("readiness_status") or "blocked").strip() or "blocked",
            "current_layer": "query_detail" if ready_for_detail else "recent_summary",
            "promotion_status": "query_detail_ready" if ready_for_detail else "recent_summary_candidate",
            "allowed_layers": ["query_detail"] if ready_for_detail else ["recent_summary"],
            "blocked_layers": [] if ready_for_detail else ["query_detail", "query_history", "query_workspace"],
            "blocking_reasons": blocking_reasons,
            "evidence": {
                "recent_summary_status": str(normalized.get("recent_summary_status") or "").strip(),
                "ready_for_detail": ready_for_detail,
                "required_capabilities": dict(normalized.get("required_capabilities") or {}),
                "recommended_next_change": str(normalized.get("recommended_next_change") or "").strip(),
            },
        }

    @staticmethod
    def _build_external_adapter_channel(readiness: Dict[str, Any] | None) -> Dict[str, Any]:
        normalized = dict(readiness or {})
        return {
            "channel": "external_adapter",
            "baseline": False,
            "readiness_status": str(normalized.get("readiness_status") or "candidate").strip() or "candidate",
            "current_layer": "recent_summary",
            "promotion_status": "recent_summary_candidate",
            "allowed_layers": ["recent_summary"],
            "blocked_layers": ["query_detail", "query_history", "query_workspace"],
            "blocking_reasons": [
                str(reason or "").strip()
                for reason in (normalized.get("blocking_reasons") or ["detail_not_generalized"])
                if str(reason or "").strip()
            ],
            "evidence": {
                "recent_summary_status": str(normalized.get("recent_summary_status") or "unavailable").strip() or "unavailable",
                "ready_for_detail": bool(normalized.get("ready_for_detail")),
            },
        }


class SubagentLaneQueryDetailBuilder:
    """Assemble dedicated subagent_lane query detail read models."""

    @staticmethod
    def build_detail_contract(query_id: str | None = None) -> Dict[str, Any]:
        return {
            "contract_version": "phase-h-subagent-lane-query-detail-v1",
            "channel": "subagent_lane",
            "connected": False,
            "query_id": str(query_id or "").strip(),
            "recording_state": "unavailable",
            "stage_chain": [],
            "dedupe_keys": [],
            "dedupe_key_count": 0,
            "recent_events": [],
            "recent_event_count": 0,
            "latest_snapshot_id": "",
            "latest_warning_summary": "",
            "latest_stage": "",
            "latest_summary": "",
            "stage_count": 0,
            "warning_count": 0,
            "event_count": 0,
            "reason": "",
        }

    @classmethod
    def build_detail_from_events(
        cls,
        *,
        query_id: str | None,
        events: list[dict[str, Any]] | None,
    ) -> Dict[str, Any]:
        detail = cls.build_detail_contract(query_id)
        normalized_query_id = str(query_id or "").strip()
        if not normalized_query_id:
            detail["reason"] = "query_id_missing"
            return detail

        detail["connected"] = True
        subagent_events = []
        for entry in SubagentLaneRecentSummaryBuilder.filter_subagent_lane_events(events):
            payload = dict(entry.get("payload") or {})
            if str(payload.get("query_id") or "").strip() != normalized_query_id:
                continue
            subagent_events.append(dict(entry))

        detail["event_count"] = len(subagent_events)
        if not subagent_events:
            detail["recording_state"] = "no_records"
            detail["reason"] = "query_id_not_found"
            return detail

        ordered_events = sorted(subagent_events, key=lambda entry: str(entry.get("timestamp") or ""))
        stage_chain: list[str] = []
        dedupe_keys: list[str] = []
        recent_events: list[dict[str, Any]] = []
        latest_snapshot_id = ""
        latest_warning_summary = ""
        latest_stage = ""
        latest_summary = ""
        warning_count = 0
        for entry in ordered_events:
            payload = dict(entry.get("payload") or {})
            stage = str(payload.get("stage") or "").strip()
            if stage and (not stage_chain or stage_chain[-1] != stage):
                stage_chain.append(stage)
                latest_stage = stage
            summary = str(entry.get("summary") or "").strip()
            if summary:
                latest_summary = summary
            dedupe_key = str(payload.get("dedupe_key") or "").strip()
            if dedupe_key and dedupe_key not in dedupe_keys:
                dedupe_keys.append(dedupe_key)
            snapshot_id = str(((payload.get("snapshot_ref") or {}).get("snapshot_id")) or "").strip()
            if snapshot_id:
                latest_snapshot_id = snapshot_id
            severity = str(entry.get("severity") or "info").strip() or "info"
            if severity.lower() == "warning":
                latest_warning_summary = summary
                warning_count += 1
            recent_events.append({
                "timestamp": str(entry.get("timestamp") or "").strip(),
                "stage": stage,
                "summary": summary,
                "severity": severity,
                "snapshot_id": snapshot_id,
                "dedupe_key": dedupe_key,
            })

        detail["recording_state"] = "recorded"
        detail["stage_chain"] = stage_chain
        detail["dedupe_keys"] = dedupe_keys
        detail["dedupe_key_count"] = len(dedupe_keys)
        detail["recent_events"] = recent_events[-5:]
        detail["recent_event_count"] = len(detail["recent_events"])
        detail["latest_snapshot_id"] = latest_snapshot_id
        detail["latest_warning_summary"] = latest_warning_summary
        detail["latest_stage"] = latest_stage
        detail["latest_summary"] = latest_summary
        detail["stage_count"] = len(stage_chain)
        detail["warning_count"] = warning_count
        return detail
