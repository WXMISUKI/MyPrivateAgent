import unittest

from backend.services.query_control_plane_service import QueryControlPlaneService


class QueryControlPlaneServiceTests(unittest.TestCase):
    def test_build_runtime_contract_exposes_stable_lifecycle_and_channels(self):
        contract = QueryControlPlaneService().build_runtime_contract()

        self.assertEqual(contract["contract_version"], "phase-g-query-control-plane-v1")
        self.assertEqual(contract["overall_status"], "design_ready")
        self.assertEqual(contract["lifecycle_stages"], [
            "input_received",
            "context_assembly",
            "planning",
            "model_stream",
            "tool_decision",
            "tool_execution",
            "observation",
            "review",
            "final_output",
        ])
        self.assertIn("main_chat", contract["execution_channels"])
        self.assertIn("embedded_sdk", contract["execution_channels"])
        self.assertIn("external_adapter", contract["execution_channels"])
        self.assertIn("subagent_lane", contract["execution_channels"])
        self.assertIn("context_assembly", contract["required_trace_events"])
        self.assertIn("tool_execution", contract["required_trace_events"])
        self.assertEqual(contract["adapter_boundaries"]["provider_adapter"], "normalizes model streams into runtime events")
        self.assertEqual(contract["adapter_boundaries"]["timeline"], "records lifecycle events through QueryControlTimelineService")
        self.assertEqual(
            contract["adapter_boundaries"]["tool_runtime_observation_payload"],
            "compact_status_summary",
        )
        self.assertTrue(contract["runtime_surface_enabled"])


if __name__ == "__main__":
    unittest.main()
