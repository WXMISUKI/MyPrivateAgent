"""Local async wrapper provider for Stage 3B document VLM acceptance.

This provider is intentionally lightweight. It exposes the async job API expected
by MyPrivateAgent and delegates real parsing to a configured synchronous upstream
provider such as PaddleOCR PP-StructureV3.

Run:
  python backend/scripts/document_vlm_async_wrapper_provider.py --host 127.0.0.1 --port 8082
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI
from fastapi.responses import JSONResponse


TERMINAL_STATUSES = {"succeeded", "failed"}
SUPPORTED_TASKS = {"summarize", "extract_fields", "chart_understanding", "qa"}


@dataclass
class JobRecord:
    job_id: str
    status: str = "queued"
    progress: float = 0.0
    result: dict[str, Any] = field(default_factory=dict)
    error: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_payload(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "warnings": self.warnings,
            "raw": self.raw,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


UpstreamInvoker = Callable[[dict[str, Any]], dict[str, Any]]


class AsyncVlmWrapperProvider:
    def __init__(
        self,
        *,
        upstream_base_url: str = "http://127.0.0.1:8081",
        upstream_invoke_path: str = "/layout-parsing",
        upstream_timeout_seconds: float = 120.0,
        upstream_invoker: UpstreamInvoker | None = None,
    ) -> None:
        self.upstream_base_url = upstream_base_url.rstrip("/")
        self.upstream_invoke_path = _normalize_path(upstream_invoke_path, "/layout-parsing")
        self.upstream_timeout_seconds = upstream_timeout_seconds
        self._upstream_invoker = upstream_invoker or self._post_upstream
        self._jobs: dict[str, JobRecord] = {}
        self._lock = threading.Lock()

    def health(self) -> dict[str, Any]:
        return {
            "logId": str(uuid.uuid4()),
            "errorCode": 0,
            "errorMsg": "Healthy",
            "service": "document-vlm-async-wrapper",
            "upstream_base_url": self.upstream_base_url,
            "upstream_invoke_path": self.upstream_invoke_path,
        }

    def submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        validation_error = _validate_submit_payload(payload)
        if validation_error is not None:
            return {"errorCode": 400, "errorMsg": validation_error["message"], "error": validation_error}

        job_id = f"vlm-job-{uuid.uuid4().hex}"
        job = JobRecord(job_id=job_id)
        with self._lock:
            self._jobs[job_id] = job

        worker = threading.Thread(target=self._run_job, args=(job_id, dict(payload)), daemon=True)
        worker.start()
        return {"errorCode": 0, "errorMsg": "Accepted", "result": job.to_payload()}

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return {"errorCode": 0, "errorMsg": "Success", "result": job.to_payload()}

    def _run_job(self, job_id: str, payload: dict[str, Any]) -> None:
        self._update_job(job_id, status="running", progress=0.1)
        try:
            upstream_payload = _to_layout_payload(payload)
            self._update_job(job_id, progress=0.35)
            upstream_response = self._upstream_invoker(upstream_payload)
            self._update_job(job_id, progress=0.8)
            error_code = upstream_response.get("errorCode")
            if error_code not in (0, "0", None):
                self._update_job(
                    job_id,
                    status="failed",
                    progress=1.0,
                    error={
                        "code": "DOCUMENT_VLM_UPSTREAM_ERROR",
                        "message": str(upstream_response.get("errorMsg") or "Upstream parsing failed."),
                        "provider_error_code": str(error_code),
                    },
                    raw=upstream_response,
                )
                return

            upstream_result = upstream_response.get("result") if isinstance(upstream_response.get("result"), dict) else {}
            normalized = _normalize_vlm_result(upstream_result, payload)
            self._update_job(
                job_id,
                status="succeeded",
                progress=1.0,
                result=normalized,
                raw=upstream_response,
            )
        except Exception as exc:  # pragma: no cover - defensive provider boundary
            self._update_job(
                job_id,
                status="failed",
                progress=1.0,
                error={"code": "DOCUMENT_VLM_WRAPPER_ERROR", "message": str(exc)},
            )

    def _update_job(self, job_id: str, **updates: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for key, value in updates.items():
                setattr(job, key, value)
            job.updated_at = time.time()

    def _post_upstream(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.upstream_base_url}{self.upstream_invoke_path}"
        raw = json.dumps(payload).encode("utf-8")
        request = Request(
            url,
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.upstream_timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            return {
                "errorCode": exc.code,
                "errorMsg": f"Upstream HTTP error: {exc.code}",
                "raw": body,
            }
        except URLError as exc:
            return {
                "errorCode": "UPSTREAM_UNREACHABLE",
                "errorMsg": f"Upstream unreachable: {exc.reason}",
            }


def create_app(provider: AsyncVlmWrapperProvider | None = None) -> FastAPI:
    wrapper = provider or AsyncVlmWrapperProvider(
        upstream_base_url=os.getenv("VLM_ASYNC_UPSTREAM_BASE_URL", "http://127.0.0.1:8081"),
        upstream_invoke_path=os.getenv("VLM_ASYNC_UPSTREAM_INVOKE_PATH", "/layout-parsing"),
        upstream_timeout_seconds=float(os.getenv("VLM_ASYNC_UPSTREAM_TIMEOUT_SECONDS", "120")),
    )
    app = FastAPI(title="Document VLM Async Wrapper Provider")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return wrapper.health()

    @app.post("/api/vlm/jobs")
    def submit_job(payload: dict[str, Any]) -> JSONResponse:
        result = wrapper.submit(payload)
        status_code = 202 if result.get("errorCode") in (0, "0") else 400
        return JSONResponse(status_code=status_code, content=result)

    @app.get("/api/vlm/jobs/{job_id}")
    def get_job(job_id: str) -> JSONResponse:
        result = wrapper.get_job(job_id)
        if result is None:
            return JSONResponse(
                status_code=404,
                content={
                    "errorCode": 404,
                    "errorMsg": f"Job not found: {job_id}",
                    "result": {
                        "job_id": job_id,
                        "status": "failed",
                        "progress": 1.0,
                        "result": {},
                        "error": {"code": "VLM_JOB_NOT_FOUND", "message": f"Job not found: {job_id}"},
                        "warnings": [],
                        "raw": {},
                    },
                },
            )
        return JSONResponse(status_code=200, content=result)

    return app


def _validate_submit_payload(payload: dict[str, Any]) -> dict[str, str] | None:
    if not str(payload.get("file") or "").strip():
        return {"code": "VLM_INVALID_INPUT", "message": "file is required."}
    try:
        file_type = int(payload.get("fileType"))
    except (TypeError, ValueError):
        return {"code": "VLM_INVALID_INPUT", "message": "fileType must be 0 or 1."}
    if file_type not in {0, 1}:
        return {"code": "VLM_INVALID_INPUT", "message": "fileType must be 0 or 1."}
    task = str(payload.get("task") or "summarize").strip().lower()
    if task not in SUPPORTED_TASKS:
        return {"code": "VLM_UNSUPPORTED_TASK", "message": f"Unsupported task: {task}"}
    if task == "qa" and not str(payload.get("question") or "").strip():
        return {"code": "VLM_INVALID_INPUT", "message": "question is required when task=qa."}
    return None


def _to_layout_payload(payload: dict[str, Any]) -> dict[str, Any]:
    mapped: dict[str, Any] = {
        "file": str(payload.get("file") or ""),
        "fileType": int(payload.get("fileType")),
        "outputFormat": "markdown",
        "includeTables": True,
        "includeLayout": True,
    }
    if payload.get("maxPages") is not None:
        mapped["maxPages"] = int(payload["maxPages"])
    return mapped


def _normalize_vlm_result(upstream_result: dict[str, Any], original_payload: dict[str, Any]) -> dict[str, Any]:
    markdown = _extract_markdown(upstream_result)
    task = str(original_payload.get("task") or "summarize").strip().lower()
    answers: list[dict[str, Any]] = []
    if task == "qa":
        answers.append(
            {
                "question": str(original_payload.get("question") or ""),
                "answer": markdown,
                "source": "layout-markdown",
            }
        )
    return {
        "summary": markdown,
        "sections": _derive_sections(upstream_result, markdown),
        "entities": [],
        "answers": answers,
        "evidence": _derive_evidence(upstream_result),
        "warnings": [] if markdown else ["Upstream provider returned empty markdown."],
        "raw": upstream_result,
    }


def _extract_markdown(result: dict[str, Any]) -> str:
    if isinstance(result.get("markdown"), str):
        return str(result.get("markdown") or "")
    pages = result.get("layoutParsingResults")
    if isinstance(pages, list):
        segments: list[str] = []
        for page in pages:
            if not isinstance(page, dict):
                continue
            markdown_obj = page.get("markdown")
            if isinstance(markdown_obj, dict) and isinstance(markdown_obj.get("text"), str):
                segments.append(str(markdown_obj.get("text") or ""))
            elif isinstance(markdown_obj, str):
                segments.append(markdown_obj)
            else:
                pruned = page.get("prunedResult")
                if isinstance(pruned, dict) and isinstance(pruned.get("markdown"), str):
                    segments.append(str(pruned.get("markdown") or ""))
        return "\n\n".join(segment for segment in segments if segment.strip())
    return str(result.get("text") or result.get("md") or "")


def _derive_sections(result: dict[str, Any], markdown: str) -> list[dict[str, Any]]:
    pages = result.get("layoutParsingResults")
    if isinstance(pages, list):
        sections: list[dict[str, Any]] = []
        for index, page in enumerate(pages, start=1):
            if not isinstance(page, dict):
                continue
            page_markdown = _extract_markdown({"layoutParsingResults": [page]}).strip()
            if page_markdown:
                sections.append({"title": f"Page {index}", "content": page_markdown})
        if sections:
            return sections
    return [{"title": "Document", "content": markdown}] if markdown else []


def _derive_evidence(result: dict[str, Any]) -> list[dict[str, Any]]:
    pages = result.get("layoutParsingResults")
    if not isinstance(pages, list):
        return []
    evidence: list[dict[str, Any]] = []
    for index, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            continue
        pruned = page.get("prunedResult")
        layout_count = 0
        table_count = 0
        if isinstance(pruned, dict):
            layouts = pruned.get("layouts")
            tables = pruned.get("table_res_list") or pruned.get("tables")
            layout_count = len(layouts) if isinstance(layouts, list) else 0
            table_count = len(tables) if isinstance(tables, list) else 0
        evidence.append({"page": index, "layout_count": layout_count, "table_count": table_count})
    return evidence


def _normalize_path(path: str, default: str) -> str:
    normalized = (path or "").strip() or default
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local async VLM wrapper provider.")
    parser.add_argument("--host", default=os.getenv("VLM_ASYNC_WRAPPER_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("VLM_ASYNC_WRAPPER_PORT", "8082")))
    parser.add_argument("--upstream-base-url", default=os.getenv("VLM_ASYNC_UPSTREAM_BASE_URL", "http://127.0.0.1:8081"))
    parser.add_argument("--upstream-invoke-path", default=os.getenv("VLM_ASYNC_UPSTREAM_INVOKE_PATH", "/layout-parsing"))
    parser.add_argument("--upstream-timeout", type=float, default=float(os.getenv("VLM_ASYNC_UPSTREAM_TIMEOUT_SECONDS", "120")))
    args = parser.parse_args(argv)

    provider = AsyncVlmWrapperProvider(
        upstream_base_url=args.upstream_base_url,
        upstream_invoke_path=args.upstream_invoke_path,
        upstream_timeout_seconds=args.upstream_timeout,
    )
    app = create_app(provider)

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
