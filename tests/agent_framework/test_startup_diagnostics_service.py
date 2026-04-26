import unittest
from unittest.mock import patch

from backend.services.startup_diagnostics_service import StartupDiagnosticsService


class StartupDiagnosticsServiceTests(unittest.TestCase):
    @patch.object(StartupDiagnosticsService, "_check_environment", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_database", return_value={"status": "warn", "details": ["db slow"]})
    @patch.object(StartupDiagnosticsService, "_check_filesystem", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_ui_assets", return_value={"status": "warn", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_models", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_presets", return_value={"status": "ok", "details": []})
    def test_collect_report_builds_warn_summary(self, *_mocks):
        report = StartupDiagnosticsService().collect_report()

        self.assertEqual(report["status"], "warn")
        self.assertEqual(report["summary"]["warn"], 2)
        self.assertEqual(report["summary"]["fail"], 0)

    @patch.object(StartupDiagnosticsService, "_check_environment", return_value={"status": "fail", "details": ["missing env"]})
    @patch.object(StartupDiagnosticsService, "_check_database", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_filesystem", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_ui_assets", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_models", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_presets", return_value={"status": "ok", "details": []})
    def test_collect_report_marks_fail_when_any_critical_check_fails(self, *_mocks):
        report = StartupDiagnosticsService().collect_report()
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["fail"], 1)


if __name__ == "__main__":
    unittest.main()
