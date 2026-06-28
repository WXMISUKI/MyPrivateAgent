## Context

项目里已经存在 `backend/routers/providers.py`、`backend/services/provider_config_service.py` 和前端 `ProviderConfigPanel`，用于管理模型/Provider 的 API key、base URL 和模型名。这些实现能够工作，但目前主要以功能代码存在，没有被正式定义为一个独立控制面能力，导致 read model、安全边界、更新语义和测试语义缺少统一合同。

这次 change 的目标不是引入新的 provider marketplace，也不是重写 provider consumption contract，而是把现有配置控制面收口成可测试、可审计、可复用的规范层。

## Goals / Non-Goals

**Goals:**
- 统一 Provider 配置读模型，明确哪些字段可以看、哪些字段必须脱敏。
- 统一 Provider 配置更新语义，支持 base URL、API key 和模型名的显式更新。
- 统一 Provider 连接测试语义，使其成为显式动作而不是隐式副作用。
- 让 Settings 页的 Provider 配置区成为稳定消费面，便于多人协作时复用。

**Non-Goals:**
- 不建设完整的模型市场或第三方 provider 商店。
- 不把 `/api/providers` 替代成 `/api/service-providers`，两者分工保持清晰。
- 不暴露原始 API key 到任何 read surface。
- 不在本次 change 中引入新 provider 类型或新模型供应商。

## Decisions

1. **配置控制面保留在现有 `/api/providers` 里**
   - 选择：继续使用现有 provider 配置 API，而不是新开平行配置域。
   - 原因：已有前端和后端调用链，新增平行域会制造双入口和双语义。
   - 备选：为 Provider 配置另开一组新 API。
   - 为什么不选：会增加迁移成本，并与现有 settings 页面重复。

2. **读模型只返回脱敏信息和配置来源**
   - 选择：API key 只返回 masked 形式或空值，保留 base URL、模型名和 config source。
   - 原因：配置控制面需要可视化，但不能把 secret 泄露给浏览器或日志。
   - 备选：返回完整配置供调试。
   - 为什么不选：违背最基本的安全边界。

3. **连接测试是显式动作**
   - 选择：测试按钮触发的 `/test` 调用只做连接校验和状态反馈。
   - 原因：测试应该帮助判断配置是否可用，而不是默默改变 runtime 状态。
   - 备选：自动在保存后立即执行连接测试。
   - 为什么不选：会让保存动作带有不确定副作用，且不利于排障。

4. **前端只消费控制面结果，不推导配置真源**
   - 选择：Settings 页只展示 ProviderConfigPanel 返回的配置结果和 failover 诊断。
   - 原因：避免前端自己拼状态，导致配置真源分散。
   - 备选：前端本地保存和本地推导 provider 状态。
   - 为什么不选：会重新制造读模型漂移。

## Risks / Trade-offs

- [Risk] API key 仍以 local override 形式存在于本地数据目录，存在本地泄露风险。 → [Mitigation] 只在本地调试控制面使用，read surface 永远脱敏，文档里明确不要把它当集中 secrets manager。
- [Risk] 连接测试可能对外部 provider 产生额外流量。 → [Mitigation] 保持测试动作显式且最小化，只用于验证可达性和认证，不做真实业务调用。
- [Risk] Settings 页把配置和 failover 看板放在同一 tab，可能看起来像一个大杂烩。 → [Mitigation] 通过分区和文案明确“配置”与“观测”是不同职责。
- [Risk] Provider 配置模块容易演变成模型市场。 → [Mitigation] 在 spec 和 docs 中明确不承担 provider discovery、marketplace 或自动注册职责。

## Migration Plan

1. 先把 provider config control plane 规格写清楚，并同步 docs。
2. 增加聚焦测试，锁住 masked read model、update 语义和 test 语义。
3. 若测试暴露语义漂移，再做最小代码修正。
4. 验证通过后归档 change，让 Settings 页与 provider 配置模块成为可复用模板。

Rollback:
- 如果更新语义或测试语义出现不可接受的漂移，回退到仅保留只读列表示意。
- 如果出现 secret 暴露风险，优先收紧读模型并禁用新增字段展示。

## Open Questions

- 是否需要为 `/api/providers/{provider_name}/test` 增加统一错误码，还是保持当前 provider-specific 文案？
- 是否需要把 provider 配置持久化从本地 JSON 进一步抽象成可替换存储层？
- 是否应该把 Settings 页里的 failover 看板拆成独立观测页，还是继续保持同一 tab？
