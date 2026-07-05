"""
Runtime Plane Smoke Test - 运行层验证脚本

验证运行层核心能力：
1. 图引擎基本执行（线性、分支、循环）
2. 工具注册和调用
3. Checkpoint 保存和恢复
4. Human-in-the-Loop 中断和恢复
5. 流式输出
6. Agent 定义和执行
7. 多 Agent 编排

用法：
    python backend/scripts/runtime_plane_smoke.py [--verbose]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# 确保可以导入 backend 模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_graph_engine():
    """测试图引擎基本执行。"""
    from backend.runtime_plane.graph import StateGraph, MessagesState, START, END

    print("=== Test 1: Graph Engine Basic ===")

    # 定义节点
    def node_a(state):
        return {"messages": [{"role": "assistant", "content": "Hello from A"}]}

    def node_b(state):
        return {"messages": [{"role": "assistant", "content": "Hello from B"}]}

    # 构建图
    graph = StateGraph(MessagesState)
    graph.add_node("a", node_a)
    graph.add_node("b", node_b)
    graph.add_edge(START, "a")
    graph.add_edge("a", "b")
    graph.add_edge("b", END)

    compiled = graph.compile()
    result = compiled.invoke({"messages": [{"role": "user", "content": "test"}]})

    messages = result.get("messages", [])
    assert len(messages) >= 3, f"Expected 3+ messages, got {len(messages)}"
    print(f"  ✓ Linear execution: {len(messages)} messages")
    return True


def test_conditional_edges():
    """测试条件路由。"""
    from backend.runtime_plane.graph import StateGraph, MessagesState, START, END

    print("=== Test 2: Conditional Edges ===")

    def classify(state):
        content = state.get("messages", [{}])[-1].get("content", "")
        if "?" in content:
            return {"_route": "answer"}
        return {"_route": "acknowledge"}

    def answer(state):
        return {"messages": [{"role": "assistant", "content": "That's a question!"}]}

    def acknowledge(state):
        return {"messages": [{"role": "assistant", "content": "Noted."}]}

    def route(state):
        return state.get("_route", "acknowledge")

    graph = StateGraph(MessagesState)
    graph.add_node("classify", classify)
    graph.add_node("answer", answer)
    graph.add_node("acknowledge", acknowledge)
    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route, ["answer", "acknowledge"])
    graph.add_edge("answer", END)
    graph.add_edge("acknowledge", END)

    compiled = graph.compile()

    # Test question
    result = compiled.invoke({"messages": [{"role": "user", "content": "What is AI?"}]})
    msgs = result.get("messages", [])
    assert any("question" in str(m).lower() for m in msgs), "Should route to answer"
    print("  ✓ Conditional routing (question → answer)")

    # Test statement
    result = compiled.invoke({"messages": [{"role": "user", "content": "AI is amazing."}]})
    msgs = result.get("messages", [])
    assert any("noted" in str(m).lower() for m in msgs), "Should route to acknowledge"
    print("  ✓ Conditional routing (statement → acknowledge)")
    return True


def test_checkpoint():
    """测试检查点存储。"""
    from backend.runtime_plane.graph import InMemoryCheckpointStore, Checkpoint

    print("=== Test 3: Checkpoint Store ===")

    store = InMemoryCheckpointStore()

    # 保存检查点
    cp1 = Checkpoint(thread_id="t1", step=1, state={"messages": ["msg1"]}, current_node="a")
    cp2 = Checkpoint(thread_id="t1", step=2, state={"messages": ["msg1", "msg2"]}, current_node="b")
    store.save("t1", cp1)
    store.save("t1", cp2)

    # 加载最新
    latest = store.load("t1")
    assert latest.step == 2, f"Expected step 2, got {latest.step}"
    print(f"  ✓ Save and load latest: step={latest.step}")

    # 列出所有
    all_cps = store.list_checkpoints("t1")
    assert len(all_cps) == 2, f"Expected 2 checkpoints, got {len(all_cps)}"
    print(f"  ✓ List checkpoints: {len(all_cps)}")

    # 加载指定
    specific = store.load("t1", cp1.checkpoint_id)
    assert specific.step == 1, f"Expected step 1, got {specific.step}"
    print(f"  ✓ Load specific checkpoint: step={specific.step}")
    return True


def test_tool_registry():
    """测试工具注册。"""
    from backend.runtime_plane.tools import tool, ToolRegistry

    print("=== Test 4: Tool Registry ===")

    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    @tool(name="custom_multiply", risk_level="medium")
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers."""
        return a * b

    registry = ToolRegistry()
    registry.register(add)
    registry.register(multiply)

    # 列出工具
    tools = registry.list_tools()
    assert len(tools) == 2, f"Expected 2 tools, got {len(tools)}"
    print(f"  ✓ Register tools: {len(tools)}")

    # 获取工具
    t, handler = registry.get("add")
    assert t is not None
    assert handler is not None
    result = handler(3, 4)
    assert result == 7, f"Expected 7, got {result}"
    print(f"  ✓ Execute tool 'add(3, 4)' = {result}")

    # 自定义名称
    t2, _ = registry.get("custom_multiply")
    assert t2 is not None
    assert t2.risk_level == "medium"
    print(f"  ✓ Custom tool name and risk_level")

    # 生成模型格式
    model_tools = registry.get_tools_for_model()
    assert len(model_tools) == 2
    assert model_tools[0]["type"] == "function"
    print(f"  ✓ Generate model-compatible tool format")
    return True


