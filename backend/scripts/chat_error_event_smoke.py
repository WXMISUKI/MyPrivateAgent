"""Verify chat SSE error-event handling without a real model backend."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

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
            bootstrap=AgentServerBootstrapConfig(load_environment=True, init_database=False),
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
        )
    )
    client = TestClient(app)

    try:
        guest_response = client.post("/api/auth/guest")
        token = guest_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/api/chat",
            headers=headers,
            json={"message": "测试错误事件兜底", "model_name": "doubao"},
        )
        body = response.text

        payload = {
            "status": "ok" if response.status_code == 200 and "模拟流式错误" in body else "fail",
            "checks": [
                {
                    "path": "/api/chat",
                    "status_code": response.status_code,
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
