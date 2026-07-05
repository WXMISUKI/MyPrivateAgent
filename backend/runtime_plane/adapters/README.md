# Framework Adapters

## 定位

外部执行框架的 ExecutionAdapter 实现。

## 适配器清单

| 适配器 | 目标框架 | 借鉴能力 | 状态 |
|---|---|---|---|
| LangGraphAdapter | LangGraph | 图/状态/checkpoint/human-in-loop | 待实现（现有 pilot 骨架在 framework_adapter_spi/） |
| AgentRunAdapter | AgentRun | 托管运行/沙箱/模型代理/可观测 | 待实现 |
| ADKAdapter | Google ADK | agent 发现/跨 agent 通信 | 待实现 |
| OpenAIAgentsAdapter | OpenAI Agents SDK | handoff/guardrail/session/tracing | 待实现 |

## 每个 adapter 必须实现

1. `health_check()` - 健康检查
2. `can_execute()` - 是否可执行
3. `translate_input()` - ExecutionRequest → 框架原生格式
4. `stream_events()` - 框架原生事件 → ExecutionEvent
5. `translate_output()` - 框架原生结果 → ExecutionResult

## Promotion Gate

每个 adapter 必须经过：experimental → pilot → production

## 当前状态

**骨架占位**。现有 LangGraph draft adapter 在 `backend/agent_framework/framework_adapter_spi/langgraph_draft.py`。
