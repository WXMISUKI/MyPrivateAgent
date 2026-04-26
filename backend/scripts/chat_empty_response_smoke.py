"""Verify chat SSE fallback behavior when upstream returns no content."""

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


class _EmptyOrchestrator:
    async def process_message(self, user_message: str, selected_model: str, execution_context=None):
        if False:
            yield None


def main() -> int:
    original_factory = chat_router.get_orchestrator
    original_learning = chat_router.record_learning_if_possible
    chat_router.get_orchestrator = lambda conversation_id, show_reasoning: _EmptyOrchestrator()
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
                json={"message": "测试空响应兜底", "model_name": "doubao"},
            )
            body = response.text

            payload = {
                "status": "ok" if response.status_code == 200 and "本次未生成有效回复，请重试" in body and '"type": "done"' in body else "fail",
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
