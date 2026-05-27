"""HTTP client for external capability providers."""

from __future__ import annotations

from typing import Any

import httpx


class CapabilityProviderError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_payload(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class HttpCapabilityClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def get_json(self, path: str) -> dict[str, Any]:
        return self._request_json("GET", path)

    def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request_json("POST", path, json_payload=payload)

    def _request_json(self, method: str, path: str, json_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            with httpx.Client(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = client.request(method, url, json=json_payload)
                data = self._parse_json(response)
                if response.status_code >= 400:
                    error = data.get("error") if isinstance(data, dict) else None
                    message = str((error or {}).get("message") or response.text or response.status_code)
                    code = str((error or {}).get("code") or "CAPABILITY_PROVIDER_ERROR")
                    raise CapabilityProviderError(code, message)
                return data
        except CapabilityProviderError:
            raise
        except httpx.RequestError as exc:
            raise CapabilityProviderError(
                "CAPABILITY_PROVIDER_UNREACHABLE",
                f"Capability provider unreachable at {self.base_url}: {exc}",
            ) from exc
        except ValueError as exc:
            raise CapabilityProviderError(
                "CAPABILITY_PROVIDER_PROTOCOL_ERROR",
                f"Capability provider returned invalid JSON: {exc}",
            ) from exc

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("expected JSON object")
        return data
