from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.capability_runtime.knowledge_provider_trial import (
    DEFAULT_PROVIDER_BASE_URL,
    DEFAULT_TRIAL_QUERY,
    export_knowledge_provider_trial_outcome,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the MyPrivateAgent repo-side unified knowledge provider trial outcome."
    )
    parser.add_argument(
        "--provider-base-url",
        default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_URL", DEFAULT_PROVIDER_BASE_URL),
        help="Unified knowledge provider base URL.",
    )
    parser.add_argument(
        "--provider-api-key",
        default=os.getenv("PROVIDER_API_KEY"),
        help="Optional provider API key. The value is not written to artifacts.",
    )
    parser.add_argument(
        "--provider-readiness-path",
        type=Path,
        default=Path(os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_READINESS_PATH"))
        if os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_READINESS_PATH")
        else None,
        help="Optional provider-side Phase 24 document RAG readiness JSON path.",
    )
    parser.add_argument(
        "--query",
        default=os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_TRIAL_QUERY", DEFAULT_TRIAL_QUERY),
        help="RAG retrieve query used by the trial.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.getenv("UNIFIED_KNOWLEDGE_PROVIDER_TIMEOUT_SECONDS", "5")),
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/integration/unified-knowledge-provider-trial"),
        help="Directory for JSON and Markdown outcome artifacts.",
    )
    args = parser.parse_args()

    outcome = export_knowledge_provider_trial_outcome(
        output_dir=args.output_dir,
        provider_base_url=args.provider_base_url,
        provider_api_key=args.provider_api_key,
        provider_readiness_path=args.provider_readiness_path,
        query=args.query,
        timeout_seconds=args.timeout_seconds,
    )
    print(f"Unified knowledge provider trial outcome JSON ready: {outcome.json_path}")
    print(f"Unified knowledge provider trial outcome Markdown ready: {outcome.markdown_path}")
    print(f"Status: {outcome.status}")
    print(f"Decision: {outcome.decision}")


if __name__ == "__main__":
    main()
