import unittest
from unittest.mock import patch

import httpx

from backend.agent_framework.framework_adapters import AgentFrameworkAdapterRegistry, LangGraphDraftAdapter
from backend.services.framework_adapter_runtime_service import FrameworkAdapterRuntimeService


class _StubRunTraceService:
    trace_calls = []
    audit_calls = []
    existing_runtime_trace_dedupe_keys = set()

    def append_runtime_trace(self, **kwargs):
        self.__class__.trace_calls.append(kwargs)
        payload = kwargs.get("payload") if isinstance(kwargs.get("payload"), dict) else {}
        if payload.get("dedupe_key"):
            self.__class__.existing_runtime_trace_dedupe_keys.add(payload["dedupe_key"])
        return True

    def append_runtime_audit(self, **kwargs):
        self.__class__.audit_calls.append(kwargs)
        return True

    def has_runtime_trace_dedupe_key(self, **kwargs):
        return kwargs.get("dedupe_key") in self.__class__.existing_runtime_trace_dedupe_keys

    def build_snapshot_ref(self, **kwargs):
        return {
            "snapshot_id": "FRAM-EXT-321-20260513000000",
            "generated_at": "2026-05-13T00:00:00Z",
            **kwargs,
        }


class _StubExternalPilotTransport:
    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        return {"status_code": 200, "assistant_exists": True, "assistant_id": assistant_id}

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        return {
            "status": "completed",
            "output": {"content": "LangGraph external answer"},
        }

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        yield {"type": "status", "status": "accepted", "detail": "external runtime accepted"}
        yield {"type": "reasoning", "summary": "external runtime reasoning", "detail": "node=planner"}


class _StubErrorTransport:
    def __init__(self, exc):
        self.exc = exc

    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        raise self.exc

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise self.exc

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        raise self.exc


class _StubQueryControlTimelineService:
    def __init__(self):
        self.calls = []

    def record_stage(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "trace_written": True,
            "audit_written": True,
            "conversation_id": kwargs.get("conversation_id"),
            "snapshot_ref": {"source": "query_control", "event_type": f"query_control_{kwargs.get('stage')}"},
            "dedupe_key": f"query_control:{kwargs.get('channel')}:{kwargs.get('stage')}:{kwargs.get('conversation_id')}:{kwargs.get('query_id')}",
        }


class _FailingQueryControlTimelineService:
    def record_stage(self, **_kwargs):
        raise RuntimeError("query control recorder unavailable")


class _StubProtocolProbeTransport:
    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        return "not-a-mapping"

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("invoke should not be called when preflight fails")

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("stream should not be called when preflight fails")


class _StubMissingAssistantEvidenceTransport:
    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        return {"status_code": 200}

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("invoke should not be called when assistant evidence is missing")

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("stream should not be called when assistant evidence is missing")


class _StubAssistantNotFoundTransport:
    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        return {"status_code": 200, "assistant_exists": False, "assistant_id": assistant_id}

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("invoke should not be called when assistant identity is missing upstream")

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("stream should not be called when assistant identity is missing upstream")


