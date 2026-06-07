from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.capability_runtime.local_knowledge_provider_corpus_trial import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PROVIDER_BASE_URL,
    DEFAULT_SOURCE_ID,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_TOP_K,
    export_local_knowledge_provider_corpus_trial,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export a MyPrivateAgent caller-side local knowledge provider corpus trial.",
    )
    parser.add_argument(
        "--provider-base-url",
        default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_URL", DEFAULT_PROVIDER_BASE_URL),
    )
    parser.add_argument(
        "--provider-api-key",
        default=os.getenv("PROVIDER_API_KEY"),
        help="Optional provider API key. The value is not written to artifacts.",
    )
    parser.add_argument("--source-id", default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_SOURCE_ID", DEFAULT_SOURCE_ID))
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--case-file", type=Path, default=None)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    trial = export_local_knowledge_provider_corpus_trial(
        output_dir=args.output_dir,
        provider_base_url=args.provider_base_url,
        provider_api_key=args.provider_api_key,
        source_id=args.source_id,
        case_file=args.case_file,
        top_k=args.top_k,
        timeout_seconds=args.timeout_seconds,
    )
    print(f"Local knowledge provider corpus trial JSON ready: {trial.json_path}")
    print(f"Local knowledge provider corpus trial Markdown ready: {trial.markdown_path}")
    print(f"Decision: {trial.decision}")
    print(f"Reason: {trial.reason_code}")
    return 0 if trial.decision != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
