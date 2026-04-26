"""Auth + conversation minimal smoke flow for demo readiness."""

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
except ModuleNotFoundError:  # pragma: no cover - package import compatibility
    from backend.agent_server import create_app
    from backend.agent_server.config import AgentServerBootstrapConfig, AgentServerConfig, AgentServerUIConfig


def main() -> int:
    app = create_app(
        config=AgentServerConfig(
            bootstrap=AgentServerBootstrapConfig(load_environment=True, init_database=True),
            ui=AgentServerUIConfig(enabled=False, mode="disabled"),
        )
    )
    results = []
    with TestClient(app) as client:
        guest_response = client.post("/api/auth/guest")
        guest_ok = guest_response.status_code == 200 and bool(guest_response.json().get("access_token"))
        results.append(
            {
                "path": "/api/auth/guest",
                "status_code": guest_response.status_code,
                "ok": guest_ok,
                "body_excerpt": json.dumps(guest_response.json(), ensure_ascii=False)[:300],
            }
        )
        if not guest_ok:
            payload = {"status": "fail", "checks": results}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1

        token = guest_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        for method, path, payload in (
            ("get", "/api/auth/me", None),
            ("post", "/api/conversations", {"title": "Smoke Check", "model_name": "doubao"}),
            ("get", "/api/conversations", None),
        ):
            if method == "get":
                response = client.get(path, headers=headers)
            else:
                response = client.post(path, headers=headers, json=payload)
            results.append(
                {
                    "path": path,
                    "method": method.upper(),
                    "status_code": response.status_code,
                    "ok": response.status_code == 200,
                    "body_excerpt": json.dumps(response.json(), ensure_ascii=False)[:300],
                }
            )

        created = results[2]
        if created["ok"]:
            conversation_id = client.post(
                "/api/conversations",
                headers=headers,
                json={"title": "Smoke Check Detail", "model_name": "doubao"},
            ).json().get("id")
            if conversation_id:
                detail_response = client.get(f"/api/conversations/{conversation_id}", headers=headers)
                results.append(
                    {
                        "path": f"/api/conversations/{conversation_id}",
                        "method": "GET",
                        "status_code": detail_response.status_code,
                        "ok": detail_response.status_code == 200,
                        "body_excerpt": json.dumps(detail_response.json(), ensure_ascii=False)[:300],
                    }
                )

    payload = {"status": "ok" if all(item["ok"] for item in results) else "fail", "checks": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
