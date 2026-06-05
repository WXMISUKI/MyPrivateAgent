from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.capability_runtime.knowledge_provider_integration_closure import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_TRIAL_OUTCOME_PATH,
    export_knowledge_provider_integration_closure,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the Phase 20 unified knowledge provider integration closure decision."
    )
    parser.add_argument(
        "--trial-outcome-path",
        type=Path,
        default=DEFAULT_TRIAL_OUTCOME_PATH,
        help="Path to the Phase 19 trial outcome JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for JSON and Markdown closure artifacts.",
    )
    args = parser.parse_args()

    closure = export_knowledge_provider_integration_closure(
        trial_outcome_path=args.trial_outcome_path,
        output_dir=args.output_dir,
    )
    print(f"Unified knowledge provider integration closure JSON ready: {closure.json_path}")
    print(f"Unified knowledge provider integration closure Markdown ready: {closure.markdown_path}")
    print(f"Decision: {closure.decision}")
    print(f"Evidence chain status: {closure.evidence_chain_status}")
    print(f"Recommended next line: {closure.recommended_next_line}")


if __name__ == "__main__":
    main()
