import json
import tempfile
import textwrap
import unittest
from pathlib import Path

import httpx

from backend.services.domain_agent_live_grounded_answer_trial_service import (
    DomainAgentLiveGroundedAnswerTrialService,
    render_domain_agent_live_grounded_answer_trial_markdown,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class DomainAgentLiveGroundedAnswerTrialServiceTests(unittest.TestCase):
    def test_live_trial_goes_with_answerable_provider_evidence(self):
        service = DomainAgentLiveGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            query="退款政策是什么？",
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(_answerable_provider_handler),
            eval_dir=self._eval_dir(),
        )

        self.assertEqual(report.live_trial_status, "go")
        self.assertEqual(report.provider_retrieve["status"], "ready")
        self.assertEqual(report.provider_retrieve["knowledge_base_ids"], ["refund_policy_docs"])
        self.assertEqual(report.trial_report["trial_status"], "go")
        self.assertEqual(report.package["package_status"], "ready")
        self.assertEqual(report.composition["composition_status"], "ready")
        self.assertEqual(report.provider_retrieve["allowed_citations"], ["refund_policy_2026#section-3"])
        self.assertEqual(report.boundary["chat_invocation"], "not_performed")
        self.assertEqual(report.boundary["source_binding_creation"], "not_performed")
        self.assertFalse(report.boundary["runtime_behavior_changed"])
        self.assertIn("# Domain Agent Live Grounded Answer Trial", render_domain_agent_live_grounded_answer_trial_markdown(report))

    def test_live_trial_blocks_insufficient_evidence_for_citation_required_agent(self):
        service = DomainAgentLiveGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="ecommerce_support",
            domain="refund.policy",
            query="没有证据的问题",
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(_insufficient_provider_handler),
            eval_dir=self._eval_dir(),
        )

        self.assertEqual(report.live_trial_status, "blocked")
        self.assertEqual(report.provider_retrieve["evidence_pack_status"], "insufficient_evidence")
        self.assertEqual(report.trial_report["grounding_decision"]["reason_code"], "insufficient_evidence")
        self.assertIn(
            {"component": "grounding", "status": "blocked", "reason_code": "insufficient_evidence"},
            report.blockers,
        )

    def test_live_trial_blocks_missing_agent_without_provider_call(self):
        called = False

        def handler(request):
            nonlocal called
            called = True
            return _json_response({})

        service = DomainAgentLiveGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="missing_agent",
            query="退款政策是什么？",
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
            eval_dir=self._eval_dir(),
        )

        self.assertEqual(report.live_trial_status, "blocked")
        self.assertEqual(report.reason_code, "agent_not_found")
        self.assertFalse(called)

    def test_live_trial_blocks_agent_without_rag_sources(self):
        service = DomainAgentLiveGroundedAnswerTrialService(registry_service=self._registry_service(include_sources=False))

        report = service.run_trial(
            agent_id="ecommerce_support",
            query="退款政策是什么？",
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(_answerable_provider_handler),
            eval_dir=self._eval_dir(),
        )

        self.assertEqual(report.live_trial_status, "blocked")
        self.assertEqual(report.reason_code, "rag_sources_missing")

    def test_live_trial_blocks_provider_http_failure(self):
        def handler(request):
            return _json_response({"error": {"code": "RAG_DOWN", "message": "down"}}, status_code=503)

        service = DomainAgentLiveGroundedAnswerTrialService(registry_service=self._registry_service())

        report = service.run_trial(
            agent_id="ecommerce_support",
            query="退款政策是什么？",
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
            eval_dir=self._eval_dir(),
        )

        self.assertEqual(report.live_trial_status, "blocked")
        self.assertEqual(report.provider_retrieve["reason_code"], "RAG_DOWN")
        self.assertIn(
            {"component": "provider", "status": "blocked", "reason_code": "RAG_DOWN"},
            report.blockers,
        )

    def test_live_trial_export_writes_artifacts(self):
        service = DomainAgentLiveGroundedAnswerTrialService(registry_service=self._registry_service())
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            report = service.export_trial(
                output_dir=output_dir,
                agent_id="ecommerce_support",
                domain="refund.policy",
                query="退款政策是什么？",
                provider_base_url="http://knowledge.test",
                transport=httpx.MockTransport(_answerable_provider_handler),
                eval_dir=self._eval_dir(),
            )

            payload = json.loads(report.json_path.read_text(encoding="utf-8"))
            markdown = report.markdown_path.read_text(encoding="utf-8")
            self.assertEqual(payload["live_trial_status"], "go")
            self.assertIn("Domain Agent Live Grounded Answer Trial", markdown)

    def _registry_service(self, *, include_sources=True):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        agent_dir = root / "ecommerce_support"
        agent_dir.mkdir()
        source_block = (
            """
              rag_sources:
                - refund_policy_docs
            """
            if include_sources
            else ""
        )
        manifest = (
            """
            id: ecommerce_support
            name: Ecommerce Support
            version: 0.1.0
            roles:
              - id: default
                default: true
            capabilities:
            """
            + source_block
            + """
            grounding_policy:
              require_citations: true
              allow_ungrounded: false
              must_use_knowledge_for_domains:
                - refund.policy
              fallback_policy: refuse_or_clarify_when_no_evidence
              source_acl_mode: agent_manifest
            """
        )
        (agent_dir / "agent.yaml").write_text(textwrap.dedent(manifest).strip(), encoding="utf-8")
        return DomainAgentRegistryService(root)

    def _eval_dir(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        eval_dir = Path(temp_dir.name)
        (eval_dir / "scenario.json").write_text(
            json.dumps(
                {
                    "id": "prompt_version_visibility",
                    "enabled": True,
                    "turns": [{"role": "user", "content": "退款政策是什么？"}],
                    "evidence": {"promptops": {"prompt_key": "refund_policy", "version": "1"}},
                    "assertions": {"promptops": {"prompt_key": "refund_policy", "version": "1"}},
                }
            ),
            encoding="utf-8",
        )
        return eval_dir


def _answerable_provider_handler(request):
    payload = json.loads(request.content.decode("utf-8"))
    assert request.url.path == "/api/rag/retrieve"
    assert payload["knowledge_base_ids"] == ["refund_policy_docs"]
    return _json_response(
        {
            "ok": True,
            "result": {
                "documents": [
                    {
                        "source_id": "refund_policy_docs",
                        "document_id": "refund_policy_2026",
                        "title": "Refund Policy",
                        "snippet": "refund snippet",
                        "score": 0.91,
                        "citation": "refund_policy_2026#section-3",
                    }
                ],
                "metadata": {
                    "evidence_pack": {
                        "version": "evidence-pack-v1",
                        "status": "answerable",
                        "citation_policy": "use_only_returned_citations",
                    }
                },
            },
        }
    )


def _insufficient_provider_handler(request):
    return _json_response(
        {
            "ok": True,
            "result": {
                "documents": [],
                "metadata": {
                    "evidence_pack": {
                        "version": "evidence-pack-v1",
                        "status": "insufficient_evidence",
                        "allowed_citations": [],
                        "citation_policy": "use_only_returned_citations",
                    }
                },
            },
        }
    )


if __name__ == "__main__":
    unittest.main()