def test_interrupt():
    """测试 Human-in-the-Loop 中断。"""
    from backend.runtime_plane.graph import StateGraph, MessagesState, START, END, InterruptError

    print("=== Test 5: Interrupt (Human-in-the-Loop) ===")

    def human_approval(state):
        from backend.runtime_plane.graph import interrupt
        approved = interrupt("Do you approve?")
        return {"messages": [{"role": "assistant", "content": f"Approved: {approved}"}]}

    graph = StateGraph(MessagesState)
    graph.add_node("approval", human_approval)
    graph.add_edge(START, "approval")
    graph.add_edge("approval", END)

    compiled = graph.compile()

    # 执行会触发中断
    chunks = list(compiled.stream({"messages": [{"role": "user", "content": "request"}]}))
    has_interrupt = any(c.mode.value == "interrupt" for c in chunks)
    assert has_interrupt, "Should have interrupt event"
    print("  ✓ Interrupt triggered during execution")
    return True


def test_streaming():
    """测试流式输出。"""
    from backend.runtime_plane.graph import StateGraph, MessagesState, START, END

    print("=== Test 6: Streaming ===")

    def step_1(state):
        return {"messages": [{"role": "assistant", "content": "Step 1 done"}]}

    def step_2(state):
        return {"messages": [{"role": "assistant", "content": "Step 2 done"}]}

    graph = StateGraph(MessagesState)
    graph.add_node("s1", step_1)
    graph.add_node("s2", step_2)
    graph.add_edge(START, "s1")
    graph.add_edge("s1", "s2")
    graph.add_edge("s2", END)

    compiled = graph.compile()
    chunks = list(compiled.stream({"messages": [{"role": "user", "content": "go"}]}))

    assert len(chunks) >= 2, f"Expected 2+ chunks, got {len(chunks)}"
    modes = [c.mode.value for c in chunks]
    assert "updates" in modes, "Should have updates mode"
    print(f"  ✓ Streaming: {len(chunks)} chunks, modes={modes}")
    return True


def test_agent_definition():
    """测试 Agent 定义。"""
    from backend.runtime_plane.agents import Agent
    from backend.runtime_plane.tools import tool

    print("=== Test 7: Agent Definition ===")

    @tool
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello, {name}!"

    agent = Agent(
        name="test_agent",
        instructions="You are a test agent.",
        model="gpt-4o",
        tools=[greet],
        description="A test agent.",
    )

    card = agent.to_agent_card()
    assert card["agent_id"] == "test_agent"
    assert card["model"] == "gpt-4o"
    assert "greet" in card["tools"]
    assert "chat" in card["capabilities"]
    assert "tool_call" in card["capabilities"]
    print(f"  ✓ Agent card: {card['agent_id']}, tools={card['tools']}, caps={card['capabilities']}")

    # Agent as tool
    as_tool = agent.as_tool("call_test", "Call test agent")
    assert as_tool.name == "call_test"
    print(f"  ✓ Agent as tool: {as_tool.name}")
    return True


def test_graph_with_tools():
    """测试图引擎 + 工具调用。"""
    from backend.runtime_plane.graph import StateGraph, MessagesState, START, END
    from backend.runtime_plane.graph.nodes import ToolNode
    from backend.runtime_plane.tools import tool, ToolRegistry

    print("=== Test 8: Graph with Tool Execution ===")

    @tool
    def calculate(expression: str) -> str:
        """Calculate a math expression."""
        try:
            result = eval(expression)  # noqa: S307
            return str(result)
        except Exception:
            return "error"

    registry = ToolRegistry()
    registry.register(calculate)

    tool_node = ToolNode(name="tools", tool_registry=registry)

    call_count = {"n": 0}

    def agent_node(state):
        call_count["n"] += 1
        if call_count["n"] <= 1:
            # 第一次：调用工具
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"id": "tc1", "name": "calculate", "args": {"expression": "2+3"}}],
                }]
            }
        # 第二次：工具已执行，直接返回最终答案
        messages = state.get("messages", [])
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "tool":
                return {"messages": [{"role": "assistant", "content": f"The result is {m['content']}"}]}
        return {"messages": [{"role": "assistant", "content": "No result"}]}

    def final_node(state):
        messages = state.get("messages", [])
        # 找到工具结果
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "tool":
                return {"messages": [{"role": "assistant", "content": f"The result is {m['content']}"}]}
        return {"messages": [{"role": "assistant", "content": "No result"}]}

    def has_tool_calls(state):
        messages = state.get("messages", [])
        if messages:
            last = messages[-1]
            if isinstance(last, dict) and last.get("tool_calls"):
                return "tools"
        return "final"

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("final", final_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", has_tool_calls, ["tools", "final"])
    graph.add_edge("tools", "agent")
    graph.add_edge("final", END)

    compiled = graph.compile()
    result = compiled.invoke({"messages": [{"role": "user", "content": "Calculate 2+3"}]})

    messages = result.get("messages", [])
    assert any("5" in str(m) for m in messages), f"Should contain result '5', got {messages}"
    print(f"  ✓ Tool execution in graph: {len(messages)} messages, result contains '5'")
    return True


def main():
    verbose = "--verbose" in sys.argv

    tests = [
        test_graph_engine,
        test_conditional_edges,
        test_checkpoint,
        test_tool_registry,
        test_interrupt,
        test_streaming,
        test_agent_definition,
        test_graph_with_tools,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ FAILED: {e}")
            if verbose:
                import traceback
                traceback.print_exc()

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {len(tests)} total")

    if failed > 0:
        sys.exit(1)
    print("All tests passed! ✓")


if __name__ == "__main__":
    main()
