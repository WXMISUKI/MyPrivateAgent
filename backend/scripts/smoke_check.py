"""Minimal backend smoke check without invoking the heavy chat model path."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

try:
    from agent_server import create_app
    from agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server import create_app
    from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig


def main() -> int:
    app = create_app(
        config=AgentServerConfig(
            bootstrap=AgentServerBootstrapConfig(load_environment=True, init_database=False),
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
        )
    )
    client = TestClient(app)

    results = []
    for path in ("/api/health", "/api/models"):
        response = client.get(path)
        results.append(
            {
                "path": path,
                "status_code": response.status_code,
                "ok": response.status_code == 200,
                "body_excerpt": json.dumps(response.json(), ensure_ascii=False)[:300],
            }
        )

    payload = {
        "status": "ok" if all(item["ok"] for item in results) else "fail",
        "checks": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
