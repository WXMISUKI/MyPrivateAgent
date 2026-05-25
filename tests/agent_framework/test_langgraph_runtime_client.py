import unittest

import httpx

from backend.agent_framework.external.langgraph_client import (
    LangGraphRuntimeClient,
    LangGraphRuntimeClientError,
)


class _StubInvokeTransport:
    def __init__(self):
        self.calls = []

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        self.calls.append({
            "endpoint": endpoint,
            "payload": payload,
            "timeout_seconds": timeout_seconds,
            "headers": headers,
        })
        return {"status": "accepted", "output": {"content": "ok"}}

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("stream should not be called in invoke test")


class _StubStreamingTransport:
    def __init__(self):
        self.probe_calls = []

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise AssertionError("invoke should not be called in stream test")

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        yield {"type": "status", "message": "accepted"}
        yield {"type": "output", "content": "hello"}

    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        self.probe_calls.append({
            "endpoint": endpoint,
            "timeout_seconds": timeout_seconds,
            "headers": headers,
            "assistant_id": assistant_id,
        })
        return {"status_code": 200, "assistant_exists": True, "assistant_id": assistant_id}


class _StubErrorTransport:
    def __init__(self, exc):
        self.exc = exc

    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        raise self.exc

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        raise self.exc

    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        raise self.exc


class _BadInvokeTransport:
    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        return "not-a-dict"

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        return iter(())


class _BadStreamTransport:
    def invoke(self, *, endpoint, payload, timeout_seconds, headers):
        return {}

    def stream(self, *, endpoint, payload, timeout_seconds, headers):
        yield {"type": "status", "message": "accepted"}
        yield "not-a-dict"

    def probe(self, *, endpoint, timeout_seconds, headers, assistant_id=None):
        return {"status_code": 200, "assistant_exists": True, "assistant_id": assistant_id}


class LangGraphRuntimeClientTests(unittest.TestCase):
    def test_invoke_delegates_to_transport_and_returns_payload(self):
        transport = _StubInvokeTransport()
        client = LangGraphRuntimeClient(transport=transport, timeout_seconds=9.5)

        result = client.invoke(
            endpoint="http://localhost:8123/langgraph",
            payload={"run_id": "run_1"},
            headers={"Authorization": "Bearer demo"},
        )

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(transport.calls[0]["endpoint"], "http://localhost:8123/langgraph")
        self.assertEqual(transport.calls[0]["payload"], {"run_id": "run_1"})
        self.assertEqual(transport.calls[0]["timeout_seconds"], 9.5)
        self.assertEqual(transport.calls[0]["headers"]["Authorization"], "Bearer demo")

    def test_stream_yields_transport_chunks(self):
        client = LangGraphRuntimeClient(
            transport=_StubStreamingTransport(),
            timeout_seconds=4.0,
        )

        chunks = list(client.stream(
            endpoint="http://localhost:8123/langgraph",
            payload={"run_id": "run_2"},
            headers={},
        ))

        self.assertEqual(
            chunks,
            [
                {"type": "status", "message": "accepted"},
                {"type": "output", "content": "hello"},
            ],
        )

    def test_invoke_wraps_connectivity_error(self):
        client = LangGraphRuntimeClient(
            transport=_StubErrorTransport(httpx.ConnectError("connect failed")),
        )

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "connectivity_error")

    def test_invoke_wraps_authentication_error(self):
        client = LangGraphRuntimeClient(
            transport=_StubErrorTransport(PermissionError("401 unauthorized")),
        )

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "authentication_error")

    def test_invoke_wraps_protocol_error_when_transport_returns_non_mapping(self):
        client = LangGraphRuntimeClient(transport=_BadInvokeTransport())

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "protocol_error")

    def test_invoke_wraps_unknown_errors_as_upstream_runtime_error(self):
        client = LangGraphRuntimeClient(
            transport=_StubErrorTransport(RuntimeError("upstream exploded")),
        )

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.invoke(endpoint="http://localhost:8123/langgraph", payload={}, headers={})

        self.assertEqual(ctx.exception.error_type, "upstream_runtime_error")

    def test_stream_wraps_protocol_error_when_transport_yields_non_mapping(self):
        client = LangGraphRuntimeClient(transport=_BadStreamTransport())

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            list(client.stream(endpoint="http://localhost:8123/langgraph", payload={}, headers={}))

        self.assertEqual(ctx.exception.error_type, "protocol_error")

    def test_probe_delegates_to_transport(self):
        transport = _StubStreamingTransport()
        client = LangGraphRuntimeClient(
            transport=transport,
            timeout_seconds=3.0,
        )

        result = client.probe(
            endpoint="http://localhost:8123/langgraph",
            headers={"Authorization": "Bearer demo"},
            assistant_id="assistant-1",
        )

        self.assertEqual(result["status_code"], 200)
        self.assertTrue(result["assistant_exists"])
        self.assertEqual(transport.probe_calls[0]["assistant_id"], "assistant-1")

    def test_probe_wraps_connectivity_error(self):
        client = LangGraphRuntimeClient(
            transport=_StubErrorTransport(httpx.ConnectError("connect failed")),
        )

        with self.assertRaises(LangGraphRuntimeClientError) as ctx:
            client.probe(endpoint="http://localhost:8123/langgraph", headers={}, assistant_id="assistant-1")

        self.assertEqual(ctx.exception.error_type, "connectivity_error")


if __name__ == "__main__":
    unittest.main()
