from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.capability_runtime.document_rag_local_readiness import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_OCR_PROFILE,
    DEFAULT_PROVIDER_BASE_URL,
    DEFAULT_PROVIDER_PYTHON,
    DEFAULT_PROVIDER_REPO,
    DEFAULT_SOURCE_ID,
    DEFAULT_TIMEOUT_SECONDS,
    OCR_CAPABILITY_PROVIDER_BASE_URL,
    OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS,
    export_document_rag_local_readiness,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check local readiness for MyPrivateAgent document RAG trials.",
    )
    parser.add_argument("--ocr-base-url", default=os.getenv("OCR_CAPABILITY_PROVIDER_BASE_URL", OCR_CAPABILITY_PROVIDER_BASE_URL))
    parser.add_argument("--ocr-profile", default=os.getenv("OCR_CAPABILITY_PROVIDER_PROFILE", DEFAULT_OCR_PROFILE), choices=["cpu", "gpu", "unknown"])
    parser.add_argument(
        "--ocr-timeout-seconds",
        type=float,
        default=float(os.getenv("OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS", OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS)),
    )
    parser.add_argument("--provider-base-url", default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_URL", DEFAULT_PROVIDER_BASE_URL))
    parser.add_argument("--source-id", default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_SOURCE_ID", DEFAULT_SOURCE_ID))
    parser.add_argument("--knowledge-provider-repo", type=Path, default=Path(os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_REPO", str(DEFAULT_PROVIDER_REPO))))
    parser.add_argument("--provider-python", default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_PYTHON", DEFAULT_PROVIDER_PYTHON))
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    report = export_document_rag_local_readiness(
        output_dir=args.output_dir,
        ocr_base_url=args.ocr_base_url,
        ocr_profile=args.ocr_profile,
        ocr_timeout_seconds=args.ocr_timeout_seconds,
        provider_base_url=args.provider_base_url,
        source_id=args.source_id,
        provider_repo_path=args.knowledge_provider_repo,
        provider_python=args.provider_python,
        timeout_seconds=args.timeout_seconds,
    )
    print(f"Document RAG local readiness JSON ready: {report.json_path}")
    print(f"Document RAG local readiness Markdown ready: {report.markdown_path}")
    print(f"Decision: {report.decision}")
    print(f"Reason: {report.reason_code}")
    return 0 if report.decision != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
