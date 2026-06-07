import json
import unittest
from pathlib import Path

from backend.capability_runtime.local_knowledge_base_user_loop import (
    build_local_knowledge_base_user_loop,
    export_local_knowledge_base_user_loop,
)


SOURCE_ID = "company_profile_2025_trial"
CITATION = f"{SOURCE_ID}#chunk-4"


class LocalKnowledgeBaseUserLoopTests(unittest.TestCase):
    def test_user_loop_go_with_ready_artifacts(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        corpus_path.write_text(json.dumps(_corpus_trial(), ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = build_local_knowledge_base_user_loop(
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "go")
        self.assertEqual(report.reason_code, "local_knowledge_base_user_loop_ready")
        self.assertEqual(report.source["source_id"], SOURCE_ID)
        self.assertEqual(report.entrypoint["endpoint"], "/api/domain-agents/company_profile/live-grounded-answer")
        self.assertEqual(report.citation_summary["citations"], [CITATION])
        self.assertGreaterEqual(len(report.suggested_questions), 3)
        self.assertEqual(report.blockers, [])

    def test_user_loop_reviews_non_blocking_corpus_warning(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        corpus = _corpus_trial(decision="review", reason_code="local_corpus_trial_needs_review")
        corpus["summary"]["review_case_count"] = 1
        corpus_path.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = build_local_knowledge_base_user_loop(
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "review")
        self.assertEqual(report.reason_code, "local_knowledge_base_user_loop_review_required")
        self.assertEqual(report.warnings[0]["component"], "corpus_trial")

    def test_user_loop_blocks_missing_artifact(self):
        root = Path(self._tmp_dir())
        explicit_path = root / "explicit.json"
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = build_local_knowledge_base_user_loop(
            corpus_trial_json_path=root / "missing.json",
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "input_artifact_missing")
        self.assertEqual(report.blockers[0]["component"], "corpus_trial")

    def test_user_loop_blocks_source_mismatch(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        corpus = _corpus_trial()
        corpus["source_id"] = "other_source"
        corpus_path.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = build_local_knowledge_base_user_loop(
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "source_id_mismatch")

    def test_user_loop_blocks_missing_citations(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        explicit = _explicit_api_smoke()
        explicit["citations"] = []
        corpus_path.write_text(json.dumps(_corpus_trial(), ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(explicit, ensure_ascii=False), encoding="utf-8")

        report = build_local_knowledge_base_user_loop(
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "citations_missing")

    def test_user_loop_blocks_boundary_drift(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        explicit = _explicit_api_smoke()
        explicit["boundary"]["model_invocation"] = "performed"
        corpus_path.write_text(json.dumps(_corpus_trial(), ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(explicit, ensure_ascii=False), encoding="utf-8")

        report = build_local_knowledge_base_user_loop(
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "blocked")
        self.assertEqual(report.reason_code, "runtime_boundary_drift")
        self.assertEqual(report.blockers[0]["component"], "boundary")

    def test_export_writes_json_and_markdown(self):
        root = Path(self._tmp_dir())
        corpus_path = root / "corpus.json"
        explicit_path = root / "explicit.json"
        output_dir = root / "out"
        corpus_path.write_text(json.dumps(_corpus_trial(), ensure_ascii=False), encoding="utf-8")
        explicit_path.write_text(json.dumps(_explicit_api_smoke(), ensure_ascii=False), encoding="utf-8")

        report = export_local_knowledge_base_user_loop(
            output_dir=output_dir,
            corpus_trial_json_path=corpus_path,
            explicit_api_smoke_json_path=explicit_path,
        )

        self.assertEqual(report.decision, "go")
        self.assertTrue(report.json_path.exists())
        self.assertTrue(report.markdown_path.exists())
        self.assertIn("Local Knowledge Base User Loop", report.markdown_path.read_text(encoding="utf-8"))

    def _tmp_dir(self):
        import tempfile

        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        return temp_dir.name


def _corpus_trial(decision="go", reason_code="local_corpus_trial_accepted"):
    return {
        "id": "local-knowledge-provider-corpus-trial-v1",
        "generated_at": "2026-06-07T00:00:00+00:00",
        "provider_base_url": "http://127.0.0.1:8020",
        "source_id": SOURCE_ID,
        "top_k": 3,
        "decision": decision,
        "reason_code": reason_code,
        "summary": {
            "case_count": 5,
            "ready_case_count": 5,
            "review_case_count": 0,
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
        "citations": [CITATION],
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
