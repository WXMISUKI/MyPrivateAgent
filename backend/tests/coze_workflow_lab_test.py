"""Focused tests for Coze workflow lab read contracts."""

import json
import tempfile
from pathlib import Path


class _FakeRegistryService:
    def __init__(self, workflows):
        self.workflows = workflows

    def build_runtime_contract(self):
        return {
            "status": "ready",
            "ready_workflows": len(self.workflows),
            "invalid_workflows": 0,
            "workflows": self.workflows,
            "errors": [],
        }

    def get_workflow_by_id(self, workflow_id):
        for workflow in self.workflows:
            if workflow.get("id") == workflow_id:
                return workflow
        return None


class _FakeCapabilityService:
    def __init__(self, response):
        self.response = response
        self.invocations = []

    def invoke(self, capability_id, payload):
        self.invocations.append({"capability_id": capability_id, "payload": payload})
        return self.response


def _workflow_fixture(**overrides):
    workflow = {
        "id": "dependency_probe",
        "name": "Dependency Probe",
        "version": "0.1.0",
        "status": "active",
        "capability_id": "coze.workflow.dependency_probe",
        "owner": {"primary": "owner@example.com"},
        "readiness": {"status": "ready", "reason": "fixture", "blockers": []},
        "inputs": {"schema": {"type": "object", "properties": {}}},
        "outputs": {"schema": {"type": "object"}},
        "prompts": {},
        "acceptance": {"examples": [], "smoke": {}},
        "governance": {},
        "metadata": {},
        "source": {"unsupported_nodes": []},
        "dependencies": {
            "tools": [],
            "mcp_capabilities": [],
            "skills": [],
            "providers": [],
            "runtime_capabilities": [],
        },
        "workflow_dir": "",
        "manifest_path": "",
    }
    workflow.update(overrides)
    return workflow


