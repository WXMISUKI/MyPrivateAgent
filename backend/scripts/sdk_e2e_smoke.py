"""Embedded SDK end-to-end smoke test with real LLM provider.

This script validates the full SDK execution loop with a real model call:
  AgentHarnessFacade.execute(model_name="doubao")
    → build_provider_model_step("doubao")
    → ExecutionLoopController
    → model.invoke() [real LLM]
    → governance trace captured

Usage:
    conda activate myenv
    python backend/scripts/sdk_e2e_smoke.py

Requires a configured LLM provider (Volcengine Ark API key or local Ollama).
"""

from __future__ import annotations

import json
import sys
import os

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent_framework.harness import AgentHarnessFacade
from agent_framework.runtime import AgentRunContext


def main() -> int:
    print("=" * 60)
    print("Embedded SDK E2E Smoke Test")
    print("=" * 60)

    # Step 1: Create facade
    print("\n[1/5] Creating AgentHarnessFacade...")
    facade = AgentHarnessFacade(name="smoke-test-agent", model_name="doubao")
    contract = facade.build_contract()
    print(f"  Agent: {contract['agent_name']}")
    print(f"  Tools registered: {contract['tool_registry_bridge']['registered_tool_count']}")

    # Step 2: Register a simple tool
    print("\n[2/5] Registering test tool...")
    facade.register_tool(
        {"name": "get_current_time", "description": "Get the current date and time"},
        handler=lambda args: "2026-06-14 12:00:00 UTC",
    )
    print("  Tool registered: get_current_time")

    # Step 3: Create a run
    print("\n[3/5] Creating run...")
    run = facade.run({"run_kind": "chat", "input": "What is the current time? Use the get_current_time tool."})
    run_id = run["run"]["run_id"]
    print(f"  Run ID: {run_id}")
    print(f"  State: {run['run']['state']}")

    # Step 4: Execute with real model
    print("\n[4/5] Executing with real LLM provider...")
    print("  (This may take a few seconds...)")

    try:
        result = facade.execute(
            run_id,
            model_name="doubao",
        )
    except Exception as exc:
        print(f"\n  ERROR: {type(exc).__name__}: {exc}")
        print("\n  This likely means the LLM provider is not configured.")
        print("  Check your .env for ARK_API_KEY or ensure Ollama is running.")
        return 1

    # Step 5: Validate governance trace
    print("\n[5/5] Validating governance trace...")
    run_data = result["run"]
    events = result["events"]

    print(f"  Final state: {run_data['state']}")
    print(f"  Stop reason: {run_data.get('stop_reason', 'N/A')}")
    print(f"  Iteration: {run_data['iteration']}")
    print(f"  Total events: {len(events)}")

    # State history
    states = [h["state"] for h in run_data.get("state_history", [])]
    print(f"  State history: {' → '.join(states)}")

    # Model step evidence
    model_evidence = run_data.get("metadata", {}).get("execution_model_step")
    if model_evidence:
        print(f"\n  Model Step Evidence:")
        print(f"    text: {model_evidence.get('text', '')[:100]}...")
        print(f"    model_name: {model_evidence.get('model_name', 'N/A')}")
        print(f"    finish_reason: {model_evidence.get('finish_reason', 'N/A')}")
    else:
        print("\n  WARNING: No model step evidence captured!")

    # Event summary
    event_kinds = {}
    for e in events:
        kind = e.get("status_kind") or e.get("type") or "unknown"
        event_kinds[kind] = event_kinds.get(kind, 0) + 1

    print(f"\n  Event Summary:")
    for kind, count in sorted(event_kinds.items()):
        print(f"    {kind}: {count}")

    # Validation
    errors = []
    if run_data["state"] != "done":
        errors.append(f"Expected state 'done', got '{run_data['state']}'")
    if "execution_loop_model_step_completed" not in event_kinds:
        errors.append("Missing execution_loop_model_step_completed event")
    if "execution_loop_done" not in event_kinds:
        errors.append("Missing execution_loop_done event")
    if model_evidence is None:
        errors.append("No model step evidence in metadata")

    print("\n" + "=" * 60)
    if errors:
        print("SMOKE TEST FAILED:")
        for err in errors:
            print(f"  ✗ {err}")
        return 1
    else:
        print("SMOKE TEST PASSED ✓")
        print("  The Embedded SDK path works end-to-end with a real LLM provider.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
