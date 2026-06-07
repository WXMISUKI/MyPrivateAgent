import json
import tempfile
import textwrap
import unittest
from pathlib import Path

import httpx

from backend.services.domain_agent_live_grounded_answer_api_service import (
    DomainAgentLiveGroundedAnswerApiService,
)
from backend.services.domain_agent_live_grounded_answer_trial_service import (
    DomainAgentLiveGroundedAnswerTrialService,
)
from backend.services.domain_agent_registry_service import DomainAgentRegistryService


def _json_response(payload, status_code=200):
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode("utf-8"),
    )


class DomainAgentLiveGroundedAnswerApiServiceTests(unittest.TestCase):
    def test_api_response_is_compact_and_uses_manifest_rag_source(self):
        service = self._service()
        seen_payload = {}

        def handler(request):
            seen_payload.update(json.loads(request.content.decode("utf-8")))
            return _answerable_response()

        response = service.run(
            agent_id="company_profile",
            domain="company.profile",
            query="公司主营业务是什么？",
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
            eval_dir=self._eval_dir(),
        )

        self.assertTrue(response["ok"])
        self.assertEqual(response["status"], "go")
        self.assertEqual(response["reason_code"], "live_grounded_answer_trial_ready")
        self.assertIn("company_profile_2025_trial#chunk-4", response["citations"])
        self.assertEqual(response["documents"][0]["source_id"], "company_profile_2025_trial")
        self.assertEqual(response["boundary"]["default_chat_retrieval_injection"], "disabled")
        self.assertEqual(response["trial"]["provider_retrieve"]["knowledge_base_ids"], ["company_profile_2025_trial"])
        self.assertEqual(seen_payload["knowledge_base_ids"], ["company_profile_2025_trial"])

    def test_api_response_blocks_provider_failure(self):
        service = self._service()

        def handler(request):
            return _json_response({"error": {"code": "RAG_DOWN", "message": "down"}}, status_code=503)

        response = service.run(
            agent_id="company_profile",
            query="公司主营业务是什么？",
            provider_base_url="http://knowledge.test",
            transport=httpx.MockTransport(handler),
            eval_dir=self._eval_dir(),
        )

        self.assertFalse(response["ok"])
        self.assertEqual(response["status"], "blocked")
        self.assertEqual(response["reason_code"], "RAG_DOWN")
        self.assertEqual(response["blockers"][0]["component"], "provider")

    def test_provider_api_key_is_used_but_not_echoed(self):
        service = self._service()
        secret = "secret-provider-key"

        def handler(request):
            self.assertEqual(request.headers.get("authorization"), f"Bearer {secret}")
            self.assertEqual(request.headers.get("x-provider-api-key"), secret)
            return _answerable_response()

        response = service.run(
            agent_id="company_profile",
            query="公司主营业务是什么？",
            provider_base_url="http://knowledge.test",
            provider_api_key=secret,
            transport=httpx.MockTransport(handler),
            eval_dir=self._eval_dir(),
        )

        serialized = json.dumps(response, ensure_ascii=False)
        self.assertTrue(response["ok"])
        self.assertNotIn(secret, serialized)

    def _service(self):
        trial_service = DomainAgentLiveGroundedAnswerTrialService(registry_service=self._registry_service())
        return DomainAgentLiveGroundedAnswerApiService(trial_service=trial_service)

    def _registry_service(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        agent_dir = root / "company_profile"
        agent_dir.mkdir()
        manifest = """
            id: company_profile
            name: Company Profile
            version: 0.1.0
            roles:
              - id: default
                default: true
            capabilities:
              rag_sources:
                - company_profile_2025_trial
            grounding_policy:
              require_citations: true
              allow_ungrounded: false
              must_use_knowledge_for_domains:
                - company.profile
              fallback_policy: refuse_or_clarify_when_no_evidence
              source_acl_mode: agent_manifest
        """
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
                    "turns": [{"role": "user", "content": "公司主营业务是什么？"}],
                    "evidence": {"promptops": {"prompt_key": "company_profile", "version": "1"}},
                    "assertions": {"promptops": {"prompt_key": "company_profile", "version": "1"}},
                }
            ),
            encoding="utf-8",
        )
        return eval_dir


def _answerable_response():
    return _json_response(
        {
            "ok": True,
            "result": {
                "documents": [
                    {
                        "source_id": "company_profile_2025_trial",
                        "document_id": "company_profile_2025_trial",
                        "title": "公司简介2025",
                        "snippet": "公司主要经营高等级公路、大型桥梁和隧道工程及水运工程的施工监理。",
                        "score": 0.93,
                        "citation": "company_profile_2025_trial#chunk-4",
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


if __name__ == "__main__":
    unittest.main()
