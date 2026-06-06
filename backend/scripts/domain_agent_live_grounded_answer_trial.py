from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.domain_agent_live_grounded_answer_trial_service import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PROVIDER_BASE_URL,
    DomainAgentLiveGroundedAnswerTrialService,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an explicit live provider-backed grounded-answer trial for a domain agent."
    )
    parser.add_argument("--agent-id", required=True, help="Domain agent id from backend/domain_agents/*/agent.yaml.")
    parser.add_argument("--query", required=True, help="Query to send to the external document RAG provider.")
    parser.add_argument("--domain", default=None, help="Optional grounding policy domain, such as refund.policy.")
    parser.add_argument(
        "--provider-base-url",
        default=os.getenv("KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL", DEFAULT_PROVIDER_BASE_URL),
        help="External knowledge provider base URL.",
    )
    parser.add_argument(
        "--provider-api-key",
        default=os.getenv("PROVIDER_API_KEY"),
        help="Optional provider API key. The value is not written to artifacts.",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Provider retrieve top_k.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.getenv("KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS", "5")),
        help="Provider HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=Path("docs/evals/multiturn"),
        help="Directory containing deterministic multi-turn eval scenarios.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for JSON and Markdown trial artifacts.",
    )
    parser.add_argument("--pretty", action="store_true", help="Print the full report JSON.")
    args = parser.parse_args()

    report = DomainAgentLiveGroundedAnswerTrialService().export_trial(
        output_dir=args.output_dir,
        agent_id=args.agent_id,
        query=args.query,
        domain=args.domain,
        provider_base_url=args.provider_base_url,
        provider_api_key=args.provider_api_key,
        top_k=args.top_k,
        timeout_seconds=args.timeout_seconds,
        eval_dir=args.eval_dir,
    )
    print(f"Domain agent live grounded-answer trial JSON ready: {report.json_path}")
    print(f"Domain agent live grounded-answer trial Markdown ready: {report.markdown_path}")
    print(f"Status: {report.live_trial_status}")
    print(f"Reason: {report.reason_code}")
    if args.pretty:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
