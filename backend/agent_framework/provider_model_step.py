"""Provider model-step adapter for the Embedded SDK execution loop.

This module provides a factory function that wraps the existing
``ModelProviderRegistry`` into a ``ModelStepCallable``, enabling
vertical-agent projects to invoke a real LLM through the execution
loop's ``model_step`` seam without hand-authoring a callable each time.

Usage::

    from backend.agent_framework.provider_model_step import build_provider_model_step

    model_step = build_provider_model_step(model_name="doubao")
    result = sdk.execute_run(run_id, model_step=model_step)

The adapter is opt-in and does not change default behavior.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .execution_loop import ExecutionModelStepResult, ModelStepCallable
from .providers import ModelProvider
from .runtime import AgentRunContext

logger = logging.getLogger(__name__)


def build_provider_model_step(
    model_name: str,
    *,
    provider: Optional[ModelProvider] = None,
) -> ModelStepCallable:
    """Build a ``ModelStepCallable`` that resolves a model from the provider
    registry and invokes it synchronously.

    Parameters
    ----------
    model_name:
        The model name to resolve (e.g. ``"doubao"``, ``"llama3.1"``).
    provider:
        Optional ``ModelProvider`` instance. If ``None``, uses the default
        ``ModelRouterProviderAdapter`` singleton via ``get_model_provider()``.

    Returns
    -------
    ModelStepCallable
        A callable that, when invoked with an ``AgentRunContext``, resolves
        the model, constructs a minimal message list, invokes the model
        synchronously, and returns an ``ExecutionModelStepResult``.
    """

    def _model_step(run_context: AgentRunContext) -> ExecutionModelStepResult:
        resolved_provider = provider or _get_default_provider()
        effective_model_name = run_context.model_name or model_name

        model = resolved_provider.get_model(effective_model_name)
        messages = _build_messages(run_context)

        response = model.invoke(messages)

        return _normalize_response(response, effective_model_name)

    return _model_step


def _get_default_provider() -> ModelProvider:
    """Get the default provider via the existing ModelRouter singleton."""
    try:
        from .adapters import get_model_provider
    except (ImportError, ModuleNotFoundError):
        try:
            from backend.agent_framework.adapters import get_model_provider
        except (ImportError, ModuleNotFoundError):
            raise RuntimeError(
                "No provider supplied and default ModelRouterProviderAdapter "
                "is not available. Pass an explicit `provider` to "
                "build_provider_model_step()."
            )
    return get_model_provider()


def _build_messages(run_context: AgentRunContext) -> list:
    """Construct a minimal message list from the run context.

    Extracts ``system_prompt`` and ``user_message`` (or ``input``) from
    ``run_context.metadata``. This is intentionally minimal — richer
    message construction (history, tool results) belongs to the
    orchestrator layer.
    """
    messages = []
    system_prompt = run_context.metadata.get("system_prompt")
    if system_prompt:
        messages.append({"role": "system", "content": str(system_prompt)})

    user_message = (
        run_context.metadata.get("user_message")
        or run_context.metadata.get("input")
        or ""
    )
    messages.append({"role": "user", "content": str(user_message)})
    return messages


def _normalize_response(response: Any, model_name: str) -> ExecutionModelStepResult:
    """Normalize a LangChain model response into an ``ExecutionModelStepResult``.

    Handles ``AIMessage`` objects (with ``.content`` and ``.usage_metadata``)
    and falls back to string conversion for other types.
    """
    text = ""
    finish_reason = ""
    usage: Dict[str, Any] = {}

    # LangChain AIMessage has .content
    content = getattr(response, "content", None)
    if content is not None:
        text = str(content)
    else:
        text = str(response)

    # LangChain AIMessage may have .usage_metadata
    usage_metadata = getattr(response, "usage_metadata", None)
    if isinstance(usage_metadata, dict):
        usage = {
            "prompt_tokens": usage_metadata.get("input_tokens", 0),
            "completion_tokens": usage_metadata.get("output_tokens", 0),
            "total_tokens": usage_metadata.get("total_tokens", 0),
        }

    # LangChain AIMessage may have .response_metadata
    response_metadata = getattr(response, "response_metadata", None)
    if isinstance(response_metadata, dict):
        finish_reason = str(response_metadata.get("finish_reason") or "")

    return ExecutionModelStepResult(
        text=text,
        summary=text[:160],
        model_name=model_name,
        finish_reason=finish_reason,
        usage=usage,
    )
