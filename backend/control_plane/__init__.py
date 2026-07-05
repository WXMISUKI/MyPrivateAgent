"""
Control Plane（治理控制面）

此目录承载 MyPrivateAgent 的治理控制面能力：
- registry: agent 资产注册与发现
- governance: 策略、审批、审计
- policy: 策略引擎
- approval: 审批流程
- trace: 运行追踪
- audit: 治理审计
- runtime_surface: 运行时表面聚合
- contract_gate: 质量门禁

注意：此目录当前为骨架占位。现有代码仍在 backend/services/ 和 backend/agent_framework/ 中。
新治理能力应优先放在此目录下，逐步收口。
"""
