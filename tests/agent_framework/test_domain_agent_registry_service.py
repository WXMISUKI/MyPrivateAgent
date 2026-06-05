import tempfile
import textwrap
import unittest
from pathlib import Path

from backend.services.domain_agent_registry_service import DomainAgentRegistryService
from backend.services.runtime_surface_service import RuntimeSurfaceProfileAssembler


class _StaticContractService:
    def __init__(self, contract):
        self._contract = contract

    def build_runtime_contract(self, *args, **kwargs):
        return dict(self._contract)

    def build_rag_source_registry_contract(self):
        return {
            "contract_version": "rag-source-registry-v1",
            "status": "empty",
            "total_entries": 0,
            "entries": [],
        }

    def build_knowledge_graph_registry_contract(self):
        return {
            "contract_version": "knowledge-graph-registry-v1",
            "status": "empty",
            "total_entries": 0,
            "entries": [],
        }


class _RuntimeFactoryStub:
    def build_runtime_contract(self):
        return {
            "embedded_runtime_factory": {"status": "ready"},
            "embedded_runtime_bootstrap": {"status": "ready"},
            "default_runtime_recovery": {"status": "ready"},
        }


class _ConfigServiceStub:
    def get_effective_config(self):
        return {}

    def get_config_layers(self):
        return []

    def load_overrides(self):
        return {}


class _RuntimeSurfaceStub:
    def __init__(self):
        self.config_service = _ConfigServiceStub()
        self.command_registry_service = _StaticContractService({"commands": []})
        self.domain_agent_registry_service = _StaticContractService(
            {
                "contract_version": "domain-agent-registry-v1",
                "status": "empty",
                "grounding_policy_registry": {
                    "contract_version": "agent-grounding-policy-registry-v1",
                    "status": "empty",
                    "enforcement": "visibility_only",
                    "total_entries": 0,
                    "ready_entries": 0,
                    "unknown_entries": 0,
                    "degraded_entries": 0,
                    "entries": [],
                },
            }
        )
        self.tool_runtime_service = _StaticContractService({"contract_version": "tool-runtime-v1"})
        self.tool_runtime_service.build_adapter_health_contract = lambda: {"status": "ready"}
        self.mcp_runtime_service = _StaticContractService({"contract_version": "mcp-runtime-v1"})
        self.capability_profile_service = _StaticContractService({})
        self.skill_runtime_service = _StaticContractService({})
        self.agent_memory_service = _StaticContractService({})
        self.subagent_runtime_service = _StaticContractService({})
        self.agent_hook_service = _StaticContractService({})
        self.contract_gate_service = _StaticContractService({})
        self.self_improvement_ledger_service = _StaticContractService({})
        self.query_control_plane_service = _StaticContractService({})
        self.contract_snapshot_service = type(
            "SnapshotService",
            (),
            {"build_snapshot": staticmethod(lambda profile: {"status": "ok"})},
        )()
        self.runtime_factory = _RuntimeFactoryStub()

    def _list_all_models(self):
        return []

    def _build_runtime_scope_contract(self, **kwargs):
        return {}

    def _build_main_chat_trace_overview_contract(self, **kwargs):
        return {}

    def _build_main_chat_query_detail_contract(self, **kwargs):
        return {}

    def _build_external_adapter_recent_summary_contract(self, **kwargs):
        return {}

    def get_channel_promotion_gate(self, **kwargs):
        return {}

    def _build_run_recovery_contract(self):
        return {"status": "ready"}

    def _build_child_executor_preflight_contract(self, command_contract):
        return {"backend_registry": {}}

    def _build_child_executor_promotion_gate_contract(self, command_contract, child_executor_preflight):
        return {}

    def _build_child_executor_dispatch_contract(self, command_contract, child_executor_promotion_gate):
        return {}

    def _build_runtime_core_contract(self, runtime_scope):
        return {"status": "not_started"}

    def _build_governance_overview_contract(self, **kwargs):
        return {}

    def _build_embedded_runtime_boundaries_contract(self, command_contract):
        return {}


