import json
import unittest
from pathlib import Path

from backend.capability_runtime.business_rag_user_loop_closure import (
    build_business_rag_user_loop_closure,
    export_business_rag_user_loop_closure,
)


class BusinessRagUserLoopClosureTests(unittest.TestCase):
    def test_closure_go_when_corpus_and_explicit_api_are_ready(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        corpus_path.write_text(json.dumps(_corpus_trial(), ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = build_business_rag_user_loop_closure(
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "go")
        self.assertEqual(report.reason_code, "business_rag_user_loop_ready")
        self.assertEqual(report.source_id, "company_profile_2025_trial")
        self.assertEqual(report.citations, ["company_profile_2025_trial#chunk-4"])
        self.assertEqual(report.provider_base_url, "http://127.0.0.1:8020")
        self.assertEqual(report.blockers, [])

    def test_closure_blocks_missing_input_artifact(self):
        root = Path(self._tmp_dir())
        explicit_path = root / "explicit.json"
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = build_business_rag_user_loop_closure(
            corpus_trial_json_path=root / "missing.json",
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "input_artifact_missing")
        self.assertEqual(report.blockers[0]["component"], "corpus_trial")

    def test_closure_blocks_boundary_drift(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        explicit = _explicit_api_smoke()
        explicit["boundary"]["default_chat_retrieval_injection"] = "enabled"
        corpus_path.write_text(json.dumps(_corpus_trial(), ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(explicit, ensure_ascii=False), encoding="utf-8")

        report = build_business_rag_user_loop_closure(
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "explicit_boundary_drift")
        self.assertEqual(report.blockers[0]["component"], "boundary")

    def test_export_writes_json_and_markdown(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        output_dir = root / "out"
        corpus_path.write_text(json.dumps(_corpus_trial(), ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = export_business_rag_user_loop_closure(
            output_dir=output_dir,
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "go")
        self.assertTrue(report.json_path.exists())
        self.assertTrue(report.markdown_path.exists())
        self.assertIn("Business RAG User Loop Closure", report.markdown_path.read_text(encoding="utf-8"))

    def _tmp_dir(self):
        import tempfile

        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return temp_dir.name


def _corpus_trial():
    return {
        "id": "local-knowledge-provider-corpus-trial-v1",
        "generated_at": "2026-06-07T00:00:00+00:00",
        "provider_base_url": "http://127.0.0.1:8020",
        "source_id": "company_profile_2025_trial",
        "decision": "go",
        "reason_code": "local_corpus_trial_accepted",
        "summary": {
            "case_count": 5,
            "ready_case_count": 5,
            "blocked_case_count": 0,
            "invalid_citation_count": 0,
        },
    }


def _explicit_api_smoke():
    return {
        "contract_version": "company-profile-explicit-api-local-smoke-v1",
        "generated_at": "2026-06-07T00:00:00+00:00",
        "decision": "go",
        "reason_code": "company_profile_explicit_api_ready",
        "endpoint": "/api/domain-agents/company_profile/live-grounded-answer",
        "agent_id": "company_profile",
        "domain": "company.profile",
        "query": "公司主营业务是什么？",
        "provider_base_url": "http://127.0.0.1:8020",
        "http_status_code": 200,
        "api_status": "go",
        "document_count": 1,
        "answer_preview": "基于 company_profile_2025_trial#chunk-4，已生成受控回答预览。",
        "citations": ["company_profile_2025_trial#chunk-4"],
        "boundary": {
            "default_chat_retrieval_injection": "disabled",
            "chat_invocation": "not_performed",
            "model_invocation": "not_performed",
            "tool_execution": "not_performed",
            "source_binding_creation": "not_performed",
            "memory_write": "not_performed",
            "audit_write": "not_performed",
            "trace_write": "not_performed",
            "graphrag_execution": "not_promoted",
            "runtime_behavior_changed": False,
        },
    }


if __name__ == "__main__":
    unittest.main()

