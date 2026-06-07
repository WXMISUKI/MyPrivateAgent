from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.capability_runtime.document_rag_upload_to_use_loop import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PARSE_MODE,
    DEFAULT_PROVIDER_PYTHON,
    DEFAULT_PROVIDER_REPO,
    DEFAULT_PROVIDER_BASE_URL,
    DEFAULT_QUERY,
    DEFAULT_SOURCE_ID,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_TITLE,
    DEFAULT_TOP_K,
    export_document_rag_upload_to_use_loop,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run local MyPrivateAgent document RAG upload-to-use loop.",
    )
    parser.add_argument("--document-path", type=Path, required=True)
    parser.add_argument("--parse-mode", default=DEFAULT_PARSE_MODE, choices=["ocr", "layout"])
    parser.add_argument("--source-id", default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_SOURCE_ID", DEFAULT_SOURCE_ID))
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--provider-base-url", default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_URL", DEFAULT_PROVIDER_BASE_URL))
    parser.add_argument("--provider-api-key", default=os.getenv("PROVIDER_API_KEY"))
    parser.add_argument("--knowledge-provider-repo", type=Path, default=DEFAULT_PROVIDER_REPO)
    parser.add_argument("--provider-python", default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_PYTHON", DEFAULT_PROVIDER_PYTHON))
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--handoff-only", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    report = export_document_rag_upload_to_use_loop(
        document_path=args.document_path,
        output_dir=args.output_dir,
        parse_mode=args.parse_mode,
        source_id=args.source_id,
        title=args.title,
        query=args.query,
        provider_base_url=args.provider_base_url,
        provider_api_key=args.provider_api_key,
        provider_repo_path=args.knowledge_provider_repo,
        provider_python=args.provider_python,
        top_k=args.top_k,
        timeout_seconds=args.timeout_seconds,
        max_pages=args.max_pages,
        handoff_only=args.handoff_only,
    )
    print(f"Document RAG upload-to-use loop JSON ready: {report.json_path}")
    print(f"Document RAG upload-to-use loop Markdown ready: {report.markdown_path}")
    print(f"Decision: {report.decision}")
    print(f"Reason: {report.reason_code}")
    return 0 if report.decision != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
