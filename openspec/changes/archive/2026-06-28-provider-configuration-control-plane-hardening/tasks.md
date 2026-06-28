## 1. Specification and Docs

- [x] 1.1 固化 provider configuration control plane 的规格，明确 masked read model、显式更新和显式测试语义
- [x] 1.2 更新 `docs/guides/capability_runtime_registry.md`，把 `/api/providers` 和 `ProviderConfigPanel` 的分工写清楚
- [x] 1.3 更新 `docs/architecture/runtime_contracts.md` 和 `docs/roadmap/next_phase_hardening.md`，把 provider 配置控制面的边界写入真源文档

## 2. Backend Validation

- [x] 2.1 增加 provider config service 的聚焦测试，覆盖 masked API key、config source、local override persist 和 unknown provider fail closed
- [x] 2.2 增加 provider config test endpoint 的聚焦测试，覆盖支持的 provider family 和不支持的 provider family

## 3. Frontend Validation

- [x] 3.1 增加 `ProviderConfigPanel` 的聚焦测试，覆盖列表渲染、编辑、保存和测试入口
- [x] 3.2 确认 `SettingsView` 仍然可以挂载 provider 配置面板，并保持模型 tab 的可见性

## 4. Validation and Archive

- [x] 4.1 运行后端聚焦测试确认 provider config control plane 通过
- [x] 4.2 运行前端聚焦测试确认 ProviderConfigPanel 和 SettingsView 通过
- [x] 4.3 运行 OpenSpec strict 校验确认 change 结构有效
- [x] 4.4 验证通过后归档 change，并保留文档作为 provider 配置样板
