"""Local smoke runner for OCR/Layout real-file acceptance.

Usage examples:
  python backend/scripts/ocr_layout_local_smoke.py --ocr-base-url http://127.0.0.1:8080 --layout-base-url http://127.0.0.1:8081 --samples-dir D:\\AI\\ocr
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests


@dataclass
class ProbeResult:
    name: str
    path: str
    media_type: str
    ok: bool
    capability: str
    detail: str
    data: dict[str, Any]


def _encode_file_base64(path: Path) -> str:
    raw = path.read_bytes()
    return base64.b64encode(raw).decode("utf-8")


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
    response.raise_for_status()
    return response.json()


def _get_json(url: str, timeout: float = 30.0) -> dict[str, Any]:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _to_bool(result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "response is not a dict"
    if "errorCode" in result and result.get("errorCode") not in (0, "0", None):
        return False, str(result.get("errorMsg") or "provider returned errorCode")
    return True, "ok"


def _run_ocr(file_path: Path, base_url: str) -> ProbeResult:
    payload = {
        "file": _encode_file_base64(file_path),
        "fileType": 0 if file_path.suffix.lower() == ".pdf" else 1,
        "filename": file_path.name,
        "visualize": False,
    }
    result = _post_json(f"{base_url}/ocr", payload, timeout=120.0)
    body = {}
    if isinstance(result.get("result"), dict):
        body = result["result"]
    ok, reason = _to_bool(result)
    if ok:
        ocr_results = body.get("ocrResults") or []
        text = "\n".join(
            str(item.get("prunedResult", {}).get("rec_texts", [""])[0])
            for item in ocr_results
            if isinstance(item, dict)
        )
        return ProbeResult(
            name=file_path.name,
            path=str(file_path),
            media_type=_media_type(file_path),
            ok=True,
            capability="document.ocr.extract",
            detail=reason,
            data={"text": text, "ocr_results": ocr_results, "raw": body},
        )
    return ProbeResult(
        name=file_path.name,
        path=str(file_path),
        media_type=_media_type(file_path),
        ok=False,
        capability="document.ocr.extract",
        detail=reason,
        data={"raw": result},
    )


def _run_layout(file_path: Path, base_url: str) -> ProbeResult:
    payload = {
        "file": _encode_file_base64(file_path),
        "fileType": 0 if file_path.suffix.lower() == ".pdf" else 1,
        "filename": file_path.name,
        "outputFormat": "markdown",
        "includeTables": True,
        "includeLayout": True,
    }
    result = _post_json(f"{base_url}/layout-parsing", payload, timeout=120.0)
    body = {}
    if isinstance(result.get("result"), dict):
        body = result["result"]
    ok, reason = _to_bool(result)
    if ok:
        layout_results = body.get("layoutParsingResults") or []
        markdown = str(body.get("markdown") or body.get("md") or "")
        if not markdown and isinstance(layout_results, list):
            markdown_parts: list[str] = []
            for page in layout_results:
                if not isinstance(page, dict):
                    continue
                markdown_obj = page.get("markdown")
                if isinstance(markdown_obj, dict):
                    markdown_parts.append(str(markdown_obj.get("text") or ""))
                if isinstance(markdown_obj, str):
                    markdown_parts.append(markdown_obj)
            markdown = "\n\n".join([item for item in markdown_parts if item.strip()])
        return ProbeResult(
            name=file_path.name,
            path=str(file_path),
            media_type=_media_type(file_path),
            ok=True,
            capability="document.layout.parse",
            detail=reason,
            data={"markdown": markdown, "pages": layout_results if isinstance(layout_results, list) else [], "raw": body},
        )
    return ProbeResult(
        name=file_path.name,
        path=str(file_path),
        media_type=_media_type(file_path),
        ok=False,
        capability="document.layout.parse",
        detail=reason,
        data={"raw": result},
    )


def _collect_samples(samples_dir: Path) -> list[Path]:
    extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    files = [p for p in sorted(samples_dir.glob("*")) if p.is_file() and p.suffix.lower() in extensions]
    if not files:
        raise FileNotFoundError(f"no sample files found in {samples_dir}")
    return files


def _print_report(results: list[ProbeResult]) -> None:
    print("# OCR/Layout Acceptance Summary")
    print()
    for item in results:
        status = "PASS" if item.ok else "FAIL"
        print(f"[{status}] {item.capability} - {item.name}")
        print(f"  - media_type: {item.media_type}")
        if item.detail and not item.ok:
            print(f"  - reason: {item.detail}")
        elif item.ok and isinstance(item.data, dict):
            extra = [
                f"text_len={len(str(item.data.get('text', '')))}" if item.capability == "document.ocr.extract" else "",
                f"markdown_len={len(str(item.data.get('markdown', '')))}" if item.capability == "document.layout.parse" else "",
            ]
            extra = [entry for entry in extra if entry]
            if extra:
                print("  - " + " ".join(extra))
    print()
    print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))


def _safe_dump(path: Path, results: list[ProbeResult]) -> None:
    payload = [r.__dict__ for r in results]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run OCR/Layout smoke against local PaddleOCR services.")
    parser.add_argument("--ocr-base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--layout-base-url", default="http://127.0.0.1:8081")
    parser.add_argument("--samples-dir", default="D:/AI/ocr")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--report", default="", help="Optional JSON report path, e.g. docs/guides/layout_acceptance_report_2026-06-xx.json")
    args = parser.parse_args(argv)

    samples_dir = Path(args.samples_dir)
    if not samples_dir.exists():
        raise FileNotFoundError(f"samples dir not found: {samples_dir}")

    # preflight health check
    _get_json(f"{args.ocr_base_url}/health", timeout=args.timeout)
    _get_json(f"{args.layout_base_url}/health", timeout=args.timeout)

    results: list[ProbeResult] = []
    for sample in _collect_samples(samples_dir):
        results.append(_run_ocr(sample, args.ocr_base_url.rstrip("/")))
        results.append(_run_layout(sample, args.layout_base_url.rstrip("/")))

    _print_report(results)
    if args.report:
        _safe_dump(Path(args.report), results)

    failures = [result for result in results if not result.ok]
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI surface
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