class TestCozeWorkflowLabService:
    def test_lab_lists_registered_workflows_with_launch_evidence(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        service = CozeWorkflowLabService()
        contract = service.list_workflows()

        assert contract["contract_version"] == "coze-workflow-lab-v1"
        workflows = {item["workflow_id"]: item for item in contract["workflows"]}
        assert "hazardous_project_list_recognition" in workflows
        assert "szzg_agent_encapsulation_route" in workflows

        route_workflow = workflows["szzg_agent_encapsulation_route"]
        assert route_workflow["status"] == "active"
        assert route_workflow["readiness"]["status"] == "ready"
        assert route_workflow["capability_id"] == "coze.workflow.szzg_agent_encapsulation_route"
        assert route_workflow["launch_evidence"]["status"] == "present"
        assert route_workflow["launch_evidence"]["decision"] == "go"

    def test_lab_detail_contains_schemas_examples_and_governance(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        service = CozeWorkflowLabService()
        detail = service.get_workflow_detail("szzg_agent_encapsulation_route")

        assert detail is not None
        assert detail["contract_version"] == "coze-workflow-lab-v1"
        assert detail["workflow_id"] == "szzg_agent_encapsulation_route"
        assert detail["input_schema"]["required"] == ["user_input"]
        assert "command" in detail["output_schema"]["required"]
        assert detail["prompts"]["system"]["exists"] is True
        assert detail["governance"]["trace_required"] is True
        assert len(detail["acceptance"]["examples"]) == 4
        assert detail["dependency_mapping"]["status"] == "ready"
        items = detail["dependency_mapping"]["items"]
        http_dependency = next(
            item for item in items if item["kind"] == "runtime_capability" and item["source"] == "http.request"
        )
        assert http_dependency["status"] == "ready"
        http_node = next(item for item in items if item["kind"] == "coze_node")
        assert http_node["target_capability_id"] == "http.request"
        assert http_node["status"] == "mapped"

    def test_lab_loads_acceptance_example_payloads(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        service = CozeWorkflowLabService()
        example = service.load_example("szzg_agent_encapsulation_route", "route_agent_single_match")

        assert example is not None
        assert example["contract_version"] == "coze-workflow-lab-v1"
        assert example["workflow_id"] == "szzg_agent_encapsulation_route"
        assert example["example_id"] == "route_agent_single_match"
        assert example["input"]["error"] is None
        assert example["input"]["payload"]["user_input"] == "打开代码调试助手"
        assert example["expected"]["error"] is None
        assert example["expected"]["payload"]["command"] == "route_agent"

    def test_lab_missing_example_returns_none(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        service = CozeWorkflowLabService()
        assert service.load_example("szzg_agent_encapsulation_route", "missing") is None

    def test_launch_evidence_paths_are_repo_relative(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        service = CozeWorkflowLabService()
        detail = service.get_workflow_detail("hazardous_project_list_recognition")

        assert detail is not None
        evidence_path = detail["launch_evidence"]["path"]
        assert evidence_path is not None
        assert not Path(evidence_path).is_absolute()

    def test_dependency_mapping_blocks_unknown_runtime_capability(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        workflow = _workflow_fixture(
            dependencies={
                "tools": [],
                "mcp_capabilities": [],
                "skills": [],
                "providers": [],
                "runtime_capabilities": ["unknown.ocr.magic"],
            }
        )
        service = CozeWorkflowLabService(registry_service=_FakeRegistryService([workflow]))
        detail = service.get_workflow_detail("dependency_probe")

        assert detail is not None
        mapping = detail["dependency_mapping"]
        assert mapping["status"] == "blocked"
        assert mapping["blockers"] == ["missing_runtime_capability:unknown.ocr.magic"]
        item = mapping["items"][0]
        assert item["kind"] == "runtime_capability"
        assert item["status"] == "blocked"

    def test_dependency_mapping_links_provider_backed_runtime_capability(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        workflow = _workflow_fixture(
            dependencies={
                "tools": [],
                "mcp_capabilities": [],
                "skills": [],
                "providers": [],
                "runtime_capabilities": ["document.ocr.extract"],
            }
        )
        service = CozeWorkflowLabService(registry_service=_FakeRegistryService([workflow]))
        detail = service.get_workflow_detail("dependency_probe")

        assert detail is not None
        item = detail["dependency_mapping"]["items"][0]
        assert item["target_capability_id"] == "document.ocr.extract"
        assert item["provider_id"] == "paddleOCRProvider"
        assert item["onboarding_id"] == "document-ocr-provider"
        assert item["onboarding_path"] == "/api/provider-onboarding/document-ocr-provider"
        assert item["service_provider_detail_path"] == "/api/service-providers/paddleOCRProvider"
        assert item["service_provider_evidence_preview_path"] == "/api/service-providers/paddleOCRProvider/evidence-preview"
        assert item["provider_readiness"]["configuration_status"] in {"configured", "unconfigured"}
        assert item["default_chat_behavior"] == "not_changed"

    def test_dependency_mapping_links_declared_provider_to_onboarding(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        workflow = _workflow_fixture(
            dependencies={
                "tools": [],
                "mcp_capabilities": [],
                "skills": [],
                "providers": ["unifiedKnowledgeProvider"],
                "runtime_capabilities": [],
            }
        )
        service = CozeWorkflowLabService(registry_service=_FakeRegistryService([workflow]))
        detail = service.get_workflow_detail("dependency_probe")

        assert detail is not None
        item = detail["dependency_mapping"]["items"][0]
        assert item["kind"] == "provider"
        assert item["provider_id"] == "unifiedKnowledgeProvider"
        assert item["onboarding_id"] == "knowledge-rag-provider"
        assert item["onboarding_path"] == "/api/provider-onboarding/knowledge-rag-provider"
        assert item["provider_readiness"]["recommended_action"] in {
            "configure_required_provider_environment",
            "run_live_service_provider_probe",
        }

    def test_dependency_mapping_reports_file_artifact_contract(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        detail = CozeWorkflowLabService().get_workflow_detail("hazardous_project_list_recognition")

        assert detail is not None
        artifact_item = next(
            item for item in detail["dependency_mapping"]["items"] if item["kind"] == "artifact_input"
        )
        assert artifact_item["source"] == "inputs.file"
        assert "content_ref" in artifact_item["accepted_reference_types"]
        assert "artifact_id" in artifact_item["accepted_reference_types"]
        assert artifact_item["artifact_flow"]["local_fixture"] == "allowed_for_lab_only"

    def test_dependency_mapping_blocks_unknown_coze_node(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        workflow = _workflow_fixture(source={"unsupported_nodes": ["MagicImagePlugin"]})
        service = CozeWorkflowLabService(registry_service=_FakeRegistryService([workflow]))
        detail = service.get_workflow_detail("dependency_probe")

        assert detail is not None
        mapping = detail["dependency_mapping"]
        assert mapping["status"] == "blocked"
        assert mapping["blockers"] == ["unsupported_coze_node:MagicImagePlugin"]

    def test_lab_replays_example_through_capability_runtime_and_matches_expected(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        service = CozeWorkflowLabService()
        replay = service.invoke_example("szzg_agent_encapsulation_route", "route_agent_single_match")

        assert replay is not None
        assert replay["status"] == "completed"
        assert replay["capability_id"] == "coze.workflow.szzg_agent_encapsulation_route"
        assert replay["result"]["command"] == "route_agent"
        assert replay["expected_comparison"]["status"] == "match"
        assert replay["trace_summary"]["delegated_to_capability_runtime"] is True
        assert replay["trace_summary"]["workflow_version"] == "0.1.0"

    def test_lab_replay_reports_mismatch_diff(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        with tempfile.TemporaryDirectory() as tmp_dir:
            workflow_dir = Path(tmp_dir) / "mismatch_probe"
            (workflow_dir / "examples").mkdir(parents=True)
            (workflow_dir / "examples" / "demo.json").write_text(
                json.dumps({"user_input": "打开代码调试助手"}, ensure_ascii=False),
                encoding="utf-8",
            )
            (workflow_dir / "examples" / "demo_expected.json").write_text(
                json.dumps(
                    {
                        "command": "route_agent",
                        "params": ["ROUTE://agent_detail?id=7"],
                        "message": "ok",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            workflow = _workflow_fixture(
                id="mismatch_probe",
                capability_id="coze.workflow.mismatch_probe",
                workflow_dir=str(workflow_dir),
                acceptance={
                    "examples": [
                        {
                            "id": "demo",
                            "path": "examples/demo.json",
                            "path_exists": True,
                            "expected_path": "examples/demo_expected.json",
                            "expected_exists": True,
                            "required": True,
                        }
                    ],
                    "smoke": {},
                },
            )
            registry = _FakeRegistryService([workflow])
            capability = _FakeCapabilityService(
                {
                    "ok": True,
                    "capability_id": "coze.workflow.mismatch_probe",
                    "run_id": "run_fake",
                    "result": {"command": "clarify_none", "params": [], "message": "wrong"},
                    "trace": {"workflow_id": "mismatch_probe", "workflow_version": "0.1.0"},
                }
            )
            service = CozeWorkflowLabService(registry_service=registry, capability_service=capability)

            replay = service.invoke_example("mismatch_probe", "demo")

            assert replay is not None
            assert replay["status"] == "completed"
            assert replay["expected_comparison"]["status"] == "mismatch"
            assert any(item["path"] == "$.command" for item in replay["expected_comparison"]["diff"])
            assert capability.invocations == [
                {
                    "capability_id": "coze.workflow.mismatch_probe",
                    "payload": {"user_input": "打开代码调试助手"},
                }
            ]

    def test_lab_replay_blocks_non_ready_workflow_without_invocation(self):
        from backend.services.coze_workflow_lab_service import CozeWorkflowLabService

        workflow = _workflow_fixture(
            id="blocked_probe",
            readiness={
                "status": "review",
                "reason": "Workflow is under review",
                "blockers": ["manual_review_required"],
            },
        )
        workflow["acceptance"] = {
            "examples": [
                {
                    "id": "demo",
                    "path": "examples/demo.json",
                    "path_exists": True,
                    "expected_path": "examples/demo_expected.json",
                    "expected_exists": True,
                    "required": True,
                }
            ],
            "smoke": {},
        }
        capability = _FakeCapabilityService({"ok": True, "result": {"ok": True}})
        service = CozeWorkflowLabService(
            registry_service=_FakeRegistryService([workflow]),
            capability_service=capability,
        )
        replay = service.invoke_example("blocked_probe", "demo")

        assert replay is not None
        assert replay["status"] == "blocked"
        assert replay["error"]["code"] == "COZE_WORKFLOW_LAB_REPLAY_BLOCKED"
        assert replay["error"]["blockers"] == ["manual_review_required"]
        assert replay["trace_summary"]["delegated_to_capability_runtime"] is False
        assert capability.invocations == []