class FrameworkAdapterExternalPilotTests(unittest.TestCase):
    def setUp(self):
        _StubRunTraceService.trace_calls = []
        _StubRunTraceService.audit_calls = []
        _StubRunTraceService.existing_runtime_trace_dedupe_keys = set()

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", False)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_rejects_when_gate_disabled(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()])
        )

        with self.assertRaises(ValueError) as ctx:
            service.execute_external_adapter_run(
                adapter_id="langgraph_draft",
                run_id="run-external-1",
                messages=[{"role": "user", "content": "hello"}],
                execution_context={},
                db=object(),
                user_id=1,
                conversation_id=321,
            )

        self.assertEqual(str(ctx.exception), "external pilot is not enabled")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_runs_translators_and_returns_snapshot(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubExternalPilotTransport(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-2",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"plan_id": 10, "plan_item_id": 24, "run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["adapter_id"], "langgraph_draft")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["final_output"], "LangGraph external answer")
        self.assertTrue(result["events"])
        self.assertEqual(len(_StubRunTraceService.trace_calls), 3)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_status")
        self.assertEqual(_StubRunTraceService.trace_calls[1]["event_type"], "framework_adapter_reasoning")
        self.assertEqual(_StubRunTraceService.trace_calls[2]["event_type"], "framework_adapter_output")
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "framework_adapter_external_pilot_completed")
        self.assertEqual(result["snapshot_ref"]["snapshot_id"], "FRAM-EXT-321-20260513000000")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_records_query_control_lifecycle_when_recorder_is_injected(self, *_mocks):
        query_control_timeline = _StubQueryControlTimelineService()
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubExternalPilotTransport(),
            query_control_timeline_service=query_control_timeline,
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-query-1",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"plan_id": 10, "plan_item_id": 24, "run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        stages = [call["stage"] for call in query_control_timeline.calls]
        self.assertIn("model_stream", stages)
        self.assertIn("planning", stages)
        self.assertIn("final_output", stages)
        self.assertTrue(result["query_control_recordings"])
        first_call = query_control_timeline.calls[0]
        self.assertEqual(first_call["channel"], "external_adapter")
        self.assertEqual(first_call["conversation_id"], 99)
        self.assertEqual(first_call["query_id"], "run-external-query-1")
        self.assertEqual(first_call["payload"]["source_run_id"], "run-external-query-1")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_query_control_failure_does_not_break_pilot(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubExternalPilotTransport(),
            query_control_timeline_service=_FailingQueryControlTimelineService(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-query-2",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"plan_id": 10, "plan_item_id": 24, "run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query_control_recording_failures"][0]["error"], "query control recorder unavailable")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_records_external_error_when_transport_fails(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubErrorTransport(httpx.ConnectError("connect failed")),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-3",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"plan_id": 10, "plan_item_id": 24, "run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error_type"], "connectivity_error")
        self.assertEqual(len(_StubRunTraceService.trace_calls), 1)
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_external_error")
        self.assertTrue(
            _StubRunTraceService.trace_calls[0]["payload"]["dedupe_key"].startswith(
                "framework_adapter_external_error:99:langgraph_draft:connectivity_error:"
            )
        )
        self.assertEqual(_StubRunTraceService.audit_calls[0]["event_type"], "framework_adapter_external_pilot_completed")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_dedupes_repeated_external_error_trace(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubErrorTransport(httpx.ConnectError("connect failed")),
        )

        first_result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-dup-1",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"plan_id": 10, "plan_item_id": 24, "run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )
        second_result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-dup-2",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"plan_id": 10, "plan_item_id": 24, "run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(first_result["status"], "failed")
        self.assertEqual(second_result["status"], "failed")
        external_error_traces = [
            call for call in _StubRunTraceService.trace_calls if call["event_type"] == "framework_adapter_external_error"
        ]
        self.assertEqual(len(external_error_traces), 1)
        self.assertEqual(len(_StubRunTraceService.audit_calls), 2)

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_returns_configuration_error_for_invalid_endpoint(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubExternalPilotTransport(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-4",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error_type"], "configuration_error")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_external_error")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant with spaces")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_returns_configuration_error_for_invalid_assistant_identity(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubExternalPilotTransport(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-5",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error_type"], "configuration_error")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_external_error")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_returns_protocol_error_when_probe_shape_is_invalid(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubProtocolProbeTransport(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-6",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error_type"], "protocol_error")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_external_error")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_returns_protocol_error_when_probe_omits_assistant_evidence(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubMissingAssistantEvidenceTransport(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-7",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error_type"], "protocol_error")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_external_error")

    @patch("backend.services.framework_adapter_runtime_service.get_run_trace_service", return_value=_StubRunTraceService())
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_EXTERNAL_PILOT", True)
    @patch("backend.agent_framework.framework_adapters.ENABLE_LANGGRAPH_RUNTIME_EXECUTION", True)
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_RUNTIME_ENDPOINT", "http://localhost:8123/langgraph")
    @patch("backend.agent_framework.framework_adapters.LANGGRAPH_ASSISTANT_ID", "assistant-1")
    @patch("backend.agent_framework.framework_adapters._is_python_package_available", return_value=True)
    def test_external_pilot_returns_configuration_error_when_assistant_is_not_recognized_upstream(self, *_mocks):
        service = FrameworkAdapterRuntimeService(
            framework_adapter_registry=AgentFrameworkAdapterRegistry([LangGraphDraftAdapter()]),
            external_pilot_transport=_StubAssistantNotFoundTransport(),
        )

        result = service.execute_external_adapter_run(
            adapter_id="langgraph_draft",
            run_id="run-external-8",
            messages=[{"role": "user", "content": "生成总结"}],
            execution_context={"run_kind": "framework_adapter_external_pilot"},
            db=object(),
            user_id=1,
            conversation_id=99,
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["error_type"], "configuration_error")
        self.assertEqual(_StubRunTraceService.trace_calls[0]["event_type"], "framework_adapter_external_error")


if __name__ == "__main__":
    unittest.main()
