"""Read-only lab contracts for migrated Coze workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping

try:
    from capability_runtime.service import CapabilityRuntimeService, get_capability_runtime_service
    from capability_runtime.provider_onboarding_catalog import get_provider_onboarding_catalog_service
    from services.coze_workflow_registry_service import (
        CozeWorkflowRegistryService,
        get_coze_workflow_registry_service,
    )
    from services.coze_workflow_dependency_mapper import build_dependency_contract
except ModuleNotFoundError:
    from backend.capability_runtime.service import CapabilityRuntimeService, get_capability_runtime_service
    from backend.capability_runtime.provider_onboarding_catalog import get_provider_onboarding_catalog_service
    from backend.services.coze_workflow_registry_service import (
        CozeWorkflowRegistryService,
        get_coze_workflow_registry_service,
    )
    from backend.services.coze_workflow_dependency_mapper import build_dependency_contract


CONTRACT_VERSION = "coze-workflow-lab-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_DOCS_ROOT = REPO_ROOT / "docs" / "integration"

SUPPORTED_RUNTIME_CAPABILITIES = {
    "document.file_type.detect",
    "http.request",
    "spreadsheet.table.extract",
    "llm.structured_json.generate",
    "json_schema.validate",
}

PROVIDER_BACKED_CAPABILITIES = {
    "document.ocr.extract": {
        "provider_id": "paddleOCRProvider",
        "onboarding_id": "document-ocr-provider",
        "onboarding_path": "/api/provider-onboarding/document-ocr-provider",
    },
    "document.layout.parse": {
        "provider_id": "paddleLayoutProvider",
        "onboarding_id": "document-layout-provider",
        "onboarding_path": "/api/provider-onboarding/document-layout-provider",
    },
    "document.vlm.parse": {
        "provider_id": "documentVlmProvider",
        "onboarding_id": "document-vlm-provider",
        "onboarding_path": "/api/provider-onboarding/document-vlm-provider",
    },
    "knowledge.rag.retrieve": {
        "provider_id": "unifiedKnowledgeProvider",
        "onboarding_id": "knowledge-rag-provider",
        "onboarding_path": "/api/provider-onboarding/knowledge-rag-provider",
    },
    "knowledge.graph.query": {
        "provider_id": "unifiedKnowledgeProvider",
        "onboarding_id": "knowledge-rag-provider",
        "onboarding_path": "/api/provider-onboarding/knowledge-rag-provider",
    },
    "voice.asr.vosk": {
        "provider_id": "unifiedTTSandASR",
        "onboarding_id": "voice-asr-tts-provider",
        "onboarding_path": "/api/provider-onboarding/voice-asr-tts-provider",
    },
    "voice.tts.edge": {
        "provider_id": "unifiedTTSandASR",
        "onboarding_id": "voice-asr-tts-provider",
        "onboarding_path": "/api/provider-onboarding/voice-asr-tts-provider",
    },
}

NODE_CAPABILITY_HINTS = {
    "http": "http.request",
    "http request": "http.request",
    "HTTP 请求": "http.request",
    "LinkReaderPlugin": "spreadsheet.table.extract",
    "get_file_type": "document.file_type.detect",
    "ocr": "document.ocr.extract",
    "vlm": "document.vlm.parse",
    "rag": "knowledge.rag.retrieve",
}


class CozeWorkflowLabService:
    """Assemble workflow lab read models without invoking workflows."""

    def __init__(
        self,
        registry_service: CozeWorkflowRegistryService | None = None,
        capability_service: CapabilityRuntimeService | None = None,
    ):
        self.registry_service = registry_service or get_coze_workflow_registry_service()
        self.capability_service = capability_service or get_capability_runtime_service()

    def list_workflows(self) -> Dict[str, Any]:
        contract = self.registry_service.build_runtime_contract()
        workflows = [
            self._build_summary(workflow)
            for workflow in contract.get("workflows", [])
            if isinstance(workflow, Mapping)
        ]
        return {
            "contract_version": CONTRACT_VERSION,
            "status": contract.get("status"),
            "total_workflows": len(workflows),
            "ready_workflows": contract.get("ready_workflows", 0),
            "invalid_workflows": contract.get("invalid_workflows", 0),
            "workflows": workflows,
            "errors": list(contract.get("errors") or []),
        }

    def get_workflow_detail(self, workflow_id: str) -> Dict[str, Any] | None:
        workflow = self.registry_service.get_workflow_by_id(workflow_id)
        if workflow is None:
            return None
        return self._build_detail(workflow)

    def load_example(self, workflow_id: str, example_id: str) -> Dict[str, Any] | None:
        workflow = self.registry_service.get_workflow_by_id(workflow_id)
        if workflow is None:
            return None
        workflow_dir = Path(str(workflow.get("workflow_dir") or ""))
        for example in self._acceptance_examples(workflow):
            if str(example.get("id") or "") != example_id:
                continue
            input_payload = self._read_json_file(workflow_dir / str(example.get("path") or ""))
            expected_output = self._read_json_file(workflow_dir / str(example.get("expected_path") or ""))
            return {
                "contract_version": CONTRACT_VERSION,
                "workflow_id": workflow_id,
                "example_id": example_id,
                "input": {
                    "path": example.get("path"),
                    "exists": bool(example.get("path_exists")),
                    "payload": input_payload.get("payload"),
                    "error": input_payload.get("error"),
                },
                "expected": {
                    "path": example.get("expected_path"),
                    "exists": bool(example.get("expected_exists")),
                    "payload": expected_output.get("payload"),
                    "error": expected_output.get("error"),
                },
            }
        return None

    def invoke_example(self, workflow_id: str, example_id: str) -> Dict[str, Any] | None:
        workflow = self.registry_service.get_workflow_by_id(workflow_id)
        if workflow is None:
            return None

        example = self.load_example(workflow_id, example_id)
        if example is None:
            return None

        readiness = dict(workflow.get("readiness") or {})
        if readiness.get("status") != "ready":
            return self._blocked_example_replay(
                workflow=workflow,
                example_id=example_id,
                blockers=list(readiness.get("blockers") or []),
                reason=str(readiness.get("reason") or "Workflow is not ready for lab replay."),
            )

        input_error = example.get("input", {}).get("error")
        if input_error:
            return self._blocked_example_replay(
                workflow=workflow,
                example_id=example_id,
                blockers=[f"example_input_unavailable:{input_error}"],
                reason="Acceptance example input could not be loaded.",
            )

        payload = example.get("input", {}).get("payload")
        if not isinstance(payload, Mapping):
            return self._blocked_example_replay(
                workflow=workflow,
                example_id=example_id,
                blockers=["example_input_not_object"],
                reason="Acceptance example input must be a JSON object.",
            )

        capability_id = str(workflow.get("capability_id") or f"coze.workflow.{workflow_id}")
        try:
            invocation = self.capability_service.invoke(capability_id, dict(payload))
        except LookupError:
            invocation = {
                "ok": False,
                "capability_id": capability_id,
                "error": {
                    "code": "CAPABILITY_NOT_FOUND",
                    "message": f"Capability not found: {capability_id}",
                    "blockers": [f"missing_capability:{capability_id}"],
                },
            }

        actual = invocation.get("result") if invocation.get("ok") else None
        expected = example.get("expected", {}).get("payload")
        comparison = self._compare_expected_output(actual, expected, expected_error=example.get("expected", {}).get("error"))
        return {
            "contract_version": CONTRACT_VERSION,
            "workflow_id": workflow_id,
            "capability_id": capability_id,
            "example_id": example_id,
            "status": "completed" if invocation.get("ok") else "blocked",
            "run_id": invocation.get("run_id"),
            "result": actual,
            "error": invocation.get("error"),
            "trace_summary": self._trace_summary(invocation, workflow),
            "expected_comparison": comparison,
        }

    def _build_summary(self, workflow: Mapping[str, Any]) -> Dict[str, Any]:
        readiness = dict(workflow.get("readiness") or {})
        evidence = self._find_launch_evidence(workflow)
        return {
            "workflow_id": str(workflow.get("id") or ""),
            "name": str(workflow.get("name") or ""),
            "version": str(workflow.get("version") or ""),
            "status": str(workflow.get("status") or ""),
            "capability_id": str(workflow.get("capability_id") or ""),
            "readiness": {
                "status": str(readiness.get("status") or "unknown"),
                "reason": str(readiness.get("reason") or ""),
                "blockers": list(readiness.get("blockers") or []),
            },
            "owner": dict(workflow.get("owner") or {}),
            "launch_evidence": evidence,
        }

    def _build_detail(self, workflow: Mapping[str, Any]) -> Dict[str, Any]:
        summary = self._build_summary(workflow)
        dependency_contract = build_dependency_contract(workflow)
        return {
            "contract_version": CONTRACT_VERSION,
            **summary,
            "input_schema": dict(workflow.get("inputs", {}).get("schema") or {}),
            "output_schema": dict(workflow.get("outputs", {}).get("schema") or {}),
            "prompts": dict(workflow.get("prompts") or {}),
            "acceptance": {
                "examples": self._acceptance_examples(workflow),
                "smoke": dict(workflow.get("acceptance", {}).get("smoke") or {}),
            },
            "governance": dict(workflow.get("governance") or {}),
            "metadata": dict(workflow.get("metadata") or {}),
            "source": dict(workflow.get("source") or {}),
            "asset_paths": {
                "workflow_dir": workflow.get("workflow_dir"),
                "manifest_path": workflow.get("manifest_path"),
            },
            "dependency_summary": dependency_contract["summary"],
            "dependency_mapping": dependency_contract["mapping"],
            "dependency_blockers": list(dependency_contract["blockers"] or []),
        }

    def _blocked_example_replay(
        self,
        *,
        workflow: Mapping[str, Any],
        example_id: str,
        blockers: List[str],
        reason: str,
    ) -> Dict[str, Any]:
        workflow_id = str(workflow.get("id") or "")
        capability_id = str(workflow.get("capability_id") or f"coze.workflow.{workflow_id}")
        return {
            "contract_version": CONTRACT_VERSION,
            "workflow_id": workflow_id,
            "capability_id": capability_id,
            "example_id": example_id,
            "status": "blocked",
            "run_id": None,
            "result": None,
            "error": {
                "code": "COZE_WORKFLOW_LAB_REPLAY_BLOCKED",
                "message": reason,
                "blockers": blockers,
            },
            "trace_summary": {
                "workflow_id": workflow_id,
                "workflow_version": str(workflow.get("version") or ""),
                "source": "coze_workflow_lab",
                "delegated_to_capability_runtime": False,
            },
            "expected_comparison": {
                "status": "not_compared",
                "reason": "Replay was blocked before invocation.",
                "diff": [],
            },
        }

    def _compare_expected_output(
        self,
        actual: Any,
        expected: Any,
        *,
        expected_error: Any = None,
    ) -> Dict[str, Any]:
        if expected_error:
            return {
                "status": "not_compared",
                "reason": f"Expected output could not be loaded: {expected_error}",
                "diff": [],
            }
        diff = self._diff_json(actual, expected)
        if not diff:
            return {
                "status": "match",
                "reason": "Actual result matches expected output.",
                "diff": [],
            }
        return {
            "status": "mismatch",
            "reason": "Actual result differs from expected output.",
            "diff": diff[:10],
            "diff_truncated": len(diff) > 10,
        }

    def _diff_json(self, actual: Any, expected: Any, path: str = "$") -> List[Dict[str, Any]]:
        if type(actual) is not type(expected):
            return [
                {
                    "path": path,
                    "reason": "type_mismatch",
                    "actual": actual,
                    "expected": expected,
                }
            ]
        if isinstance(expected, Mapping):
            diff: List[Dict[str, Any]] = []
            actual_keys = set(actual.keys())
            expected_keys = set(expected.keys())
            for key in sorted(expected_keys - actual_keys):
                diff.append({"path": f"{path}.{key}", "reason": "missing_actual", "expected": expected[key]})
            for key in sorted(actual_keys - expected_keys):
                diff.append({"path": f"{path}.{key}", "reason": "unexpected_actual", "actual": actual[key]})
            for key in sorted(actual_keys & expected_keys):
                diff.extend(self._diff_json(actual[key], expected[key], f"{path}.{key}"))
            return diff
        if isinstance(expected, list):
            diff = []
            min_len = min(len(actual), len(expected))
            for index in range(min_len):
                diff.extend(self._diff_json(actual[index], expected[index], f"{path}[{index}]"))
            if len(actual) != len(expected):
                diff.append(
                    {
                        "path": path,
                        "reason": "length_mismatch",
                        "actual_length": len(actual),
                        "expected_length": len(expected),
                    }
                )
            return diff
        if actual != expected:
            return [
                {
                    "path": path,
                    "reason": "value_mismatch",
                    "actual": actual,
                    "expected": expected,
                }
            ]
        return []

    @staticmethod
    def _trace_summary(invocation: Mapping[str, Any], workflow: Mapping[str, Any]) -> Dict[str, Any]:
        trace = invocation.get("trace") if isinstance(invocation.get("trace"), Mapping) else {}
        return {
            "workflow_id": str(trace.get("workflow_id") or workflow.get("id") or ""),
            "workflow_version": str(trace.get("workflow_version") or workflow.get("version") or ""),
            "run_id": invocation.get("run_id"),
            "source": trace.get("source") or "capability_runtime",
            "delegated_to_capability_runtime": True,
            "dependency_summary": dict(trace.get("dependency_summary") or {}),
        }

    def _acceptance_examples(self, workflow: Mapping[str, Any]) -> List[Dict[str, Any]]:
        examples = workflow.get("acceptance", {}).get("examples") if isinstance(workflow.get("acceptance"), Mapping) else []
        return [dict(example) for example in examples or [] if isinstance(example, Mapping)]

    def _build_dependency_mapping(self, workflow: Mapping[str, Any]) -> Dict[str, Any]:
        return dict(build_dependency_contract(workflow)["mapping"])

    def _map_runtime_capabilities(self, dependencies: Mapping[str, Any]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for capability_id in self._string_list(dependencies.get("runtime_capabilities")):
            provider = PROVIDER_BACKED_CAPABILITIES.get(capability_id)
            supported = capability_id in SUPPORTED_RUNTIME_CAPABILITIES
            item = self._base_dependency_item(
                kind="runtime_capability",
                source=capability_id,
                target_capability_id=capability_id,
                status="ready" if supported else "blocked",
                blocker=None if supported else f"missing_runtime_capability:{capability_id}",
            )
            if provider is not None:
                provider_fields = self._provider_dependency_fields(capability_id, provider)
                item.update(provider_fields)
                provider_status = str(provider_fields.get("provider_readiness", {}).get("configuration_status") or "")
                item["status"] = "ready" if provider_status == "configured" else "blocked"
                item["blocker"] = (
                    None
                    if provider_status == "configured"
                    else f"provider_not_ready:{provider['provider_id']}:{capability_id}"
                )
            items.append(item)
        return items

    def _map_named_dependencies(self, kind: str, values: Any) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for value in self._string_list(values):
            item = self._base_dependency_item(
                kind=kind,
                source=value,
                target_capability_id=None,
                status="declared",
            )
            if kind == "provider":
                item["provider_id"] = value
                item.update(self._provider_fields_for_provider_id(value))
            items.append(item)
        return items

    def _map_unsupported_nodes(self, nodes: Any) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for node in self._string_list(nodes):
            target = self._capability_hint_for_node(node)
            supported = bool(target and target in SUPPORTED_RUNTIME_CAPABILITIES)
            provider = PROVIDER_BACKED_CAPABILITIES.get(str(target or ""))
            item = self._base_dependency_item(
                kind="coze_node",
                source=node,
                target_capability_id=target,
                status="mapped" if supported or provider is not None else "blocked",
                blocker=None if supported or provider is not None else f"unsupported_coze_node:{node}",
            )
            if provider is not None:
                item.update(self._provider_dependency_fields(str(target), provider))
                provider_status = str(item.get("provider_readiness", {}).get("configuration_status") or "")
                if provider_status != "configured":
                    item["status"] = "blocked"
                    item["blocker"] = f"provider_not_ready:{provider['provider_id']}:{target}"
            items.append(item)
        return items

    def _map_file_inputs(self, workflow: Mapping[str, Any]) -> List[Dict[str, Any]]:
        schema = workflow.get("inputs", {}).get("schema") if isinstance(workflow.get("inputs"), Mapping) else {}
        properties = schema.get("properties") if isinstance(schema, Mapping) else {}
        items: List[Dict[str, Any]] = []
        if isinstance(properties, Mapping) and "file" in properties:
            items.append(
                {
                    **self._base_dependency_item(
                        kind="artifact_input",
                        source="inputs.file",
                        target_capability_id=None,
                        status="declared",
                    ),
                    "accepted_reference_types": ["content_ref", "artifact_id", "runtime_file_ref"],
                    "external_invocation_note": "External callers should pass runtime-managed references, not local filesystem paths.",
                    "artifact_flow": {
                        "local_fixture": "allowed_for_lab_only",
                        "upload": "expected_before_invocation",
                        "artifact_id": "supported_contract_shape",
                        "provider_owned_job_ref": "supported_for_large_or_async_document_workflows",
                    },
                }
            )
        return items

    def _provider_dependency_fields(self, capability_id: str, provider: Mapping[str, str]) -> Dict[str, Any]:
        provider_id = str(provider.get("provider_id") or "")
        onboarding_id = str(provider.get("onboarding_id") or "")
        fields = {
            "provider_id": provider_id,
            "onboarding_id": onboarding_id,
            "onboarding_path": str(provider.get("onboarding_path") or ""),
            "service_provider_detail_path": f"/api/service-providers/{provider_id}",
            "service_provider_evidence_preview_path": f"/api/service-providers/{provider_id}/evidence-preview",
            "provider_readiness": self._provider_readiness(onboarding_id),
            "invocation_boundary": "explicit_capability_only",
            "default_chat_behavior": "not_changed",
        }
        fields["provider_readiness"]["capability_id"] = capability_id
        return fields

    def _provider_fields_for_provider_id(self, provider_id: str) -> Dict[str, Any]:
        onboarding_service = get_provider_onboarding_catalog_service()
        onboarding_id = onboarding_service.onboarding_id_for_provider(provider_id)
        if not onboarding_id:
            return {
                "provider_readiness": {
                    "configuration_status": "unknown",
                    "checks": [],
                    "recommended_action": "inspect_provider_registration",
                },
                "service_provider_detail_path": f"/api/service-providers/{provider_id}",
                "service_provider_evidence_preview_path": f"/api/service-providers/{provider_id}/evidence-preview",
                "default_chat_behavior": "not_changed",
            }
        return {
            "onboarding_id": onboarding_id,
            "onboarding_path": f"/api/provider-onboarding/{onboarding_id}",
            "service_provider_detail_path": f"/api/service-providers/{provider_id}",
            "service_provider_evidence_preview_path": f"/api/service-providers/{provider_id}/evidence-preview",
            "provider_readiness": self._provider_readiness(onboarding_id),
            "default_chat_behavior": "not_changed",
        }

    @staticmethod
    def _provider_readiness(onboarding_id: str) -> Dict[str, Any]:
        if not onboarding_id:
            return {
                "configuration_status": "unknown",
                "checks": [],
                "recommended_action": "inspect_provider_registration",
            }
        readiness = get_provider_onboarding_catalog_service().get_readiness(onboarding_id)
        return {
            "configuration_status": readiness.get("configuration_status"),
            "checks": list(readiness.get("checks") or []),
            "recommended_action": readiness.get("recommended_action"),
            "live_probe_hints": dict(readiness.get("live_probe_hints") or {}),
            "boundaries": dict(readiness.get("boundaries") or {}),
        }

    @staticmethod
    def _base_dependency_item(
        *,
        kind: str,
        source: str,
        target_capability_id: str | None,
        status: str,
        blocker: str | None = None,
    ) -> Dict[str, Any]:
        return {
            "kind": kind,
            "source": source,
            "target_capability_id": target_capability_id,
            "status": status,
            "provider_id": None,
            "onboarding_id": None,
            "onboarding_path": None,
            "service_provider_detail_path": None,
            "service_provider_evidence_preview_path": None,
            "blocker": blocker,
        }

    @staticmethod
    def _capability_hint_for_node(node: str) -> str | None:
        normalized = node.strip()
        lowered = normalized.lower()
        for key, capability_id in NODE_CAPABILITY_HINTS.items():
            if key in normalized or key.lower() in lowered:
                return capability_id
        return None

    @staticmethod
    def _string_list(values: Any) -> List[str]:
        if not isinstance(values, list):
            return []
        return [str(value).strip() for value in values if str(value).strip()]

    def _find_launch_evidence(self, workflow: Mapping[str, Any]) -> Dict[str, Any]:
        workflow_id = str(workflow.get("id") or "").strip()
        if not workflow_id or not INTEGRATION_DOCS_ROOT.exists():
            return {"status": "missing", "path": None, "decision": None}

        candidates = [
            workflow_id,
            workflow_id.replace("_", "-"),
            str(workflow.get("name") or "").strip().lower().replace(" ", "-"),
        ]
        for child in sorted(INTEGRATION_DOCS_ROOT.iterdir(), key=lambda item: item.name):
            if not child.is_dir():
                continue
            if not any(candidate and candidate in child.name for candidate in candidates):
                continue
            decision = self._read_launch_decision(child)
            return {
                "status": "present",
                "path": str(child.relative_to(REPO_ROOT)),
                "decision": decision,
            }
        return {"status": "missing", "path": None, "decision": None}

    def _read_launch_decision(self, evidence_dir: Path) -> str | None:
        for json_path in sorted(evidence_dir.glob("*.json")):
            payload = self._read_json_file(json_path).get("payload")
            if isinstance(payload, Mapping):
                decision = payload.get("decision")
                if decision:
                    return str(decision)
        return None

    def _read_json_file(self, path: Path) -> Dict[str, Any]:
        if not path.exists() or not path.is_file():
            return {"payload": None, "error": "file_not_found"}
        try:
            return {"payload": json.loads(path.read_text(encoding="utf-8")), "error": None}
        except json.JSONDecodeError as exc:
            return {"payload": None, "error": f"invalid_json:{exc.msg}"}


_coze_workflow_lab_service: CozeWorkflowLabService | None = None


def get_coze_workflow_lab_service() -> CozeWorkflowLabService:
    global _coze_workflow_lab_service
    if _coze_workflow_lab_service is None:
        _coze_workflow_lab_service = CozeWorkflowLabService()
    return _coze_workflow_lab_service
