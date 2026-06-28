## Context

当前项目已经具备 Coze 工作流只读注册、Workflow Lab 回放和 capability runtime 统一调用面的基础能力，但这些能力主要服务于单个样例验证，还没有形成适合多人持续迁移、可对外消费的稳定合同。现阶段最需要收口的是两件事：一是把 Coze 节点依赖映射成统一的 runtime 语义，二是把已推广工作流暴露成稳定、可追踪、fail-closed 的 API 调用面。

## Goals / Non-Goals

**Goals:**
- 统一 Coze 工作流依赖映射语义，明确 runtime capability、provider-backed、artifact_input、explicit_blocker 四类结果。
- 为已推广工作流提供稳定的 capability invoke 合同，确保外部项目可以通过 API 使用，而不是依赖临时样例或人工约定。
- 保持 Workflow Lab 为只读验证层，继续承担 registry 查看、dependency mapping、acceptance replay 和 diff 观察职责。
- 让后续新增工作流可以沿同一套规则迁移、验证、上线，降低多人协作冲突。

**Non-Goals:**
- 不在本次 change 中建设完整模型 provider registry、baseurl/apikey 管理或模型市场。
- 不把 Workflow Lab 变成默认 chat 入口或第二条执行链。
- 不改写现有 Runtime Core、Query Control 或 provider service 的主定位。
- 不追求一次性覆盖所有未来 Coze 插件形态，先收口当前迁移高频依赖类型。

## Decisions

1. **依赖映射以显式分类为准，不以“能跑通”代替“可解释”**
   - 选择：把每个 Coze 节点落到固定分类和 blocker 语义。
   - 原因：后续迁移的最大风险不是不能执行，而是依赖语义不透明，导致团队无法判断是否真的完成迁移。
   - 备选：仅记录执行结果或成功/失败状态。
   - 为什么不选：状态结果无法指导后续迁移，也无法支持审计和协作分工。

2. **对外调用统一走 capability runtime envelope**
   - 选择：工作流对外以稳定 capability id 和统一 invoke envelope 暴露。
   - 原因：项目已经把 capability runtime 作为统一控制面，继续新增平行执行入口会导致治理、审计、trace 和权限语义分裂。
   - 备选：每个 workflow 直接暴露独立路由并自行执行。
   - 为什么不选：会破坏统一 contract，后续难以维护和做治理观测。

3. **Workflow Lab 保持只读**
   - 选择：Workflow Lab 只负责查看、回放和对比，不承担生产执行。
   - 原因：它的价值是迁移验证和回归检查，不是业务入口。
   - 备选：让 Lab 兼任执行调试台和生产调用台。
   - 为什么不选：容易把验证面和执行面混在一起，增加误操作和权限复杂度。

4. **模型 provider registry 另开 change**
   - 选择：本次不引入统一模型配置模块。
   - 原因：当前最紧急的是把 workflow 迁移生产线做稳，而不是立即扩展基础设施层。
   - 备选：顺手把模型列表、baseurl、apikey、provider marketplace 一并补齐。
   - 为什么不选：会把范围拉得过大，稀释当前 change 的投产价值。

## Risks / Trade-offs

- [Risk] 依赖映射规则过严，导致部分 workflow 继续停留在 blocked。 → [Mitigation] 先明确 blocker，允许逐步补能力，不要静默降级。
- [Risk] API envelope 过早稳定后，后续字段扩展受限。 → [Mitigation] 以向后兼容为原则，新增字段优先做可选扩展。
- [Risk] Workflow Lab 只读导致调试体验不如大型平台。 → [Mitigation] 通过更好的 replay diff 和 blocker 可视化提升可诊断性，但不把它改成执行链。
- [Risk] 后续团队可能仍然想绕过 capability runtime。 → [Mitigation] 在 spec、docs 和测试里明确 fail-closed，要求统一入口。

## Migration Plan

1. 先落 dependency mapping contract spec，统一分类、blocker 和输出字段。
2. 再落 invocation API hardening spec，让工作流可以以稳定 envelope 对外暴露。
3. 同步更新 Workflow Lab runbook 和 migration authoring guide，确保手册与 contract 一致。
4. 通过聚焦测试验证：依赖映射、blocked 场景、active workflow invoke、draft/review fail-closed、Lab replay diff。
5. 若回放或调用面出现 contract 漂移，优先修正 spec 和读模型，再考虑前端展示。

Rollback:
- 若稳定调用面出现不可接受的 contract 漂移，则回退到只读 registry + Workflow Lab 的状态。
- 若 dependency mapping 规则引入过多误阻断，则先保留 blocker 语义并调整分类规则，不放开隐式降级。

## Open Questions

- 是否需要在后续 change 中为 workflow invoke 增加更完整的鉴权/授权模型，还是先维持当前 envelope 语义？
- 对 `http.request` 之外的外部节点类型，是否要先定义通用 `external_dependency` 兜底，还是继续按具体能力逐项显式映射？
- Workflow Lab 的 replay 结果是否需要在后续补充更强的错误码标准，以便团队自动化消费？
