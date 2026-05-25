import unittest
from unittest.mock import patch

from backend.services.startup_diagnostics_service import StartupDiagnosticsService


class StartupDiagnosticsServiceTests(unittest.TestCase):
    @patch.object(StartupDiagnosticsService, "_check_environment", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_database", return_value={"status": "warn", "details": ["db slow"]})
    @patch.object(StartupDiagnosticsService, "_check_filesystem", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_ui_assets", return_value={"status": "warn", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_models", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_framework_adapters", return_value={"status": "ok", "details": []})
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
    @patch.object(StartupDiagnosticsService, "_check_framework_adapters", return_value={"status": "ok", "details": []})
    @patch.object(StartupDiagnosticsService, "_check_presets", return_value={"status": "ok", "details": []})
    def test_collect_report_marks_fail_when_any_critical_check_fails(self, *_mocks):
        report = StartupDiagnosticsService().collect_report()
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["summary"]["fail"], 1)

    @patch("backend.services.startup_diagnostics_service.get_tool_runtime_service")
    def test_check_framework_adapters_reports_not_configured_adapter_readiness(self, mock_tool_runtime_factory):
        mock_tool_runtime_factory.return_value.build_adapter_health_contract.return_value = {
            "contract_version": "phase-b-adapter-health-v1",
            "overall_status": "not_configured",
            "adapter_count": 3,
            "unavailable_count": 0,
            "not_configured_count": 1,
            "adapters": [
                {
                    "adapter_id": "langgraph_draft",
                    "framework_name": "LangGraph",
                    "status": "not_configured",
                    "configuration_status": "missing_package",
                    "execution_mode": "draft_external_runtime",
                    "missing_env": ["LANGGRAPH_RUNTIME_ENDPOINT", "LANGGRAPH_ASSISTANT_ID"],
                    "missing_packages": ["langgraph"],
                    "execution_block_reason": "missing required package: langgraph",
                }
            ],
        }

        report = StartupDiagnosticsService()._check_framework_adapters()

        self.assertEqual(report["status"], "warn")
        self.assertEqual(report["adapter_health"]["overall_status"], "not_configured")
        self.assertGreaterEqual(len(report["remediation_actions"]), 2)
        self.assertEqual(report["remediation_actions"][0]["adapter_id"], "langgraph_draft")
        self.assertEqual(report["remediation_actions"][0]["framework_name"], "LangGraph")
        joined = "\n".join(report["details"])
        self.assertIn("adapter_health=not_configured", joined)
        self.assertIn("langgraph_draft: status=not_configured", joined)
        self.assertIn("missing_packages=langgraph", joined)
        self.assertIn("missing_env=LANGGRAPH_RUNTIME_ENDPOINT,LANGGRAPH_ASSISTANT_ID", joined)


if __name__ == "__main__":
    unittest.main()
