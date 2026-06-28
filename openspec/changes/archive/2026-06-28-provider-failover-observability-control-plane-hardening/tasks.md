## 1. Specification and Docs

- [x] 1.1 固化 provider failover observability 规格，明确 read model、只读语义和 bounded query 参数
- [x] 1.2 更新 `docs/guides/capability_runtime_registry.md`，把 failover analytics 的读模型边界写清楚
- [x] 1.3 更新 `docs/architecture/runtime_contracts.md` 和 `docs/roadmap/next_phase_hardening.md`，明确 Settings 页中的 failover 看板是诊断面不是路由引擎

## 2. Backend Validation

- [x] 2.1 增加 provider failover analytics 的单测，覆盖窗口过滤、聚合字段和 top 路径输出
- [x] 2.2 增加 provider router 的单测，覆盖 `/api/failover-analytics` 的参数边界和失败路径

## 3. Frontend Validation

- [x] 3.1 增加 SettingsView 的聚焦测试，覆盖 failover 看板、阈值信息和 provider routing summary 的可见性
- [x] 3.2 确认 Settings 页仍然可以同时挂载 provider config、provider onboarding 和 failover observability

## 4. Validation and Archive

- [x] 4.1 运行后端聚焦测试确认 failover observability 通过
- [x] 4.2 运行前端聚焦测试确认 SettingsView failover 看板通过
- [x] 4.3 运行 OpenSpec strict 校验确认 change 结构有效
- [x] 4.4 验证通过后归档 change，并保留 failover 观测文档作为样板
