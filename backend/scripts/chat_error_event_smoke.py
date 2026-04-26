"""Verify chat SSE error-event handling without a real model backend."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _bootstrap_path() -> None:
    root = Path(__file__).resolve().parents[2]
    candidate = str(root)
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


_bootstrap_path()

try:
    from agent_server import create_app
    from agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
    from routers import chat as chat_router
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server import create_app
    from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
    from backend.routers import chat as chat_router


class _ErrorOrchestrator:
    async def process_message(self, user_message: str, selected_model: str, execution_context=None):
        yield json.dumps({"type": "error", "error": "模拟流式错误"})


def main() -> int:
    original_factory = chat_router.get_orchestrator
    original_learning = chat_router.record_learning_if_possible
    chat_router.get_orchestrator = lambda conversation_id, show_reasoning: _ErrorOrchestrator()
    chat_router.record_learning_if_possible = lambda **kwargs: None

    app = create_app(
        config=AgentServerConfig(
            bootstrap=AgentServerBootstrapConfig(load_environment=True, init_database=True),
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
        )
    )
    try:
        with TestClient(app) as client:
            guest_response = client.post("/api/auth/guest")
            token = guest_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = client.post(
                "/api/chat",
                headers=headers,
                json={"message": "测试错误事件兜底", "model_name": "doubao"},
            )
            body = response.text

            contains_error = (
                "模拟流式错误" in body
                or "\\u6a21\\u62df\\u6d41\\u5f0f\\u9519\\u8bef" in body
                or '"type": "error"' in body
            )
            contains_done = '"type": "done"' in body
            payload = {
                "status": "ok" if response.status_code == 200 and contains_error and contains_done else "fail",
                "checks": [
                    {
                        "path": "/api/chat",
                        "status_code": response.status_code,
                        "contains_error": contains_error,
                        "contains_done": contains_done,
                        "body_excerpt": body[:500],
                    }
                ],
            }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "ok" else 1
    finally:
        chat_router.get_orchestrator = original_factory
        chat_router.record_learning_if_possible = original_learning


if __name__ == "__main__":
    raise SystemExit(main())