class DomainAgentRegistryServiceTests(unittest.TestCase):
    def test_valid_domain_agent_manifest_is_listed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            agent_dir = root / "ecommerce_support"
            agent_dir.mkdir()
            (agent_dir / "agent.yaml").write_text(
                textwrap.dedent(
                    """
                    id: ecommerce_support
                    name: Ecommerce Support
                    version: 0.1.0
                    description: Order and refund support agent
                    roles:
                      - id: after_sales_specialist
                        name: After Sales Specialist
                        default: true
                    capabilities:
                      tools:
                        - order.lookup
                      skills:
                        - refund_policy
                      mcp_servers:
                        - ecommerce_order_mcp
                      rag_sources:
                        - refund_policy_docs
                      graph_sources:
                        - ecommerce_order_graph
                    grounding_policy:
                      require_citations: true
                      allow_ungrounded: false
                      must_use_knowledge_for_domains:
                        - refund.policy
                        - logistics.diagnosis
                      fallback_policy: refuse_or_clarify_when_no_evidence
                      source_acl_mode: agent_manifest
                    governance:
                      approval_required:
                        - refund.create_request
                      audit_tags:
                        - ecommerce
                    """
                ).strip(),
                encoding="utf-8",
            )

            contract = DomainAgentRegistryService(root).build_runtime_contract()

            self.assertEqual(contract["status"], "ready")
            self.assertEqual(contract["total_agents"], 1)
            self.assertEqual(contract["ready_agents"], 1)
            agent = contract["agents"][0]
            self.assertEqual(agent["id"], "ecommerce_support")
            self.assertEqual(agent["status"], "ready")
            self.assertEqual(agent["roles"][0]["id"], "after_sales_specialist")
            self.assertEqual(agent["capabilities"]["tools"], ["order.lookup"])
            self.assertEqual(agent["capabilities"]["rag_sources"], ["refund_policy_docs"])
            self.assertEqual(agent["capabilities"]["graph_sources"], ["ecommerce_order_graph"])
            self.assertEqual(agent["grounding_policy"]["policy_source"], "grounding_policy")
            self.assertTrue(agent["grounding_policy"]["require_citations"])
            self.assertFalse(agent["grounding_policy"]["allow_ungrounded"])
            self.assertEqual(
                agent["grounding_policy"]["must_use_knowledge_for_domains"],
                ["refund.policy", "logistics.diagnosis"],
            )
            self.assertEqual(agent["grounding_policy"]["fallback_policy"], "refuse_or_clarify_when_no_evidence")
            self.assertEqual(agent["grounding_policy"]["source_acl_mode"], "agent_manifest")
            self.assertEqual(agent["grounding_policy_status"]["status"], "unknown")
            self.assertEqual(agent["grounding_policy_status"]["enforcement"], "visibility_only")
            self.assertEqual(agent["governance"]["approval_required"], ["refund.create_request"])
            self.assertEqual(agent["agent_dir"], str(agent_dir))
            self.assertEqual(agent["manifest_path"], str(agent_dir / "agent.yaml"))

            rag_registry = DomainAgentRegistryService(root).build_rag_source_registry_contract()
            graph_registry = DomainAgentRegistryService(root).build_knowledge_graph_registry_contract()

            self.assertEqual(rag_registry["status"], "ready")
            self.assertEqual(rag_registry["entries"][0]["source_id"], "refund_policy_docs")
            self.assertEqual(rag_registry["entries"][0]["agent_id"], "ecommerce_support")
            self.assertEqual(graph_registry["status"], "ready")
            self.assertEqual(graph_registry["entries"][0]["graph_id"], "ecommerce_order_graph")
            self.assertEqual(graph_registry["entries"][0]["agent_id"], "ecommerce_support")
            grounding_registry = contract["grounding_policy_registry"]
            self.assertEqual(grounding_registry["status"], "unknown")
            self.assertEqual(grounding_registry["total_entries"], 1)
            self.assertEqual(grounding_registry["entries"][0]["agent_id"], "ecommerce_support")
            self.assertEqual(grounding_registry["entries"][0]["policy_source"], "grounding_policy")

    def test_legacy_retrieval_policy_maps_to_grounding_policy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            agent_dir = root / "legacy_agent"
            agent_dir.mkdir()
            (agent_dir / "agent.yaml").write_text(
                textwrap.dedent(
                    """
                    id: legacy_agent
                    name: Legacy Agent
                    version: 0.1.0
                    roles:
                      - id: default
                        default: true
                    capabilities:
                      rag_sources:
                        - legacy_docs
                    retrieval:
                      mode: agentic
                      default_top_k: 5
                      require_citations: true
                      graph_usage: relationship_questions_only
                      fallback_policy: clarify
                    """
                ).strip(),
                encoding="utf-8",
            )

            contract = DomainAgentRegistryService(root).build_runtime_contract()
            agent = contract["agents"][0]

            self.assertEqual(agent["grounding_policy"]["policy_source"], "retrieval")
            self.assertTrue(agent["grounding_policy"]["require_citations"])
            self.assertEqual(agent["grounding_policy"]["compatibility"]["mode"], "agentic")
            self.assertEqual(agent["grounding_policy"]["compatibility"]["default_top_k"], 5)
            self.assertEqual(
                agent["grounding_policy"]["compatibility"]["graph_usage"],
                "relationship_questions_only",
            )
            self.assertEqual(agent["grounding_policy"]["fallback_policy"], "clarify")
            self.assertEqual(agent["grounding_policy_status"]["status"], "unknown")

    def test_invalid_manifest_reports_missing_required_field(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            agent_dir = root / "broken_agent"
            agent_dir.mkdir()
            (agent_dir / "agent.yaml").write_text(
                "id: broken_agent\nversion: 0.1.0\nroles:\n  - id: default\n",
                encoding="utf-8",
            )

            contract = DomainAgentRegistryService(root).build_runtime_contract()

            self.assertEqual(contract["status"], "degraded")
            self.assertEqual(contract["total_agents"], 1)
            self.assertEqual(contract["ready_agents"], 0)
            self.assertEqual(contract["invalid_agents"], 1)
            self.assertIn("name", contract["errors"][0]["message"])

    def test_empty_directory_returns_stable_empty_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DomainAgentRegistryService(Path(temp_dir))
            contract = service.build_runtime_contract()
            rag_registry = service.build_rag_source_registry_contract()
            graph_registry = service.build_knowledge_graph_registry_contract()

            self.assertEqual(contract["contract_version"], "domain-agent-registry-v1")
            self.assertEqual(contract["status"], "empty")
            self.assertEqual(contract["total_agents"], 0)
            self.assertEqual(contract["agents"], [])
            self.assertEqual(contract["errors"], [])
            self.assertEqual(contract["grounding_policy_registry"]["status"], "empty")
            self.assertEqual(contract["grounding_policy_registry"]["total_entries"], 0)
            self.assertEqual(rag_registry["status"], "empty")
            self.assertEqual(rag_registry["total_entries"], 0)
            self.assertEqual(graph_registry["status"], "empty")
            self.assertEqual(graph_registry["total_entries"], 0)

    def test_runtime_surface_profile_exposes_domain_agent_registry(self):
        profile = RuntimeSurfaceProfileAssembler.assemble(_RuntimeSurfaceStub())

        self.assertIn("domain_agent_registry", profile)
        self.assertIn("rag_source_registry", profile)
        self.assertIn("knowledge_graph_registry", profile)
        self.assertEqual(
            profile["domain_agent_registry"]["contract_version"],
            "domain-agent-registry-v1",
        )
        self.assertEqual(profile["rag_source_registry"]["contract_version"], "rag-source-registry-v1")
        self.assertEqual(
            profile["knowledge_graph_registry"]["contract_version"],
            "knowledge-graph-registry-v1",
        )
        self.assertEqual(
            profile["domain_agent_registry"]["grounding_policy_registry"]["contract_version"],
            "agent-grounding-policy-registry-v1",
        )


if __name__ == "__main__":
    unittest.main()
