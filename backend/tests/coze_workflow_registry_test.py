"""Focused tests for Coze workflow registry service."""

import json
import shutil
import tempfile
from pathlib import Path

import pytest


class TestCozeWorkflowRegistryService:
    def test_empty_registry(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        with tempfile.TemporaryDirectory() as tmp_dir:
            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            contract = service.build_runtime_contract()
            assert contract["contract_version"] == "coze-workflow-registry-v1"
            assert contract["status"] == "empty"
            assert contract["total_workflows"] == 0
            assert contract["ready_workflows"] == 0
            assert contract["invalid_workflows"] == 0
            assert contract["workflows"] == []
            assert contract["errors"] == []

    def test_valid_manifest_is_discovered(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        with tempfile.TemporaryDirectory() as tmp_dir:
            workflow_dir = Path(tmp_dir) / "test_workflow"
            workflow_dir.mkdir()
            (workflow_dir / "prompts").mkdir()
            (workflow_dir / "examples").mkdir()

            manifest_content = """
id: test_workflow
name: Test Workflow
version: 0.1.0
status: draft
owner:
  team: test-team
  primary: test@example.com
  reviewers:
    - reviewer@example.com
source:
  platform: coze
  workspace: test-workspace
  workflow_id: "12345"
  workflow_name: Test
entrypoint:
  mode: local
  adapter: none
inputs:
  schema:
    type: object
    required:
      - input
    properties:
      input:
        type: string
outputs:
  schema:
    type: object
    properties:
      result:
        type: string
prompts:
  system: prompts/system.md
  task: prompts/task.md
dependencies:
  tools: []
  mcp_capabilities: []
  skills: []
  providers: []
  knowledge_sources: []
governance:
  permission_level: low
  trace_required: true
  approval_required: false
  data_sensitivity: internal
acceptance:
  examples: []
metadata:
  tags:
    - test
"""
            (workflow_dir / "workflow.yaml").write_text(manifest_content, encoding="utf-8")
            (workflow_dir / "prompts" / "system.md").write_text("System prompt", encoding="utf-8")
            (workflow_dir / "prompts" / "task.md").write_text("Task prompt", encoding="utf-8")

            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            contract = service.build_runtime_contract()

            assert contract["status"] == "ready"
            assert contract["total_workflows"] == 1
            assert contract["ready_workflows"] == 0
            assert contract["invalid_workflows"] == 0

            workflow = contract["workflows"][0]
            assert workflow["id"] == "test_workflow"
            assert workflow["name"] == "Test Workflow"
            assert workflow["version"] == "0.1.0"
            assert workflow["status"] == "draft"
            assert workflow["capability_id"] == "coze.workflow.test_workflow"
            assert workflow["readiness"]["status"] == "draft"
            assert workflow["prompts"]["system"]["exists"] is True
            assert workflow["prompts"]["task"]["exists"] is True

    def test_missing_required_field_fails_closed(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        with tempfile.TemporaryDirectory() as tmp_dir:
            workflow_dir = Path(tmp_dir) / "invalid_workflow"
            workflow_dir.mkdir()

            manifest_content = """
id: invalid_workflow
name: Invalid Workflow
version: 0.1.0
status: draft
"""
            (workflow_dir / "workflow.yaml").write_text(manifest_content, encoding="utf-8")

            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            contract = service.build_runtime_contract()

            assert contract["status"] == "degraded"
            assert contract["invalid_workflows"] == 1

            error = contract["errors"][0]
            assert error["status"] == "invalid"
            assert "Missing required fields" in error["message"]
            assert "owner" in error["message"]

    def test_missing_prompt_file_reported(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        with tempfile.TemporaryDirectory() as tmp_dir:
            workflow_dir = Path(tmp_dir) / "missing_prompt_workflow"
            workflow_dir.mkdir()
            (workflow_dir / "prompts").mkdir()

            manifest_content = """
id: missing_prompt_workflow
name: Missing Prompt Workflow
version: 0.1.0
status: draft
owner:
  team: test-team
  primary: test@example.com
source:
  platform: coze
  workspace: test-workspace
entrypoint:
  mode: local
  adapter: none
inputs:
  schema:
    type: object
    required:
      - input
    properties:
      input:
        type: string
outputs:
  schema:
    type: object
    properties:
      result:
        type: string
prompts:
  system: prompts/system.md
  task: prompts/task.md
dependencies:
  tools: []
  mcp_capabilities: []
  skills: []
  providers: []
  knowledge_sources: []
governance:
  permission_level: low
  trace_required: true
  approval_required: false
  data_sensitivity: internal
acceptance:
  examples: []
metadata:
  tags:
    - test
"""
            (workflow_dir / "workflow.yaml").write_text(manifest_content, encoding="utf-8")
            (workflow_dir / "prompts" / "system.md").write_text("System prompt", encoding="utf-8")

            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            contract = service.build_runtime_contract()

            workflow = contract["workflows"][0]
            assert workflow["prompts"]["system"]["exists"] is True
            assert workflow["prompts"]["task"]["exists"] is False
            assert "missing_prompt_task" in workflow["readiness"]["blockers"]

    def test_hazardous_project_list_recognition_exists(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        service = CozeWorkflowRegistryService()
        contract = service.build_runtime_contract()

        workflows = {w["id"]: w for w in contract["workflows"]}
        assert "hazardous_project_list_recognition" in workflows

        workflow = workflows["hazardous_project_list_recognition"]
        assert workflow["name"] == "Hazardous Project List Recognition"
        assert workflow["version"] == "0.1.0"
        assert workflow["status"] == "active"
        assert workflow["capability_id"] == "coze.workflow.hazardous_project_list_recognition"

        assert workflow["prompts"]["system"]["exists"] is True
        assert workflow["prompts"]["task"]["exists"] is True

    def test_szzg_agent_encapsulation_route_is_discovered_as_draft(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        service = CozeWorkflowRegistryService()
        contract = service.build_runtime_contract()

        workflows = {w["id"]: w for w in contract["workflows"]}
        assert "szzg_agent_encapsulation_route" in workflows

        workflow = workflows["szzg_agent_encapsulation_route"]
        assert workflow["name"] == "SZZG Agent Encapsulation Route"
        assert workflow["version"] == "0.1.0"
        assert workflow["status"] == "active"
        assert workflow["capability_id"] == "coze.workflow.szzg_agent_encapsulation_route"
        assert workflow["readiness"]["status"] == "ready"
        assert workflow["prompts"]["system"]["exists"] is True
        assert workflow["prompts"]["task"]["exists"] is True
        assert len(workflow["acceptance"]["examples"]) == 4

        examples = workflow["acceptance"]["examples"]
        assert [item["id"] for item in examples] == [
            "route_agent_single_match",
            "route_square_collect",
            "clarify_multi_match",
            "clarify_none_match",
        ]
        assert all(item["path_exists"] is True for item in examples)
        assert all(item["expected_exists"] is True for item in examples)

    def test_get_workflow_by_id(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        service = CozeWorkflowRegistryService()
        workflow = service.get_workflow_by_id("hazardous_project_list_recognition")
        assert workflow is not None
        assert workflow["id"] == "hazardous_project_list_recognition"

        not_found = service.get_workflow_by_id("non_existent_workflow")
        assert not_found is None

    def test_hidden_directory_ignored(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        with tempfile.TemporaryDirectory() as tmp_dir:
            hidden_dir = Path(tmp_dir) / "_template"
            hidden_dir.mkdir()
            (hidden_dir / "workflow.yaml").write_text(
                "id: template_workflow\nname: Template\nversion: 0.1.0\nstatus: draft\nowner:\n  team: test\n  primary: test@example.com",
                encoding="utf-8",
            )

            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            contract = service.build_runtime_contract()

            assert contract["total_workflows"] == 0
            assert contract["status"] == "empty"

    def test_invalid_status_detected(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        with tempfile.TemporaryDirectory() as tmp_dir:
            workflow_dir = Path(tmp_dir) / "invalid_status_workflow"
            workflow_dir.mkdir()

            manifest_content = """
id: invalid_status_workflow
name: Invalid Status Workflow
version: 0.1.0
status: invalid_status
owner:
  team: test-team
  primary: test@example.com
source:
  platform: coze
  workspace: test-workspace
entrypoint:
  mode: local
  adapter: none
inputs:
  schema:
    type: object
    required:
      - input
    properties:
      input:
        type: string
outputs:
  schema:
    type: object
    properties:
      result:
        type: string
prompts:
  system: prompts/system.md
dependencies:
  tools: []
governance:
  permission_level: low
acceptance:
  examples: []
"""
            (workflow_dir / "workflow.yaml").write_text(manifest_content, encoding="utf-8")
            (workflow_dir / "prompts").mkdir()
            (workflow_dir / "prompts" / "system.md").write_text("System", encoding="utf-8")

            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            contract = service.build_runtime_contract()

            workflow = contract["workflows"][0]
            assert workflow["readiness"]["status"] == "blocked"
            assert "invalid_status" in workflow["readiness"]["blockers"]

    def test_expected_json_can_be_loaded(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        service = CozeWorkflowRegistryService()
        workflow = service.get_workflow_by_id("hazardous_project_list_recognition")
        assert workflow is not None

        expected_path = Path(workflow["workflow_dir"]) / "examples" / "hazardous_project_list_expected.json"
        assert expected_path.exists()

        with open(expected_path, "r", encoding="utf-8") as f:
            expected = json.load(f)

        assert isinstance(expected, dict)
        assert "code" in expected
        assert "msg" in expected
        assert "data" in expected
        assert isinstance(expected["data"], list)

    def test_ready_workflow_exposes_capability_and_invocation(self):
        from backend.capability_runtime.registry import CapabilityRegistry
        from backend.capability_runtime.service import CapabilityRuntimeService
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        repo_root = Path(__file__).resolve().parents[2]
        source_dir = repo_root / "backend" / "coze_workflows" / "hazardous_project_list_recognition"
        sample_xlsx = source_dir / "examples" / "hazardous_project_list_sample.xlsx"

        with tempfile.TemporaryDirectory() as tmp_dir:
            workflow_dir = Path(tmp_dir) / "hazardous_project_list_recognition"
            (workflow_dir / "prompts").mkdir(parents=True)
            (workflow_dir / "examples").mkdir(parents=True)

            manifest_text = (source_dir / "workflow.yaml").read_text(encoding="utf-8").replace("status: review", "status: active")
            (workflow_dir / "workflow.yaml").write_text(manifest_text, encoding="utf-8")
            shutil.copy2(source_dir / "prompts" / "system.md", workflow_dir / "prompts" / "system.md")
            shutil.copy2(source_dir / "prompts" / "task.md", workflow_dir / "prompts" / "task.md")
            shutil.copy2(source_dir / "examples" / "hazardous_project_list_sample.xlsx", workflow_dir / "examples" / "hazardous_project_list_sample.xlsx")
            shutil.copy2(source_dir / "examples" / "hazardous_project_list_expected.json", workflow_dir / "examples" / "hazardous_project_list_expected.json")

            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            capability_runtime = CapabilityRuntimeService(CapabilityRegistry(service.build_capability_definitions()))
            capability_ids = {item["capability_id"] for item in capability_runtime.list_capabilities()["capabilities"]}

            assert "coze.workflow.hazardous_project_list_recognition" in capability_ids

            response = capability_runtime.invoke(
                "coze.workflow.hazardous_project_list_recognition",
                {
                    "file": {
                        "filename": sample_xlsx.name,
                        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "content_ref": str(sample_xlsx),
                    }
                },
            )

            assert response["ok"] is True
            assert response["result"]["code"] == 200
            assert len(response["result"]["data"]) == 14
            assert response["result"]["data"][12]["name"] == "预应力小箱梁架设（履带吊）"

    def test_missing_runtime_dependency_blocks_invocation(self):
        from backend.services.coze_workflow_registry_service import CozeWorkflowRegistryService

        repo_root = Path(__file__).resolve().parents[2]
        source_dir = repo_root / "backend" / "coze_workflows" / "hazardous_project_list_recognition"
        sample_xlsx = source_dir / "examples" / "hazardous_project_list_sample.xlsx"

        with tempfile.TemporaryDirectory() as tmp_dir:
            workflow_dir = Path(tmp_dir) / "blocked_hazardous_workflow"
            (workflow_dir / "prompts").mkdir(parents=True)
            (workflow_dir / "examples").mkdir(parents=True)

            manifest_text = (source_dir / "workflow.yaml").read_text(encoding="utf-8")
            manifest_text = manifest_text.replace("id: hazardous_project_list_recognition", "id: blocked_hazardous_workflow")
            manifest_text = manifest_text.replace("status: review", "status: active")
            manifest_text = manifest_text.replace("    - json_schema.validate", "    - json_schema.validate\n    - missing.capability")
            (workflow_dir / "workflow.yaml").write_text(manifest_text, encoding="utf-8")
            shutil.copy2(source_dir / "prompts" / "system.md", workflow_dir / "prompts" / "system.md")
            shutil.copy2(source_dir / "prompts" / "task.md", workflow_dir / "prompts" / "task.md")
            shutil.copy2(source_dir / "examples" / "hazardous_project_list_sample.xlsx", workflow_dir / "examples" / "hazardous_project_list_sample.xlsx")
            shutil.copy2(source_dir / "examples" / "hazardous_project_list_expected.json", workflow_dir / "examples" / "hazardous_project_list_expected.json")

            service = CozeWorkflowRegistryService(root_path=tmp_dir)
            response = service.invoke_workflow(
                "blocked_hazardous_workflow",
                {
                    "file": {
                        "filename": sample_xlsx.name,
                        "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "content_ref": str(sample_xlsx),
                    }
                },
            )

            assert response["ok"] is False
            assert response["error"]["code"] == "COZE_WORKFLOW_DEPENDENCY_UNAVAILABLE"
            assert "missing_runtime_capabilities:missing.capability" in response["error"]["blockers"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
