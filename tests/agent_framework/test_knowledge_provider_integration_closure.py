import json
import tempfile
import unittest
from pathlib import Path

from backend.capability_runtime.knowledge_provider_integration_closure import (
    build_knowledge_provider_integration_closure,
    export_knowledge_provider_integration_closure,
    render_knowledge_provider_integration_closure_markdown,
)


class KnowledgeProviderIntegrationClosureTests(unittest.TestCase):
    def test_closure_goes_when_phase19_trial_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            trial_path = Path(tmp) / "trial.json"
            trial_path.write_text(json.dumps(_trial_payload()), encoding="utf-8")

            closure = build_knowledge_provider_integration_closure(trial_outcome_path=trial_path)

            self.assertEqual(closure.decision, "go")
            self.assertEqual(closure.evidence_chain_status, "closed")
            self.assertEqual(closure.recommended_next_line, "continue_with_agent_grounding_policy_contract")
            self.assertEqual(closure.summary["default_chat_retrieval_injection"], "disabled")
            self.assertEqual(closure.summary["graph_rag_promotion_status"], "not_promoted")
            self.assertEqual(closure.summary["ready_required_check_count"], 5)

    def test_closure_reviews_non_blocking_trial_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            trial_path = Path(tmp) / "trial.json"
            payload = _trial_payload(status="trial_review", decision="review_trial_context_before_integration_hardening")
            payload["checks"][3]["status"] = "review"
            trial_path.write_text(json.dumps(payload), encoding="utf-8")

            closure = build_knowledge_provider_integration_closure(trial_outcome_path=trial_path)

            self.assertEqual(closure.decision, "review")
            self.assertEqual(closure.evidence_chain_status, "closed_with_review")
            self.assertEqual(closure.summary["review_required_check_count"], 1)

    def test_closure_blocks_when_trial_outcome_missing(self):
        closure = build_knowledge_provider_integration_closure(
            trial_outcome_path=Path("missing-phase19-trial-outcome.json")
        )

        self.assertEqual(closure.decision, "blocked")
        self.assertEqual(closure.evidence_chain_status, "blocked")
        self.assertEqual(closure.summary["missing_required_check_count"], 5)
        self.assertIn("regenerate_phase19_trial_outcome", closure.required_checks[0]["recommended_action"])

    def test_closure_export_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trial_path = root / "trial.json"
            output_dir = root / "out"
            trial_path.write_text(json.dumps(_trial_payload()), encoding="utf-8")

            closure = export_knowledge_provider_integration_closure(
                trial_outcome_path=trial_path,
                output_dir=output_dir,
            )

            payload = json.loads(closure.json_path.read_text(encoding="utf-8"))
            markdown = closure.markdown_path.read_text(encoding="utf-8")
            self.assertEqual(payload["decision"], "go")
            self.assertIn("# Phase 20 Unified Knowledge Provider Integration Closure", markdown)
            self.assertIn("default_chat_retrieval_injection", markdown)
            self.assertIn(
                "# Phase 20 Unified Knowledge Provider Integration Closure",
                render_knowledge_provider_integration_closure_markdown(closure),
            )


def _trial_payload(
    *,
    status: str = "trial_passed",
    decision: str = "proceed_with_myprivateagent_integration_hardening",
):
    return {
        "id": "unified-knowledge-provider-repo-side-trial-v1",
        "status": status,
        "decision": decision,
        "provider_base_url": "http://127.0.0.1:8021",
        "summary": {
            "source_binding_policy_owner": "caller",
            "runtime_promotion_status": "unchanged",
        },
        "checks": [
            _check("provider_health"),
            _check("provider_manifest"),
            _check("provider_preflight"),
            _check("source_bindings"),
            _check("rag_retrieve"),
        ],
    }


def _check(check_id: str):
    return {
        "id": check_id,
        "status": "ready",
        "summary": {},
        "recommended_action": "no_action_required",
        "error": None,
    }


if __name__ == "__main__":
    unittest.main()
