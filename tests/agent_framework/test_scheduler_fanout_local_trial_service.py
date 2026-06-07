import json
import unittest
from contextlib import redirect_stdout
from io import StringIO

from backend.scripts import scheduler_fanout_local_trial
from backend.services.scheduler_fanout_local_trial_service import SchedulerFanoutLocalTrialService


class SchedulerFanoutLocalTrialServiceTests(unittest.TestCase):
    def test_success_trial_returns_go(self):
        report = SchedulerFanoutLocalTrialService().run_trial(mode="success")

        self.assertEqual(report.decision, "go")
        self.assertEqual(report.reason_code, "scheduler_fanout_local_trial_ready")
        self.assertEqual(report.scheduler["merge_status"], "completed")
        self.assertEqual(report.scheduler["child_status_counts"], {"completed": 4})
        self.assertTrue(report.scheduler["scheduler_run_id"])
        self.assertIn("[backend] backend deterministic output ready", report.merge["merged_output"])
        self.assertEqual(report.boundary["real_child_executor_dispatch"], "not_performed")
        self.assertFalse(report.boundary["default_runtime_behavior_changed"])

    def test_success_trial_preserves_child_run_identity_fields(self):
        report = SchedulerFanoutLocalTrialService().run_trial(mode="success")

        self.assertGreaterEqual(len(report.children), 2)
        for child in report.children:
            self.assertTrue(child["child_run_id"])
            self.assertEqual(child["child_display_id"], child["child_run_id"])
            self.assertEqual(child["run_id"], child["child_run_id"])
            self.assertEqual(child["scheduler_run_id"], report.scheduler["scheduler_run_id"])

    def test_partial_failure_trial_returns_review(self):
        report = SchedulerFanoutLocalTrialService().run_trial(
            mode="partial_failure",
            failed_role="frontend",
        )

        self.assertEqual(report.decision, "review")
        self.assertEqual(report.reason_code, "scheduler_fanout_merge_partial_failed")
        self.assertEqual(report.scheduler["merge_status"], "partial_failed")
        self.assertEqual(report.scheduler["child_status_counts"]["failed"], 1)
        self.assertIn("frontend=frontend deterministic failure", report.merge["merged_output"])
        self.assertEqual(report.warnings[0]["status"], "review")

    def test_blocked_trial_returns_blocked_when_fanout_not_prepared(self):
        report = SchedulerFanoutLocalTrialService().run_trial(mode="blocked")

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "scheduler_fanout_not_prepared")
        self.assertEqual(report.blockers[0]["component"], "scheduler")
        self.assertEqual(report.scheduler, {})
        self.assertEqual(report.children, [])

    def test_cli_exit_codes_follow_decision(self):
        success_output = StringIO()
        with redirect_stdout(success_output):
            success_exit = scheduler_fanout_local_trial.main(["--mode", "success"])

        review_output = StringIO()
        with redirect_stdout(review_output):
            review_exit = scheduler_fanout_local_trial.main(["--mode", "partial-failure"])

        blocked_output = StringIO()
        with redirect_stdout(blocked_output):
            blocked_exit = scheduler_fanout_local_trial.main(["--mode", "blocked"])

        self.assertEqual(success_exit, 0)
        self.assertEqual(json.loads(success_output.getvalue())["decision"], "go")
        self.assertEqual(review_exit, 2)
        self.assertEqual(json.loads(review_output.getvalue())["decision"], "review")
        self.assertEqual(blocked_exit, 1)
        self.assertEqual(json.loads(blocked_output.getvalue())["decision"], "blocked")


if __name__ == "__main__":
    unittest.main()
