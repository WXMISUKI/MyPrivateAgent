from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Mapping, Protocol

import httpx


@dataclass
class LangGraphRuntimeClientError(RuntimeError):
    error_type: str
    detail: str

    def __str__(self) -> str:
        return f"{self.error_type}: {self.detail}"


class LangGraphTransport(Protocol):
    def probe(
        self,
        *,
        endpoint: str,
        timeout_seconds: float,
        headers: Mapping[str, str],
        assistant_id: str | None = None,
    ) -> Mapping[str, Any]:
        ...

    def invoke(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        timeout_seconds: float,
        headers: Mapping[str, str],
    ) -> Mapping[str, Any]:
        ...

    def stream(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        timeout_seconds: float,
        headers: Mapping[str, str],
    ) -> Iterator[Mapping[str, Any]]:
        ...


class HttpxLangGraphTransport:
    def probe(
        self,
        *,
        endpoint: str,
        timeout_seconds: float,
        headers: Mapping[str, str],
        assistant_id: str | None = None,
    ) -> Mapping[str, Any]:
        response = httpx.get(
            endpoint,
            params={"assistant_id": assistant_id} if assistant_id else None,
            headers=dict(headers),
            timeout=timeout_seconds,
        )
        payload = {
            "status_code": int(response.status_code),
        }
        try:
            data = response.json()
        except Exception:
            return payload
        if isinstance(data, Mapping):
            payload.update(dict(data))
        return payload

    def invoke(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        timeout_seconds: float,
        headers: Mapping[str, str],
    ) -> Mapping[str, Any]:
        response = httpx.post(
            endpoint,
            json=dict(payload),
            headers=dict(headers),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, Mapping):
            raise ValueError("langgraph runtime invoke returned a non-mapping payload")
        return data

    def stream(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        timeout_seconds: float,
        headers: Mapping[str, str],
    ) -> Iterator[Mapping[str, Any]]:
        response = httpx.post(
            endpoint,
            json=dict(payload),
            headers=dict(headers),
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, Mapping):
            chunks = data.get("chunks")
            if isinstance(chunks, list):
                for item in chunks:
                    if isinstance(item, Mapping):
                        yield item
                if not chunks:
                    yield data
                return
            yield data
            return
        if isinstance(data, list):
            for item in data:
                if isinstance(item, Mapping):
                    yield item
            return
        raise ValueError("langgraph runtime stream returned an unsupported payload")


class LangGraphRuntimeClient:
    def __init__(self, *, transport: LangGraphTransport, timeout_seconds: float = 10.0):
        self.transport = transport
        self.timeout_seconds = float(timeout_seconds)

    def invoke(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any]:
        try:
            result = self.transport.invoke(
                endpoint=endpoint,
                payload=payload,
                timeout_seconds=self.timeout_seconds,
                headers=dict(headers or {}),
            )
        except Exception as exc:
            raise self._wrap_error(exc) from exc

        if not isinstance(result, Mapping):
            raise LangGraphRuntimeClientError(
                error_type="protocol_error",
                detail="transport invoke returned a non-mapping payload",
            )
        return result

    def probe(
        self,
        *,
        endpoint: str,
        headers: Mapping[str, str] | None = None,
        assistant_id: str | None = None,
    ) -> Mapping[str, Any]:
        try:
            result = self.transport.probe(
                endpoint=endpoint,
                timeout_seconds=self.timeout_seconds,
                headers=dict(headers or {}),
                assistant_id=assistant_id,
            )
        except Exception as exc:
            raise self._wrap_error(exc) from exc

        if not isinstance(result, Mapping):
            raise LangGraphRuntimeClientError(
                error_type="protocol_error",
                detail="transport probe returned a non-mapping payload",
            )
        return result

    def stream(
        self,
        *,
        endpoint: str,
        payload: Mapping[str, Any],
        headers: Mapping[str, str] | None = None,
    ) -> Iterator[Mapping[str, Any]]:
        try:
            iterator = self.transport.stream(
                endpoint=endpoint,
                payload=payload,
                timeout_seconds=self.timeout_seconds,
                headers=dict(headers or {}),
            )
            for item in iterator:
                if not isinstance(item, Mapping):
                    raise LangGraphRuntimeClientError(
                        error_type="protocol_error",
                        detail="transport stream yielded a non-mapping chunk",
                    )
                yield item
        except LangGraphRuntimeClientError:
            raise
        except Exception as exc:
            raise self._wrap_error(exc) from exc

    @staticmethod
    def _wrap_error(exc: Exception) -> LangGraphRuntimeClientError:
        if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
            return LangGraphRuntimeClientError(
                error_type="connectivity_error",
                detail=str(exc),
            )
        if isinstance(exc, PermissionError):
            return LangGraphRuntimeClientError(
                error_type="authentication_error",
                detail=str(exc),
            )
        if isinstance(exc, ValueError):
            return LangGraphRuntimeClientError(
                error_type="protocol_error",
                detail=str(exc),
            )
        return LangGraphRuntimeClientError(
            error_type="upstream_runtime_error",
            detail=str(exc),
        )
