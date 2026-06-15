"""Weather SDK Agent — Reference domain agent using the Embedded SDK path.

This example demonstrates how a domain project uses MyPrivateAgent's
Embedded SDK to build an agent with:

  1. Tool registration via `AgentHarnessFacade.register_tool()`
  2. Real LLM calls via `build_provider_model_step()`
  3. Governance trace capture through the execution loop
  4. Tool execution through the tool_executor seam

Usage:

    # With real LLM provider (requires ARK_API_KEY or Ollama):
    conda activate myenv
    python examples/weather_sdk_agent.py

    # The agent will:
    #   - Register weather query tools
    #   - Call the LLM to understand the user's question
    #   - Execute tools to fetch weather data
    #   - Generate a final response with the tool results
    #   - Print the full governance trace

Architecture:

    User input
      → AgentHarnessFacade.execute(model_name="doubao")
        → build_provider_model_step("doubao")
          → ExecutionLoopController
            → planning
            → generating: model.invoke() → LLM generates response
            → generating: tool_policy → tool_executor → weather tool runs
            → observing: reflector (optional)
            → finalizing: reviewer (optional)
            → done
      → Governance trace: events, state history, tool results

Domain projects can:
  - Copy this file as a starting point
  - Replace mock tools with real API calls
  - Add more tools for their domain
  - Customize the system prompt
  - Add reviewer/reflector for quality gates
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.agent_framework.harness import AgentHarnessFacade
from backend.agent_framework.execution_loop import ExecutionModelStepResult


# ============================================================
# Domain Tools — Replace these with real API calls
# ============================================================

def query_weather(args: dict) -> str:
    """Query current weather for a city. Replace with real API call."""
    city = args.get("city", "unknown")
    # Mock weather data — replace with real API (e.g., OpenWeatherMap, QWeather)
    mock_data = {
        "beijing": {"temp": 28, "condition": "晴", "humidity": 45, "wind": "北风3级"},
        "shanghai": {"temp": 32, "condition": "多云", "humidity": 65, "wind": "东南风2级"},
        "guangzhou": {"temp": 35, "condition": "雷阵雨", "humidity": 80, "wind": "南风4级"},
        "shenzhen": {"temp": 34, "condition": "阵雨", "humidity": 78, "wind": "西南风3级"},
    }
    city_lower = city.lower()
    data = mock_data.get(city_lower, {"temp": 25, "condition": "未知", "humidity": 50, "wind": "微风"})
    return json.dumps({
        "city": city,
        "temperature": f"{data['temp']}°C",
        "condition": data["condition"],
        "humidity": f"{data['humidity']}%",
        "wind": data["wind"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }, ensure_ascii=False)


def query_forecast(args: dict) -> str:
    """Query weather forecast for a city. Replace with real API call."""
    city = args.get("city", "unknown")
    days = int(args.get("days", 3))
    # Mock forecast data — replace with real API
    forecast = []
    for i in range(min(days, 7)):
        forecast.append({
            "date": f"2026-06-{15 + i}",
            "temp_high": 30 + i,
            "temp_low": 22 + i,
            "condition": ["晴", "多云", "阵雨", "雷阵雨"][i % 4],
        })
    return json.dumps({
        "city": city,
        "forecast": forecast,
    }, ensure_ascii=False)


# ============================================================
# Agent Setup
# ============================================================

def create_weather_agent() -> AgentHarnessFacade:
    """Create and configure the weather SDK agent.

    This function demonstrates the standard pattern for creating
    a domain agent with the Embedded SDK:

    1. Create AgentHarnessFacade with agent name and default model
    2. Register domain tools with handlers
    3. Return the configured facade
    """
    facade = AgentHarnessFacade(
        name="weather-agent",
        model_name="doubao",  # Default model, can be overridden at execute()
    )

    # Register weather tools
    facade.register_tool(
        {
            "name": "query_weather",
            "description": "查询指定城市的当前天气信息。参数：city (城市名称)",
        },
        handler=query_weather,
    )

    facade.register_tool(
        {
            "name": "query_forecast",
            "description": "查询指定城市的天气预报。参数：city (城市名称), days (预报天数，默认3天)",
        },
        handler=query_forecast,
    )

    return facade


# ============================================================
# Main Entry Point
# ============================================================

def main() -> int:
    print("=" * 60)
    print("Weather SDK Agent — Reference Domain Agent")
    print("=" * 60)
    print()
    print("This example demonstrates how to build a domain agent")
    print("using MyPrivateAgent's Embedded SDK path.")
    print()

    # Step 1: Create the agent
    print("[1/4] Creating weather agent...")
    facade = create_weather_agent()
    contract = facade.build_contract()
    print(f"  Agent: {contract['agent_name']}")
    print(f"  Tools: {contract['tool_registry_bridge']['registered_tool_names']}")

    # Step 2: Create a run
    user_input = "北京今天天气怎么样？"
    print(f"\n[2/4] Creating run with input: {user_input}")
    run = facade.run({
        "run_kind": "chat",
        "input": user_input,
        "metadata": {
            "system_prompt": (
                "你是一个天气助手。用户会问你关于天气的问题。"
                "请使用提供的工具查询天气信息，然后用中文回答用户。"
                "回答要简洁、友好。"
            ),
        },
    })
    run_id = run["run"]["run_id"]
    print(f"  Run ID: {run_id}")

    # Step 3: Execute with real LLM
    print("\n[3/4] Executing with LLM provider...")
    print("  (This may take a few seconds...)")

    try:
        result = facade.execute(run_id, model_name="doubao")
    except Exception as exc:
        print(f"\n  ERROR: {type(exc).__name__}: {exc}")
        print("\n  This likely means the LLM provider is not configured.")
        print("  Check your .env for ARK_API_KEY or ensure Ollama is running.")
        return 1

    # Step 4: Display results
    print("\n[4/4] Results:")
    run_data = result["run"]
    events = result["events"]

    print(f"  State: {run_data['state']}")
    print(f"  Iteration: {run_data['iteration']}")

    # Model output
    model_evidence = run_data.get("metadata", {}).get("execution_model_step")
    if model_evidence:
        print(f"\n  Model Output:")
        print(f"    {model_evidence.get('text', '')[:200]}")

    # Tool results
    tool_events = [e for e in events if e.get("status_kind") == "tool_result"]
    if tool_events:
        print(f"\n  Tool Executions:")
        for te in tool_events:
            print(f"    Tool: {te.get('tool_name', 'N/A')}")
            print(f"    Result: {te.get('result', '')[:100]}")

    # State history
    states = [h["state"] for h in run_data.get("state_history", [])]
    print(f"\n  State History: {' → '.join(states)}")

    # Event summary
    event_kinds = {}
    for e in events:
        kind = e.get("status_kind") or e.get("type") or "unknown"
        event_kinds[kind] = event_kinds.get(kind, 0) + 1
    print(f"\n  Events: {len(events)} total")
    for kind, count in sorted(event_kinds.items()):
        print(f"    {kind}: {count}")

    print("\n" + "=" * 60)
    if run_data["state"] == "done":
        print("SUCCESS ✓ — The SDK path works end-to-end.")
    else:
        print(f"PARTIAL — Run ended with state: {run_data['state']}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
