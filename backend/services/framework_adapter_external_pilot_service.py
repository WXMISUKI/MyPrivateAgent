"""External framework adapter pilot execution orchestration."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence

try:
    from agent_framework.external import (
        HttpxLangGraphTransport,
        LangGraphEventTranslator,
        LangGraphOutputTranslator,
        LangGraphRequestTranslator,
        LangGraphRuntimeClient,
        LangGraphRuntimeClientError,
    )
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_framework.external import (
        HttpxLangGraphTransport,
        LangGraphEventTranslator,
        LangGraphOutputTranslator,
        LangGraphRequestTranslator,
        LangGraphRuntimeClient,
        LangGraphRuntimeClientError,
    )


class FrameworkAdapterExternalPilotService:
    """Run a controlled external framework pilot without owning trace/audit persistence."""

    def __init__(
        self,
        *,
        transport: Any = None,
        setting_reader: Callable[[str, Any], Any],
    ):
        self.transport = transport
        self.setting_reader = setting_reader

    def execute(
        self,
        *,
        adapter: Any,
        run_id: str,
        messages: Sequence[Mapping[str, Any]],
        execution_context: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = dict(execution_context or {})
        request_translator = LangGraphRequestTranslator(
            adapter_id=adapter.adapter_id,
            framework_name=getattr(adapter, "framework_name", "LangGraph"),
            assistant_id=str(self.setting_reader("LANGGRAPH_ASSISTANT_ID", "") or ""),
            endpoint=str(self.setting_reader("LANGGRAPH_RUNTIME_ENDPOINT", "") or ""),
        )
        translated_input = request_translator.translate(
            run_id=run_id,
            messages=messages,
            execution_context=context,
        )
        client = LangGraphRuntimeClient(
            transport=self.transport or HttpxLangGraphTransport(),
        )
        event_translator = LangGraphEventTranslator(
            adapter_id=adapter.adapter_id,
            framework_name=getattr(adapter, "framework_name", "LangGraph"),
        )
        output_translator = LangGraphOutputTranslator(
            adapter_id=adapter.adapter_id,
            framework_name=getattr(adapter, "framework_name", "LangGraph"),
        )

        events: List[Dict[str, Any]] = []
        final_output = ""
        status = "ok"
        error_payload: Dict[str, Any] | None = None
        try:
            self.validate_request(translated_input)
            probe_result = client.probe(
                endpoint=translated_input["endpoint"],
                headers={},
                assistant_id=translated_input["assistant_id"],
            )
            self.validate_probe(
                probe_result=probe_result,
                assistant_id=translated_input["assistant_id"],
            )
            for chunk in client.stream(
                endpoint=translated_input["endpoint"],
                payload=translated_input,
                headers={},
            ):
                events.extend(
                    event_translator.translate_chunk(
                        run_id=run_id,
                        chunk=dict(chunk),
                        execution_context=context,
                    )
                )
            remote_output = client.invoke(
                endpoint=translated_input["endpoint"],
                payload=translated_input,
                headers={},
            )
            output_payload = remote_output.get("output") if isinstance(remote_output, Mapping) and "output" in remote_output else remote_output
            output_events = output_translator.translate_final(
                run_id=run_id,
                output=output_payload,
                execution_context=context,
            )
            events.extend(output_events)
            final_output = str(output_events[0].get("payload", {}).get("content") or "") if output_events else ""
        except LangGraphRuntimeClientError as exc:
            status = "failed"
            error_payload = {
                "error_type": exc.error_type,
                "detail": exc.detail,
            }
            events.extend(self._build_error_events(
                event_translator=event_translator,
                run_id=run_id,
                execution_context=context,
                error_payload=error_payload,
            ))
        except Exception as exc:
            status = "failed"
            error_payload = {
                "error_type": "upstream_runtime_error",
                "detail": str(exc),
            }
            events.extend(self._build_error_events(
                event_translator=event_translator,
                run_id=run_id,
                execution_context=context,
                error_payload=error_payload,
            ))

        result = {
            "adapter_id": adapter.adapter_id,
            "run_id": run_id,
            "translated_input": translated_input,
            "events": events,
            "final_output": final_output,
            "status": status,
        }
        if error_payload is not None:
            result["error"] = error_payload
        return result

    def validate_request(self, translated_input: Mapping[str, Any]) -> None:
        endpoint = str(translated_input.get("endpoint") or "").strip()
        assistant_id = str(translated_input.get("assistant_id") or "").strip()

        if not assistant_id:
            raise LangGraphRuntimeClientError(
                error_type="configuration_error",
                detail="assistant identity is required",
            )
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", assistant_id):
            raise LangGraphRuntimeClientError(
                error_type="configuration_error",
                detail="assistant identity contains unsupported characters",
            )
        if not endpoint:
            raise LangGraphRuntimeClientError(
                error_type="configuration_error",
                detail="runtime endpoint is required",
            )
        parsed_endpoint = urlparse(endpoint)
        if parsed_endpoint.scheme not in ("http", "https") or not parsed_endpoint.netloc:
            raise LangGraphRuntimeClientError(
                error_type="configuration_error",
                detail="runtime endpoint must be a valid http/https URL",
            )

    def validate_probe(
        self,
        *,
        probe_result: Mapping[str, Any],
        assistant_id: str,
    ) -> None:
        normalized_assistant_id = str(assistant_id or "").strip()

        if "assistant_exists" in probe_result:
            assistant_exists = probe_result.get("assistant_exists")
            if not isinstance(assistant_exists, bool):
                raise LangGraphRuntimeClientError(
                    error_type="protocol_error",
                    detail="transport probe returned a non-boolean assistant_exists field",
                )
            if not assistant_exists:
                raise LangGraphRuntimeClientError(
                    error_type="configuration_error",
                    detail="assistant identity is not recognized by external runtime",
                )
            return

        if "assistant_id" in probe_result:
            resolved_assistant_id = str(probe_result.get("assistant_id") or "").strip()
            if not resolved_assistant_id:
                raise LangGraphRuntimeClientError(
                    error_type="protocol_error",
                    detail="transport probe returned an empty assistant identity",
                )
            if resolved_assistant_id != normalized_assistant_id:
                raise LangGraphRuntimeClientError(
                    error_type="configuration_error",
                    detail="assistant identity is not recognized by external runtime",
                )
            return

        if "assistants" in probe_result:
            assistants = probe_result.get("assistants")
            if not isinstance(assistants, (list, tuple, set)):
                raise LangGraphRuntimeClientError(
                    error_type="protocol_error",
                    detail="transport probe returned an unsupported assistants field",
                )
            resolved_assistants = {
                str(item or "").strip()
                for item in assistants
                if str(item or "").strip()
            }
            if normalized_assistant_id not in resolved_assistants:
                raise LangGraphRuntimeClientError(
                    error_type="configuration_error",
                    detail="assistant identity is not recognized by external runtime",
                )
            return

        raise LangGraphRuntimeClientError(
            error_type="protocol_error",
            detail="transport probe did not provide assistant identity evidence",
        )

    @staticmethod
    def _build_error_events(
        *,
        event_translator: Any,
        run_id: str,
        execution_context: Mapping[str, Any],
        error_payload: Mapping[str, Any],
    ) -> List[Dict[str, Any]]:
        return event_translator.translate_chunk(
            run_id=run_id,
            chunk={
                "type": "error",
                "error_type": error_payload.get("error_type"),
                "detail": error_payload.get("detail"),
            },
            execution_context=execution_context,
        )
