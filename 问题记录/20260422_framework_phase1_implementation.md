# MyPrivateAgent 框架抽离 Phase 1 实施记录

## 文档信息
- 日期：2026-04-22
- 状态：已实施
- 目标：在不打断现有业务可运行性的前提下，先抽出一层可复用的 Agent Runtime 内核

---

## 本次实施范围

本轮没有直接把项目拆成独立 pip/npm 包，而是先在 `backend/agent_framework/` 内新增一层通用运行时能力，供当前业务代码复用。这样后续再拆成独立包时，不需要推倒重来。

新增内容：

- `backend/agent_framework/events.py`
  - 定义统一 `AgentEvent`
  - 增加 `run_id / conversation_id / iteration / payload`
- `backend/agent_framework/runtime.py`
  - 定义 `AgentState`
  - 定义 `AgentRunContext`
- `backend/agent_framework/tools.py`
  - 定义 `ToolSpec`
  - 定义 `render_mode / deterministic / safe_to_rephrase / passthrough_strategy`
- `backend/agent_framework/providers.py`
  - 定义最小 `ModelProvider` 协议

---

## 现有代码接入点

### 1. Tool Registry 接入工具元数据

`backend/harness/tool_registry.py` 已增加：

- `register_tool_spec`
- `get_tool_spec`
- `list_tool_specs`

这样工具不再只有 schema 和 executor，还开始具备运行时元数据。

### 2. LangChain 工具补充 ToolSpec

`backend/harness/tools/langchain_tools.py` 已为：

- `search`
- `get_current_datetime`

补充 `ToolSpec`，包括：

- 是否确定性
- 是否允许模型重写
- 结果渲染方式
- passthrough 策略

### 3. AgentHarness 接入统一运行时上下文

`backend/harness/agent_harness.py` 已开始使用：

- `AgentRunContext`
- `AgentEventFactory`

现在每次运行都会带上：

- `run_id`
- `conversation_id`
- `iteration`
- `state`

并通过统一事件格式输出。

### 4. 确定性工具结果直出开始平台化

过去天气直出是硬编码判断。现在改为优先读取 `ToolSpec.passthrough_strategy`，开始从“个别 if/else”转向“工具元数据驱动”。

---

## 当前收益

本次实施后，框架已经具备后续独立化的基础：

1. 事件协议有了统一形态
2. 工具从“函数集合”开始升级为“带元数据的能力单元”
3. Harness 开始显式记录运行上下文
4. 未来拆成 `agent-core / agent-server / app` 时，边界更清晰

---

## 仍未完成的部分

本轮只完成了 Phase 1 的基础铺设，以下内容仍需后续推进：

1. 将 `backend/agent_framework/` 真正拆成可安装的独立包
2. 将 `ModelRouter`、`ContextManager`、`MemoryManager` 继续接口化
3. 将 SSE 输出完全切换到统一 `AgentEvent` 消费模型
4. 将工具结果渲染从“文本优先”升级为“plain_text / markdown / structured_card”
5. 增加回归测试，覆盖事件协议、工具元数据、状态机流转

---

## 下一阶段建议

建议下一轮优先做三件事：

1. 把 `ContextManager` 和 `MemoryManager` 抽成 `context/artifact/memory` 三层接口
2. 把 `ModelRouter` 改造成真正的 provider adapter 层
3. 增加 `tests/agent_framework/`，补齐核心运行时回归测试
