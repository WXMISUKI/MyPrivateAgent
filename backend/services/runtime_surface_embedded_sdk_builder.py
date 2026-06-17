"""Embedded SDK/Harness read-model builder for Runtime Surface."""

from __future__ import annotations

from typing import Any, Dict

try:
    from services.runtime_surface_builders import (
        EmbeddedRuntimeContractBundleBuilder,
        RuntimeRecoveryContractBuilder,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.services.runtime_surface_builders import (
        EmbeddedRuntimeContractBundleBuilder,
        RuntimeRecoveryContractBuilder,
    )


class EmbeddedSdkRuntimeSurfaceBuilder:
    """Assemble Runtime Surface read models for Embedded SDK/Harness contracts."""

    @staticmethod
    def build_profile_bundle(factory_contract: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return EmbeddedRuntimeContractBundleBuilder.build_profile_bundle(dict(factory_contract or {}))

    @staticmethod
    def build_bootstrap_contract(
        factory_contract: Dict[str, Any] | None = None,
        *,
        bootstrap_recovery_validation: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return EmbeddedRuntimeContractBundleBuilder.build_bootstrap_contract(
            dict(factory_contract or {}),
            bootstrap_recovery_validation=dict(bootstrap_recovery_validation or {}),
        )

    @staticmethod
    def build_post_update_verification(
        *,
        previous_contract: Dict[str, Any],
        current_contract: Dict[str, Any],
        requested_workspace_mode: str,
    ) -> Dict[str, Any]:
        return EmbeddedRuntimeContractBundleBuilder.build_post_update_verification(
            previous_contract=previous_contract,
            current_contract=current_contract,
            requested_workspace_mode=requested_workspace_mode,
        )

    @staticmethod
    def build_run_recovery_contract(probe: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return RuntimeRecoveryContractBuilder.build_run_recovery_contract(probe)

    @staticmethod
    def build_default_runtime_recovery_contract(
        factory_contract: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return RuntimeRecoveryContractBuilder.build_default_runtime_recovery_contract(factory_contract)

    @staticmethod
    def build_bootstrap_validation_contract(
        *,
        expected: Dict[str, Any],
        requested_mode: str,
        probe: Dict[str, Any],
    ) -> Dict[str, Any]:
        return RuntimeRecoveryContractBuilder.build_bootstrap_validation_contract(
            expected=expected,
            requested_mode=requested_mode,
            probe=probe,
        )

    @staticmethod
    def build_recovery_alignment_summary(
        *,
        expected_entrypoints: list[Dict[str, Any]] | None,
        actual_entrypoints: list[Dict[str, Any]] | None = None,
        current_entrypoints: list[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        return RuntimeRecoveryContractBuilder.build_recovery_alignment_summary(
            expected_entrypoints=expected_entrypoints,
            actual_entrypoints=actual_entrypoints,
            current_entrypoints=current_entrypoints,
        )
