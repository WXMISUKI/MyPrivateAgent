from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.capability_runtime.local_knowledge_base_user_loop import (
    DEFAULT_CORPUS_TRIAL_JSON_PATH,
    DEFAULT_EXPLICIT_API_SMOKE_JSON_PATH,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE_ID,
    export_local_knowledge_base_user_loop,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export the MyPrivateAgent local knowledge base user-loop package.",
    )
    parser.add_argument("--corpus-trial-json-path", type=Path, default=DEFAULT_CORPUS_TRIAL_JSON_PATH)
    parser.add_argument("--explicit-api-smoke-json-path", type=Path, default=DEFAULT_EXPLICIT_API_SMOKE_JSON_PATH)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = export_local_knowledge_base_user_loop(
        output_dir=args.output_dir,
        corpus_trial_json_path=args.corpus_trial_json_path,
        explicit_api_smoke_json_path=args.explicit_api_smoke_json_path,
        source_id=args.source_id,
    )
    print(f"Local knowledge base user-loop JSON ready: {report.json_path}")
    print(f"Local knowledge base user-loop Markdown ready: {report.markdown_path}")
    print(f"Decision: {report.decision}")
    print(f"Reason: {report.reason_code}")
    if args.pretty:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0 if report.decision != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
