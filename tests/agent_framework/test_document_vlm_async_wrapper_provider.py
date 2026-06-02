import time

from fastapi.testclient import TestClient

from backend.scripts.document_vlm_async_wrapper_provider import AsyncVlmWrapperProvider, create_app


def _wait_for_terminal(client: TestClient, job_id: str, timeout_seconds: float = 2.0):
    deadline = time.time() + timeout_seconds
    latest = None
    while time.time() < deadline:
        response = client.get(f"/api/vlm/jobs/{job_id}")
        latest = response.json()
        status = latest["result"]["status"]
        if status in {"succeeded", "failed"}:
            return latest
        time.sleep(0.02)
    return latest


def test_async_wrapper_submit_and_status_success():
    def fake_upstream(payload):
        assert payload["fileType"] == 0
        assert payload["outputFormat"] == "markdown"
        return {
            "errorCode": 0,
            "result": {
                "layoutParsingResults": [
                    {
                        "markdown": {"text": "# Summary\nDocument content"},
                        "prunedResult": {"layouts": [{"type": "title"}], "table_res_list": []},
                    }
                ]
            },
        }

    provider = AsyncVlmWrapperProvider(upstream_invoker=fake_upstream)
    client = TestClient(create_app(provider))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["errorCode"] == 0

    submit = client.post(
        "/api/vlm/jobs",
        json={"file": "JVBERg==", "fileType": 0, "task": "summarize"},
    )
    assert submit.status_code == 202
    job_id = submit.json()["result"]["job_id"]

    final = _wait_for_terminal(client, job_id)
    assert final["result"]["status"] == "succeeded"
    assert final["result"]["progress"] == 1.0
    assert final["result"]["result"]["summary"].startswith("# Summary")
    assert final["result"]["result"]["evidence"][0]["layout_count"] == 1


def test_async_wrapper_keeps_failed_job_queryable():
    def failing_upstream(payload):
        return {"errorCode": 500, "errorMsg": "upstream failed"}

    provider = AsyncVlmWrapperProvider(upstream_invoker=failing_upstream)
    client = TestClient(create_app(provider))

    submit = client.post(
        "/api/vlm/jobs",
        json={"file": "AAA=", "fileType": 1, "task": "summarize"},
    )
    job_id = submit.json()["result"]["job_id"]

    final = _wait_for_terminal(client, job_id)
    assert final["result"]["status"] == "failed"
    assert final["result"]["error"]["code"] == "DOCUMENT_VLM_UPSTREAM_ERROR"


def test_async_wrapper_unknown_job_returns_404():
    provider = AsyncVlmWrapperProvider(upstream_invoker=lambda payload: {"errorCode": 0, "result": {}})
    client = TestClient(create_app(provider))

    response = client.get("/api/vlm/jobs/missing")

    assert response.status_code == 404
    assert response.json()["result"]["error"]["code"] == "VLM_JOB_NOT_FOUND"
