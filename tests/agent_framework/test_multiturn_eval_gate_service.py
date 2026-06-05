import unittest
from pathlib import Path

from backend.services.multiturn_eval_gate_service import MultiTurnEvalGateService


class MultiTurnEvalGateServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = MultiTurnEvalGateService()

    def test_passing_grounding_scenario(self):
        scenario = {
            "id": "grounding_required_no_evidence",
            "turns": [{"role": "user", "content": "退款？"}],
            "evidence": {
                "grounding": {
                    "require_citations": True,
                    "evidence_available": False,
                },
                "response": {"behavior": "refuse_or_clarify"},
            },
            "assertions": {
                "grounding": {
                    "require_citations": True,
                    "evidence_available": False,
                },
                "response": {"behavior": "refuse_or_clarify"},
            },
        }

        result = self.service.evaluate_scenario(scenario)

        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["failed_count"], 0)
        self.assertTrue(all(item["passed"] for item in result["assertions"]))

    def test_failed_assertion_reports_expected_and_actual(self):
        scenario = {
            "id": "prompt_version_mismatch",
            "turns": [{"role": "user", "content": "退款？"}],
            "evidence": {"promptops": {"prompt_key": "refund_policy", "version": "1"}},
            "assertions": {"promptops": {"prompt_key": "refund_policy", "version": "2"}},
        }

        result = self.service.evaluate_scenario(scenario)

        self.assertEqual(result["status"], "failed")
        failed = [item for item in result["assertions"] if not item["passed"]]
        self.assertEqual(failed[0]["path"], "version")
        self.assertEqual(failed[0]["expected"], "2")
        self.assertEqual(failed[0]["actual"], "1")

    def test_disabled_scenario_is_skipped(self):
        result = self.service.evaluate_scenario({
            "id": "disabled",
            "enabled": False,
            "turns": [{"role": "user", "content": "hi"}],
            "evidence": {},
            "assertions": {"response": {"behavior": "ok"}},
        })

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "scenario_disabled")

    def test_missing_turns_blocks_scenario(self):
        result = self.service.evaluate_scenario({
            "id": "missing_turns",
            "evidence": {},
            "assertions": {"response": {"behavior": "ok"}},
        })

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "missing_turns")

    def test_tool_assertion_accepts_expected_subset(self):
        scenario = {
            "id": "tool_subset",
            "turns": [{"role": "user", "content": "查订单"}],
            "evidence": {"tools": {"called_tool_names": ["order.lookup", "policy.lookup"]}},
            "assertions": {"tools": {"expected_tool_names": ["order.lookup"]}},
        }

        result = self.service.evaluate_scenario(scenario)

        self.assertEqual(result["status"], "passed")

    def test_sample_scenarios_all_pass(self):
        directory = Path(__file__).resolve().parents[2] / "docs" / "evals" / "multiturn"
        report = self.service.evaluate_directory(directory)

        self.assertEqual(report["overall_status"], "passed")
        self.assertGreaterEqual(report["scenario_count"], 3)
        self.assertEqual(report["status_counts"]["failed"], 0)
        self.assertFalse(report["behavior_boundary"]["model_invocation"])
        self.assertFalse(report["behavior_boundary"]["state_mutation"])


if __name__ == "__main__":
    unittest.main()
