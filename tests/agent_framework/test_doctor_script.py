import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

from backend.scripts import doctor


class DoctorScriptTests(unittest.TestCase):
    @patch("backend.scripts.doctor.get_startup_diagnostics_service")
    def test_default_mode_uses_startup_diagnostics(self, mock_factory):
        mock_factory.return_value.collect_report.return_value = {
            "status": "ok",
            "summary": {"ok": 1, "warn": 0, "fail": 0},
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = doctor.main([])

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "ok")

    @patch("backend.scripts.doctor.SessionLocal")
    @patch("backend.scripts.doctor.get_capability_gap_service")
    @patch("backend.scripts.doctor.get_remediation_status_service")
    def test_capability_gaps_mode_returns_gate_warning(
        self,
        mock_remediation_factory,
        mock_service_factory,
        mock_session_local,
    ):
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_remediation_factory.return_value.status_map.return_value = {}
        mock_service_factory.return_value.get_summary.return_value = {
            "benchmark_health": {
                "gate_passed": False,
                "score": 72.0,
                "threshold_score": 80.0,
                "benchmark_catalog_coverage_ratio": 0.5,
                "benchmark_catalog_coverage_threshold": 0.6,
                "missing_profiles": ["planning"],
                "benchmark_catalog_unmatched": [
                    {
                        "id": "planning_finalize",
                        "reason": "缺少事件: completion_finalized",
                        "remediation_action_id": "fix_final_synthesis_chain",
                    }
                ],
                "action_playbook": {
                    "fix_final_synthesis_chain": {"title": "修复最终收尾链路"}
                },
            },
            "remediation_progress": {"long_blocked_count": 0},
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = doctor.main(["--capability-gaps", "--window-days", "14", "--limit", "50"])

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "warn")
        self.assertFalse(payload["gate_passed"])
        self.assertTrue(payload["escalation_recommendations"])
        self.assertEqual(payload["window_days"], 14)
        self.assertEqual(payload["limit"], 50)
        self.assertEqual(payload["pending_actions"][0]["action_id"], "fix_final_synthesis_chain")
        self.assertEqual(payload["pending_actions"][0]["owner"], "agent-core")
        self.assertIn("backend/harness/agent_harness.py", payload["pending_actions"][0]["files"])
        self.assertEqual(payload["remediation_targets"][0]["module"], "completion_synthesis")
        mock_service_factory.return_value.get_summary.assert_called_once_with(limit=50, window_days=14)
        mock_db.close.assert_called_once()

    @patch("backend.scripts.doctor.SessionLocal")
    @patch("backend.scripts.doctor.get_capability_gap_service")
    @patch("backend.scripts.doctor.get_remediation_status_service")
    def test_capability_gaps_mode_returns_zero_when_gate_passed(self, mock_remediation_factory, mock_service_factory, mock_session_local):
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_remediation_factory.return_value.status_map.return_value = {}
        mock_service_factory.return_value.get_summary.return_value = {
            "benchmark_health": {
                "gate_passed": True,
                "score": 92.0,
                "threshold_score": 80.0,
                "benchmark_catalog_coverage_ratio": 0.9,
                "benchmark_catalog_coverage_threshold": 0.6,
                "missing_profiles": [],
                "benchmark_catalog_unmatched": [],
            },
            "remediation_progress": {"long_blocked_count": 0},
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = doctor.main(["--capability-gaps"])

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["gate_passed"])
        mock_db.close.assert_called_once()

    @patch("backend.scripts.doctor.SessionLocal")
    @patch("backend.scripts.doctor.get_capability_gap_service")
    @patch("backend.scripts.doctor.get_remediation_status_service")
    def test_capability_gaps_mode_fails_when_open_action_threshold_breached(
        self,
        mock_remediation_factory,
        mock_service_factory,
        mock_session_local,
    ):
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_remediation_factory.return_value.status_map.return_value = {
            "fix_final_synthesis_chain": {"status": "open"},
            "fix_retry_convergence_chain": {"status": "blocked"},
        }
        mock_service_factory.return_value.get_summary.return_value = {
            "benchmark_health": {
                "gate_passed": True,
                "score": 92.0,
                "threshold_score": 80.0,
                "benchmark_catalog_coverage_ratio": 0.9,
                "benchmark_catalog_coverage_threshold": 0.6,
                "missing_profiles": [],
                "benchmark_catalog_unmatched": [
                    {"id": "case_1", "reason": "x", "remediation_action_id": "fix_final_synthesis_chain"},
                    {"id": "case_2", "reason": "y", "remediation_action_id": "fix_retry_convergence_chain"},
                ],
                "action_playbook": {
                    "fix_final_synthesis_chain": {"title": "修复最终收尾链路"},
                    "fix_retry_convergence_chain": {"title": "修复补查收敛链路"},
                },
            },
            "remediation_progress": {"long_blocked_count": 0},
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = doctor.main(["--capability-gaps", "--max-open-actions", "1"])

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertFalse(payload["gate_passed"])
        self.assertTrue(payload["open_action_gate_breached"])
        self.assertEqual(payload["non_closed_action_count"], 2)

    @patch("backend.scripts.doctor.SessionLocal")
    @patch("backend.scripts.doctor.get_capability_gap_service")
    @patch("backend.scripts.doctor.get_remediation_status_service")
    def test_capability_gaps_mode_fails_when_long_blocked_threshold_breached(
        self,
        mock_remediation_factory,
        mock_service_factory,
        mock_session_local,
    ):
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_remediation_factory.return_value.status_map.return_value = {}
        mock_service_factory.return_value.get_summary.return_value = {
            "benchmark_health": {
                "gate_passed": True,
                "score": 90.0,
                "threshold_score": 80.0,
                "benchmark_catalog_coverage_ratio": 0.9,
                "benchmark_catalog_coverage_threshold": 0.6,
                "missing_profiles": [],
                "benchmark_catalog_unmatched": [],
            },
            "remediation_progress": {"long_blocked_count": 2},
        }

        output = io.StringIO()
        with redirect_stdout(output):
            code = doctor.main(["--capability-gaps", "--max-long-blocked-actions", "1"])

        payload = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertFalse(payload["gate_passed"])
        self.assertEqual(payload["long_blocked_action_count"], 2)
        self.assertTrue(payload["long_blocked_action_gate_breached"])
        recommendation_types = [item.get("type") for item in payload["escalation_recommendations"]]
        self.assertIn("long_blocked_overflow", recommendation_types)


if __name__ == "__main__":
    unittest.main()
