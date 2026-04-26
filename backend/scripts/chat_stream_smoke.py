"""Minimal chat SSE smoke check without relying on a real model backend."""

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


class _SmokeOrchestrator:
    async def process_message(self, user_message: str, selected_model: str, execution_context=None):
        yield json.dumps({"type": "content", "content": "smoke-1"})
        yield json.dumps({"type": "content", "content": "smoke-2"})


def main() -> int:
    original_factory = chat_router.get_orchestrator
    original_learning = chat_router.record_learning_if_possible
    chat_router.get_orchestrator = lambda conversation_id, show_reasoning: _SmokeOrchestrator()
    chat_router.record_learning_if_possible = lambda **kwargs: None

    app = create_app(
        config=AgentServerConfig(
            bootstrap=AgentServerBootstrapConfig(load_environment=True, init_database=True),
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
        )
    )
    results = []
    try:
        with TestClient(app) as client:
            guest_response = client.post("/api/auth/guest")
            guest_ok = guest_response.status_code == 200 and bool(guest_response.json().get("access_token"))
            results.append(
                {
                    "path": "/api/auth/guest",
                    "status_code": guest_response.status_code,
                    "ok": guest_ok,
                    "body_excerpt": json.dumps(guest_response.json(), ensure_ascii=False)[:200],
                }
            )
            if not guest_ok:
                payload = {"status": "fail", "checks": results}
                print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 1

            token = guest_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            response = client.post(
                "/api/chat",
                headers=headers,
                json={"message": "请输出一个最小流式响应", "model_name": "doubao"},
            )
            body = response.text
            results.append(
                {
                    "path": "/api/chat",
                    "method": "POST",
                    "status_code": response.status_code,
                    "ok": response.status_code == 200 and "data:" in body and '"type": "done"' in body,
                    "body_excerpt": body[:500],
                }
            )

        payload = {"status": "ok" if all(item["ok"] for item in results) else "fail", "checks": results}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "ok" else 1
    finally:
        chat_router.get_orchestrator = original_factory
        chat_router.record_learning_if_possible = original_learning


if __name__ == "__main__":
    raise SystemExit(main())
