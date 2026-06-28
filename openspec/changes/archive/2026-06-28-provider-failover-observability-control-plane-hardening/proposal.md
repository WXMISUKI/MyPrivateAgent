## Why

当前 Settings 页已经在展示 provider failover 看板和默认模型选择，但这块能力还停留在实现层，缺少正式规格来约束它到底应该展示什么、统计什么、以及什么不属于它。现在把它收口成独立控制面能力，可以让团队稳定观察模型/Provider 切换行为，而不是把 failover 逻辑散落在 planner、settings 和临时诊断脚本里。

## What Changes

- 将 provider failover analytics 收口成正式观测能力，统一展示切换率、切换子任务、总切换次数、目标 provider、目标模型和常见 failover 路径。
- 将 Settings 页中的“默认模型 + Provider Failover 看板”定义为稳定消费面，明确它是观测和配置辅助，不是路由引擎。
- 明确 failover analytics 只读取已有 child execution / provider history 元数据，不新增第二套路由执行链。
- 保持对 provider fallback model selected 这类路由结果的只读解释，不把它升级成自动化调度或市场化路由系统。

## Capabilities

### New Capabilities
- `provider-failover-observability`: 定义 provider failover 指标汇总、模型路由可视化和 Settings 页面消费规则。

### Modified Capabilities
- 

## Impact

- 后端：`backend/routers/providers.py`、`backend/services/provider_failover_analytics_service.py` 及其测试。
- 前端：`frontend-vue/src/views/SettingsView.vue`、`frontend-vue/src/components/__tests__/SettingsView.test.js`，以及与 failover 看板相关的展示逻辑。
- 文档：`docs/guides/capability_runtime_registry.md`、`docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`。
- 运行时边界：failover 观测只做可视化和诊断，不替代 scheduler、planner、provider route engine 或 provider config control plane。
