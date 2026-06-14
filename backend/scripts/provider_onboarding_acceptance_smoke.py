"""Generate read-only provider onboarding acceptance evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.capability_runtime.provider_onboarding_acceptance_gate import (  # noqa: E402
    ProviderOnboardingAcceptanceGate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--onboarding-id", help="Known provider onboarding id.")
    group.add_argument("--provider-id", help="Known service provider id.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON evidence.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    gate = ProviderOnboardingAcceptanceGate()
    try:
        if args.onboarding_id:
            payload = gate.evaluate_onboarding(args.onboarding_id)
        else:
            payload = gate.evaluate_provider(args.provider_id)
    except LookupError as exc:
        payload = {
            "contract_version": "provider-onboarding-acceptance-gate-v1",
            "decision": "blocked",
            "blockers": [
                {
                    "code": "PROVIDER_ONBOARDING_NOT_FOUND",
                    "message": str(exc),
                }
            ],
        }
    print(json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if payload.get("decision") == "accepted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
