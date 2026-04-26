# Framework Phase 14 实施记录

## 目标

继续把运行时编排逻辑从 `orchestrator.py` 中剥离，减少它同时承担“状态累计 + artifact 持久化 + done 事件封装 + 错误重试判断”的职责。

## 本次改动

### 1. 新增 Orchestrator Service

新增 `backend/services/orchestrator_service.py`，集中承接原先散落在 `orchestrator.py` 里的辅助逻辑：

- `OrchestratorStreamState`
- `persist_tool_artifact()`
- `build_done_payload()`
- `should_retry_without_tools()`

这让 orchestrator 本体更接近纯编排层，只关注：

- 选择模型
- 创建 harness
- 驱动消息循环
- 按事件类型分发

### 2. 清理 orchestrator 死代码

删除了未使用的：

- `Subtask`
- `SubagentResult`
- `_process_single_agent_simple()`
- `_process_multi_agent_simple()`
- `create_adapter()` 相关残留依赖
- `LearningRecorder` / `conversation_history` 等未使用字段

这一步的意义不只是“代码更短”，而是减少误导性的伪能力和维护成本。

### 3. 增加最小回归

新增 `tests/agent_framework/test_orchestrator_service.py`，覆盖：

- tool artifact 持久化元数据
- done payload 结构
- 工具重试判断
- stream state 默认值

并将其纳入 CI。

## 验证

- `py_compile` 通过
- 当前 runtime 测试共 21 项，全部通过

## 结果

Phase 14 后，`orchestrator.py` 已明显变轻，编排层与事件后处理层的边界开始清晰。这是后续继续抽 `agent-server`、把 server adapter 做成可复用层的重要前提。
