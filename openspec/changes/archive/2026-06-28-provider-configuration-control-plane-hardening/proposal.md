## Why

项目里已经有可用的 Provider 配置入口，但它们主要以实现细节存在，缺少一份正式的控制面规格来约束 read model、update 语义、测试语义和安全边界。现在把它收口成正式能力，能让模型 base URL、API key、模型名和连接测试在多人协作时保持一致，也能避免读模型泄露敏感值。

## What Changes

- 把现有 Provider 配置能力收口为正式控制面：provider list、update、connectivity test 和 Settings 页面消费语义统一。
- 明确读模型只返回脱敏结果和配置来源，不返回原始 API key。
- 明确更新语义支持 base URL、API key、模型名等常用配置项，未知 provider 必须 fail closed。
- 明确连接测试是显式动作，不应隐式触发或替代 provider readiness 管理。
- 保持 Provider 配置模块与 provider consumption / onboarding catalog 分工清晰，不把它升级成完整模型市场。

## Capabilities

### New Capabilities
- `provider-configuration-control-plane`: 定义 Provider 配置的读取、更新、测试、脱敏与前端消费规则。

### Modified Capabilities
- 

## Impact

- 后端：`backend/routers/providers.py`、`backend/services/provider_config_service.py` 及 provider 配置相关测试。
- 前端：`frontend-vue/src/components/ProviderConfigPanel.vue`、`frontend-vue/src/views/SettingsView.vue` 及其测试。
- 文档：`docs/guides/capability_runtime_registry.md`、`docs/architecture/runtime_contracts.md`、`docs/roadmap/next_phase_hardening.md`。
- 运行时边界：provider 配置只负责配置管理与连接测试，不替代 `/api/service-providers` 的 live management contract，也不替代 onboarding catalog。
