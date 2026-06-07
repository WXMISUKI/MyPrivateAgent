import json
import sys
import types
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from fastapi.testclient import TestClient

if "slowapi" not in sys.modules:
    slowapi_module = types.ModuleType("slowapi")
    slowapi_module.Limiter = lambda *args, **kwargs: object()
    slowapi_module._rate_limit_exceeded_handler = lambda *args, **kwargs: None
    sys.modules["slowapi"] = slowapi_module

    slowapi_util_module = types.ModuleType("slowapi.util")
    slowapi_util_module.get_remote_address = lambda request: "127.0.0.1"
    sys.modules["slowapi.util"] = slowapi_util_module

    slowapi_errors_module = types.ModuleType("slowapi.errors")
    slowapi_errors_module.RateLimitExceeded = type("RateLimitExceeded", (Exception,), {})
    sys.modules["slowapi.errors"] = slowapi_errors_module

from backend.agent_server.app import create_app
from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
from backend.scripts import doctor


class LocalKnowledgeRuntimeDoctorTests(unittest.TestCase):
    def test_knowledge_runtime_doctor_returns_go_report(self):
        with patch(
            "backend.scripts.doctor.run_company_profile_explicit_api_local_smoke",
            return_value=_FakeSmokeReport(_smoke_payload(decision="go")),
        ):
            report = doctor._build_knowledge_runtime_report(provider_base_url="http://knowledge.test")

        self.assertEqual(report["scope"], "knowledge_runtime")
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["decision"], "go")
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["checks"][0]["status"], "ok")
        self.assertEqual(report["checks"][0]["document_count"], 1)
        self.assertEqual(report["boundary"]["default_chat_retrieval_injection"], "disabled")
        self.assertEqual(report["boundary"]["trace_write"], "not_performed")
        self.assertEqual(
            report["recommended_next_action"],
            "local_knowledge_runtime_ready_for_explicit_business_trials",
        )

    def test_knowledge_runtime_doctor_returns_review_report(self):
        with patch(
            "backend.scripts.doctor.run_company_profile_explicit_api_local_smoke",
            return_value=_FakeSmokeReport(
                _smoke_payload(
                    decision="review",
                    reason_code="company_profile_explicit_api_review",
                    warnings=[{"component": "provider", "reason_code": "low_score"}],
                )
            ),
        ):
            report = doctor._build_knowledge_runtime_report(provider_base_url="http://knowledge.test")

        self.assertEqual(report["status"], "warn")
        self.assertEqual(report["decision"], "review")
        self.assertEqual(report["exit_code"], 2)
        self.assertEqual(report["checks"][0]["status"], "warn")
        self.assertEqual(report["warnings"][0]["reason_code"], "low_score")

    def test_knowledge_runtime_doctor_returns_blocked_report(self):
        with patch(
            "backend.scripts.doctor.run_company_profile_explicit_api_local_smoke",
            return_value=_FakeSmokeReport(
                _smoke_payload(
                    decision="blocked",
                    reason_code="provider_unreachable",
                    blockers=[{"component": "provider", "reason_code": "provider_unreachable"}],
                    document_count=0,
                    citations=[],
                )
            ),
        ):
            report = doctor._build_knowledge_runtime_report(provider_base_url="http://knowledge.test")

        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["decision"], "blocked")
        self.assertEqual(report["exit_code"], 1)
        self.assertEqual(report["checks"][0]["status"], "fail")
        self.assertEqual(
            report["recommended_next_action"],
            "start_unifiedKnowledgeRAG_provider_and_rerun_doctor",
        )

    def test_knowledge_runtime_doctor_redacts_provider_api_key(self):
        secret = "secret-provider-key"
        with patch(
            "backend.scripts.doctor.run_company_profile_explicit_api_local_smoke",
            return_value=_FakeSmokeReport(
                _smoke_payload(
                    decision="blocked",
                    reason_code="provider_api_key_leaked",
                    answer_preview=f"bad echo {secret}",
                    blockers=[{"component": "security", "message": secret}],
                )
            ),
        ):
            report = doctor._build_knowledge_runtime_report(
                provider_base_url="http://knowledge.test",
                provider_api_key=secret,
            )

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn(secret, serialized)
        self.assertIn("[REDACTED]", serialized)

    def test_knowledge_runtime_doctor_cli_exit_code_uses_decision(self):
        with patch(
            "backend.scripts.doctor.run_company_profile_explicit_api_local_smoke",
            return_value=_FakeSmokeReport(_smoke_payload(decision="review")),
        ):
            output = StringIO()
            with redirect_stdout(output):
                exit_code = doctor.main(["--knowledge-runtime", "--provider-base-url", "http://knowledge.test"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(json.loads(output.getvalue())["scope"], "knowledge_runtime")

    def test_knowledge_runtime_doctor_cli_preserves_go_exit_code(self):
        with patch(
            "backend.scripts.doctor.run_company_profile_explicit_api_local_smoke",
            return_value=_FakeSmokeReport(_smoke_payload(decision="go")),
        ):
            output = StringIO()
            with redirect_stdout(output):
                exit_code = doctor.main(["--knowledge-runtime", "--provider-base-url", "http://knowledge.test"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(output.getvalue())["decision"], "go")

    @patch("backend.routers.health.get_doctor_runtime_service")
    def test_doctor_api_returns_knowledge_runtime_report(self, mock_service_factory):
        mock_service_factory.return_value.run_knowledge_runtime_report.return_value = {
            "scope": "knowledge_runtime",
            "status": "ok",
            "decision": "go",
            "exit_code": 0,
            "checks": [],
            "boundary": {"default_chat_retrieval_injection": "disabled"},
        }
        app = create_app(
            config=AgentServerConfig(
                bootstrap=AgentServerBootstrapConfig(load_environment=False, init_database=False),
                ui=AgentServerUIConfig(enabled=False, mode="disabled"),
            )
        )
        client = TestClient(app)

        response = client.get(
            "/api/doctor?knowledge_runtime=true&provider_base_url=http://knowledge.test&agent_id=company_profile&domain=company.profile&query=公司主营业务是什么？&top_k=2&timeout_seconds=4"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scope"], "knowledge_runtime")
        mock_service_factory.return_value.run_knowledge_runtime_report.assert_called_once_with(
            provider_base_url="http://knowledge.test",
            provider_api_key=None,
            agent_id="company_profile",
            domain="company.profile",
            query="公司主营业务是什么？",
            top_k=2,
            timeout_seconds=4,
        )


class _FakeSmokeReport:
    def __init__(self, payload):
        self.payload = payload

    def to_dict(self):
        return dict(self.payload)


def _smoke_payload(
    *,
    decision,
    reason_code=None,
    warnings=None,
    blockers=None,
    answer_preview="基于 company_profile_2025_trial#chunk-4，已生成受控回答预览。",
    citations=None,
    document_count=1,
):
    if citations is None:
        citations = ["company_profile_2025_trial#chunk-4"]
    return {
        "contract_version": "company-profile-explicit-api-local-smoke-v1",
        "decision": decision,
        "reason_code": reason_code or (
            "company_profile_explicit_api_ready" if decision == "go" else "company_profile_explicit_api_review"
        ),
        "endpoint": "/api/domain-agents/company_profile/live-grounded-answer",
        "agent_id": "company_profile",
        "domain": "company.profile",
        "query": "公司主营业务是什么？",
        "provider_base_url": "http://knowledge.test",
        "http_status_code": 200,
        "ok": decision == "go",
        "api_status": "go" if decision == "go" else decision,
        "answer_preview": answer_preview,
        "citations": citations,
        "document_count": document_count,
        "blockers": blockers or [],
        "warnings": warnings or [],
        "boundary": {
            "default_chat_retrieval_injection": "disabled",
            "chat_invocation": "not_performed",
            "memory_write": "not_performed",
            "audit_write": "not_performed",
            "graphrag_execution": "not_promoted",
        },
    }


if __name__ == "__main__":
    unittest.main()
