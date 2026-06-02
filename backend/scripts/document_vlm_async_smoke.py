"""Async VLM smoke runner against MyPrivateAgent capability invoke contract."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


TERMINAL_STATUSES = {"succeeded", "failed", "expired"}


@dataclass
class ProbeResult:
    name: str
    path: str
    media_type: str
    ok: bool
    detail: str
    result: dict[str, Any]


def _encode_file_base64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def _media_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext == ".png":
        return "image/png"
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "application/octet-stream"


def _post_json(url: str, payload: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
    response = requests.post(url, json=payload, timeout=timeout)
    try:
        data = response.json()
    except ValueError:
        response.raise_for_status()
        raise
    if response.status_code >= 400:
        data["_http_status"] = response.status_code
    return data


def _get_json(url: str, timeout: float = 30.0) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout)
    try:
        data = response.json()
    except ValueError:
        response.raise_for_status()
        raise
    if response.status_code >= 400:
        data["_http_status"] = response.status_code
    return data


def _to_bool(result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "response is not a dict"
    if not result.get("ok"):
        error = result.get("error") or {}
        return False, str(error.get("message") or error.get("code") or "capability returned failure")
    return True, "ok"


def _collect_samples(samples_dir: Path) -> list[Path]:
    extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    files = [p for p in sorted(samples_dir.glob("*")) if p.is_file() and p.suffix.lower() in extensions]
    if not files:
        raise FileNotFoundError(f"no sample files found in {samples_dir}")
    return files


def _require_async_capability_ready(runtime_base_url: str, timeout: float) -> None:
    capabilities_payload = _get_json(f"{runtime_base_url.rstrip('/')}/api/capabilities", timeout=timeout)
    capabilities = capabilities_payload.get("capabilities") if isinstance(capabilities_payload, dict) else []
    if not isinstance(capabilities, list):
        raise RuntimeError("capability list response does not contain capabilities array")
    capability = next(
        (
            item
            for item in capabilities
            if isinstance(item, dict) and item.get("capability_id") == "document.vlm.parse.async"
        ),
        None,
    )
    if capability is None:
        raise RuntimeError("document.vlm.parse.async is not registered. Check ENABLE_VLM_CAPABILITY_PROVIDER=true.")
    status = str(capability.get("status") or "unknown")
    if status != "ready":
        metadata = capability.get("metadata") if isinstance(capability.get("metadata"), dict) else {}
        error = capability.get("error") if isinstance(capability.get("error"), dict) else {}
        raise RuntimeError(
            "document.vlm.parse.async is not ready: "
            f"status={status}; "
            f"base_url={metadata.get('provider_base_url') or ''}; "
            f"submit_path={metadata.get('provider_invoke_path') or ''}; "
            f"error_code={error.get('code') or ''}; "
            f"reason={capability.get('reason') or error.get('message') or ''}"
        )


def _submit_job(runtime_base_url: str, sample: Path, timeout: float, task: str, max_pages: int | None) -> tuple[dict[str, Any], str]:
    payload = {
        "operation": "submit",
        "file_base64": _encode_file_base64(sample),
        "media_type": _media_type(sample),
        "filename": sample.name,
        "task": task,
    }
    if max_pages is not None:
        payload["max_pages"] = max_pages

    endpoint = f"{runtime_base_url.rstrip('/')}/api/capabilities/document.vlm.parse.async/invoke"
    response = _post_json(endpoint, payload, timeout=timeout)
    return response, payload["filename"]


def _query_status(runtime_base_url: str, job_id: str, timeout: float) -> dict[str, Any]:
    endpoint = f"{runtime_base_url.rstrip('/')}/api/capabilities/document.vlm.parse.async/invoke"
    response = _post_json(
        endpoint,
        {"operation": "status", "job_id": job_id},
        timeout=timeout,
    )
    return response


def _poll_status(
    runtime_base_url: str,
    job_id: str,
    *,
    poll_timeout: float = 60.0,
    poll_interval: float = 1.0,
    timeout: float = 120.0,
) -> dict[str, Any]:
    deadline = time.perf_counter() + poll_timeout
    polls: list[dict[str, Any]] = []

    while time.perf_counter() < deadline:
        status_response = _query_status(runtime_base_url, job_id, timeout=timeout)
        polls.append(status_response)
        ok, reason = _to_bool(status_response)
        if not ok:
            return {
                "ok": False,
                "job_id": job_id,
                "polls": polls,
                "detail": reason,
                "result": status_response,
            }

        result = status_response.get("result") or {}
        status = str(result.get("status") or "").lower()
        if status in TERMINAL_STATUSES:
            return {
                "ok": status == "succeeded",
                "job_id": job_id,
                "polls": polls,
                "detail": f"terminal status: {status}",
                "result": result,
            }
        time.sleep(max(0.1, float(poll_interval)))

    return {
        "ok": False,
        "job_id": job_id,
        "polls": polls,
        "detail": f"poll timeout after {poll_timeout}s",
        "result": {},
    }


def _run_sample(runtime_base_url: str, sample: Path, args: argparse.Namespace) -> ProbeResult:
    media_type = _media_type(sample)
    submit_start = time.perf_counter()
    submit_response = _submit_job(runtime_base_url, sample, timeout=args.timeout, task=args.task, max_pages=args.max_pages)
    if not isinstance(submit_response, tuple) or not submit_response[0].get("ok"):
        submit_result = submit_response[0] if isinstance(submit_response, tuple) else {}
        return ProbeResult(
            name=sample.name,
            path=str(sample),
            media_type=media_type,
            ok=False,
            detail=str((submit_result.get("error") or {}).get("message") if isinstance(submit_result, dict) else "submit failed"),
            result={"submit_response": submit_result, "duration_ms": round((time.perf_counter() - submit_start) * 1000, 2)},
        )

    submit_payload, _ = submit_response
    submit_result = submit_payload
    result_payload = submit_result.get("result") or {}
    job_id = str(result_payload.get("job_id") or "").strip()
    if not job_id:
        return ProbeResult(
            name=sample.name,
            path=str(sample),
            media_type=media_type,
            ok=False,
            detail="submit response missing job_id",
            result={"submit_response": submit_result, "duration_ms": round((time.perf_counter() - submit_start) * 1000, 2)},
        )

    status_poll = _poll_status(
        runtime_base_url,
        job_id,
        poll_timeout=args.poll_timeout,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )
    return ProbeResult(
        name=sample.name,
        path=str(sample),
        media_type=media_type,
        ok=bool(status_poll.get("ok")),
        detail=str(status_poll.get("detail") or ""),
        result={
            "submit_response": submit_result,
            "submit_duration_ms": round((time.perf_counter() - submit_start) * 1000, 2),
            "status_poll": status_poll,
            "poll_count": len(status_poll.get("polls") or []),
            "status": str((status_poll.get("result") or {}).get("status") or ""),
            "progress": (status_poll.get("result") or {}).get("progress", 0),
            "result": status_poll.get("result") or {},
        },
    )


def _print_report(results: list[ProbeResult]) -> None:
    print("# VLM Async Acceptance Summary")
    print()
    for item in results:
        status = "PASS" if item.ok else "FAIL"
        print(f"[{status}] document.vlm.parse.async - {item.name}")
        print(f"  - media_type: {item.media_type}")
        print(f"  - detail: {item.detail}")
        if item.ok:
            print(f"  - status: {item.result.get('status')} progress: {item.result.get('progress')}")
        print(f"  - polls: {item.result.get('poll_count', 0)}")
    print()
    print(json.dumps([_compact_result(r) for r in results], ensure_ascii=False, indent=2))


def _safe_dump(path: Path, results: list[ProbeResult], *, include_raw: bool = False) -> None:
    payload = [r.__dict__ for r in results] if include_raw else [_compact_result(result) for result in results]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _compact_result(result: ProbeResult) -> dict[str, Any]:
    job_result = result.result.get("result") if isinstance(result.result.get("result"), dict) else {}
    normalized_result = job_result.get("result") if isinstance(job_result.get("result"), dict) else {}
    status_poll = result.result.get("status_poll") if isinstance(result.result.get("status_poll"), dict) else {}
    return {
        "name": result.name,
        "path": result.path,
        "media_type": result.media_type,
        "ok": result.ok,
        "detail": result.detail,
        "job_id": str(status_poll.get("job_id") or (result.result.get("submit_response", {}).get("result", {}) or {}).get("job_id") or ""),
        "status": str(result.result.get("status") or ""),
        "progress": result.result.get("progress", 0),
        "poll_count": result.result.get("poll_count", 0),
        "submit_duration_ms": result.result.get("submit_duration_ms"),
        "summary_length": len(str(normalized_result.get("summary") or "")),
        "section_count": len(normalized_result.get("sections") or []) if isinstance(normalized_result.get("sections"), list) else 0,
        "evidence_count": len(normalized_result.get("evidence") or []) if isinstance(normalized_result.get("evidence"), list) else 0,
        "warnings": normalized_result.get("warnings") if isinstance(normalized_result.get("warnings"), list) else [],
        "error": job_result.get("error") if isinstance(job_result.get("error"), dict) else {},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run async VLM capability smoke against capability runtime contract.")
    parser.add_argument("--runtime-base-url", default="http://127.0.0.1:8000", help="MyPrivateAgent capability runtime base URL.")
    parser.add_argument("--samples-dir", default="D:/AI/ocr")
    parser.add_argument("--task", default="summarize", choices=["summarize", "extract_fields", "chart_understanding", "qa"])
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--poll-timeout", type=float, default=60.0)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--report", default="", help="Optional JSON report path, e.g. docs/guides/vlm_async_acceptance_report.json")
    parser.add_argument("--include-raw-report", action="store_true", help="Include full provider raw payloads in --report output.")
    args = parser.parse_args(argv)

    # preflight
    _get_json(f"{args.runtime_base_url.rstrip('/')}/api/capabilities/heartbeat", timeout=args.timeout)
    _require_async_capability_ready(args.runtime_base_url, args.timeout)
    samples_dir = Path(args.samples_dir)
    if not samples_dir.exists():
        raise FileNotFoundError(f"samples dir not found: {samples_dir}")

    results = [_run_sample(args.runtime_base_url, sample, args) for sample in _collect_samples(samples_dir)]
    _print_report(results)

    failures = [result for result in results if not result.ok]
    if args.report:
        _safe_dump(Path(args.report), results, include_raw=args.include_raw_report)
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI surface
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
