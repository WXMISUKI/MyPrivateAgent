import unittest

from backend.agent_framework.recovery_acceptance_smoke import (
    EMBEDDED_SDK_RECOVERY_ACCEPTANCE_SMOKE_VERSION,
    run_embedded_sdk_recovery_acceptance_smoke,
    sanitize_acceptance_evidence,
)


class EmbeddedSdkRecoveryAcceptanceSmokeTests(unittest.TestCase):
    def test_accepts_durable_registry_backed_recovery(self):
        payload = run_embedded_sdk_recovery_acceptance_smoke("accepted")

        self.assertEqual(payload["contract_version"], EMBEDDED_SDK_RECOVERY_ACCEPTANCE_SMOKE_VERSION)
        self.assertEqual(payload["decision"], "accepted")
        self.assertTrue(payload["workspace_backend"]["durable"])
        self.assertFalse(payload["workspace_backend"]["fallback_active"])
        self.assertEqual(payload["tool_continuation"]["recovery_reason"], "ready_via_registry")
        self.assertEqual(payload["loop_continuation"]["recovery_reason"], "ready_via_registry")
        self.assertEqual(payload["loop_continuation_result"]["approved_state"], "observing")
        self.assertEqual(payload["loop_continuation_result"]["resumed_state"], "done")
        self.assertEqual(
            payload["operation_evidence"]["latest_recovery_operation"]["entrypoint"],
            "resume_run.continue_loop",
        )
        self.assertEqual(payload["blockers"], [])
        self.assertIn("no_background_auto_recovery", payload["non_goals"])

    def test_blocks_memory_only_workspace(self):
        payload = run_embedded_sdk_recovery_acceptance_smoke("memory-only")

        self.assertEqual(payload["decision"], "blocked")
        self.assertFalse(payload["workspace_backend"]["durable"])
        self.assertEqual(payload["tool_continuation"]["recovery_reason"], "workspace_backend_not_durable")
        self.assertIn(
            "DURABLE_WORKSPACE_REQUIRED",
            {blocker["code"] for blocker in payload["blockers"]},
        )

    def test_blocks_missing_registry_binding(self):
        payload = run_embedded_sdk_recovery_acceptance_smoke("missing-registry-binding")

        self.assertEqual(payload["decision"], "blocked")
        self.assertTrue(payload["workspace_backend"]["durable"])
        self.assertEqual(payload["continuation_registry"]["total_bindings"], 0)
        self.assertEqual(payload["tool_continuation"]["recovery_reason"], "missing_registered_binding")
        self.assertIn(
            "REGISTRY_BINDING_REQUIRED",
            {blocker["code"] for blocker in payload["blockers"]},
        )

    def test_sanitized_payload_excludes_executable_objects(self):
        def _callable():
            return "unsafe"

        class _ProviderClient:
            pass

        sanitized = sanitize_acceptance_evidence({
            "callable": _callable,
            "nested": {
                "client": _ProviderClient(),
                "safe": "kept",
            },
            "items": [_callable, {"safe": True}],
        })

        self.assertNotIn("callable", sanitized)
        self.assertNotIn("client", sanitized["nested"])
        self.assertEqual(sanitized["nested"]["safe"], "kept")
        self.assertEqual(sanitized["items"], [{"safe": True}])


if __name__ == "__main__":
    unittest.main()
