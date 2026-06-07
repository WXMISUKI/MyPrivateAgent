from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.company_profile_explicit_api_local_smoke_service import (
    DEFAULT_AGENT_ID,
    DEFAULT_DOMAIN,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_QUERY,
    export_company_profile_explicit_api_local_smoke,
)
from backend.services.domain_agent_live_grounded_answer_trial_service import DEFAULT_PROVIDER_BASE_URL


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a local smoke for the explicit company-profile grounded-answer API.",
    )
    parser.add_argument("--provider-base-url", default=os.getenv("KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL", DEFAULT_PROVIDER_BASE_URL))
    parser.add_argument("--provider-api-key", default=os.getenv("PROVIDER_API_KEY"))
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=float, default=float(os.getenv("KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS", "5")))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = export_company_profile_explicit_api_local_smoke(
        output_dir=args.output_dir,
        provider_base_url=args.provider_base_url,
        provider_api_key=args.provider_api_key,
        agent_id=args.agent_id,
        domain=args.domain,
        query=args.query,
        top_k=args.top_k,
        timeout_seconds=args.timeout_seconds,
    )
    print(f"Company profile explicit API local smoke JSON ready: {report.json_path}")
    print(f"Company profile explicit API local smoke Markdown ready: {report.markdown_path}")
    print(f"Decision: {report.decision}")
    print(f"Reason: {report.reason_code}")
    if args.pretty:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0 if report.decision != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
