"""
外部框架适配器。

此模块承载各外部执行框架的 ExecutionAdapter 实现：
- LangGraphAdapter: 复杂图编排、循环、checkpoint、human-in-loop
- AgentRunAdapter: 托管运行、沙箱、模型代理、可观测
- ADKAdapter: 跨语言/跨团队 agent 发现与互操作
- OpenAIAgentsAdapter: 轻量 agent、handoff、guardrails

注意：此目录当前为骨架占位。现有 adapter 仍在 backend/agent_framework/framework_adapter_spi/ 中。
"""
