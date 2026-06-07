import json
import unittest
from pathlib import Path

from backend.services.company_profile_explicit_api_local_smoke_service import (
    export_company_profile_explicit_api_local_smoke,
    run_company_profile_explicit_api_local_smoke,
)


class CompanyProfileExplicitApiLocalSmokeServiceTests(unittest.TestCase):
    def test_smoke_go_with_compact_api_response(self):
        seen = {}
        report = run_company_profile_explicit_api_local_smoke(
            provider_base_url="http://knowledge.test",
            query="公司主营业务是什么？",
            client=_FakeClient(_go_response(), seen=seen),
        )

        self.assertEqual(report.decision, "go")
        self.assertEqual(report.reason_code, "company_profile_explicit_api_ready")
        self.assertEqual(report.citations, ["company_profile_2025_trial#chunk-4"])
        self.assertEqual(report.document_count, 1)
        self.assertEqual(seen["json"]["query"], "公司主营业务是什么？")
        self.assertEqual(seen["json"]["provider_base_url"], "http://knowledge.test")

    def test_smoke_blocks_provider_failure(self):
        report = run_company_profile_explicit_api_local_smoke(
            provider_base_url="http://knowledge.test",
            client=_FakeClient(
                {
                    "ok": False,
                    "status": "blocked",
                    "reason_code": "provider_unreachable",
                    "blockers": [{"component": "provider", "reason_code": "provider_unreachable"}],
                    "boundary": {"default_chat_retrieval_injection": "disabled"},
                }
            ),
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "provider_unreachable")
        self.assertEqual(report.blockers[0]["component"], "provider")

    def test_smoke_blocks_missing_boundary(self):
        payload = _go_response()
        payload["boundary"] = {}

        report = run_company_profile_explicit_api_local_smoke(
            provider_base_url="http://knowledge.test",
            client=_FakeClient(payload),
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "explicit_api_boundary_missing")

    def test_smoke_export_redacts_provider_api_key(self):
        secret = "secret-provider-key"

        with self.subTest("go response"):
            report = export_company_profile_explicit_api_local_smoke(
                output_dir=Path(self._tmp_dir()) / "out",
                provider_base_url="http://knowledge.test",
                provider_api_key=secret,
                client=_FakeClient(_go_response()),
            )

        serialized = json.dumps(report.to_dict(), ensure_ascii=False)
        self.assertEqual(report.decision, "go")
        self.assertNotIn(secret, serialized)
        self.assertNotIn(secret, report.json_path.read_text(encoding="utf-8"))
        self.assertNotIn(secret, report.markdown_path.read_text(encoding="utf-8"))

    def test_smoke_blocks_when_api_key_is_echoed(self):
        secret = "secret-provider-key"
        payload = _go_response()
        payload["echoed_secret"] = secret

        report = run_company_profile_explicit_api_local_smoke(
            provider_base_url="http://knowledge.test",
            provider_api_key=secret,
            client=_FakeClient(payload),
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "provider_api_key_leaked")

    def _tmp_dir(self):
        import tempfile

        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return temp_dir.name


def _go_response():
    return {
        "ok": True,
        "status": "go",
        "reason_code": "live_grounded_answer_trial_ready",
        "recommended_next_action": "proceed_with_explicit_grounded_answer_trial",
        "agent_id": "company_profile",
        "domain": "company.profile",
        "query": "公司主营业务是什么？",
        "provider_base_url": "http://knowledge.test",
        "answer_preview": "基于 company_profile_2025_trial#chunk-4，已生成受控回答预览。",
        "citations": ["company_profile_2025_trial#chunk-4"],
        "documents": [{"source_id": "company_profile_2025_trial", "citation": "company_profile_2025_trial#chunk-4"}],
        "blockers": [],
        "warnings": [],
        "boundary": {
            "default_chat_retrieval_injection": "disabled",
            "chat_invocation": "not_performed",
            "memory_write": "not_performed",
            "audit_write": "not_performed",
            "graphrag_execution": "not_promoted",
        },
        "trial": {},
    }


class _FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, payload, *, seen=None, status_code=200):
        self.payload = payload
        self.seen = seen
        self.status_code = status_code

    def post(self, endpoint, json):
        if self.seen is not None:
            self.seen["endpoint"] = endpoint
            self.seen["json"] = json
        return _FakeResponse(self.payload, status_code=self.status_code)


if __name__ == "__main__":
    unittest.main()
