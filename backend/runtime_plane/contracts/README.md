# ExecutionAdapter Contracts

## 定义

运行层与治理层之间的标准化通信 envelope。

## 合同

- `ExecutionRequest`: 执行请求（request_id, agent_id, user_input, thread_id, runtime, context_refs）
- `ExecutionEvent`: 执行事件（event_id, run_id, stage, type, payload_summary, raw_ref）
- `ExecutionResult`: 执行结果（status, final_answer, artifacts, tool_calls, citations, trace_ref）
- `AgentManifest`: Agent 清单（agent_id, role, capabilities, governance_boundaries）

## 约束

- envelope 不得包含 Python callable、active stream iterator 或 provider client
- envelope 是治理层消费的标准格式，不是框架内部格式的透出
- 每个 adapter 负责将框架原生事件翻译为标准 envelope

## 当前状态

**已落地的最小合同**。ExecutionRequest / ExecutionEvent / ExecutionResult / AgentManifest 已作为 Stage 1 首个切片实现。
