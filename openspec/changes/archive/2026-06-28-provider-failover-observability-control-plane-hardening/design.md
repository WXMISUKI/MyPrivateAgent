## Context

项目已经有 provider failover 统计面：后端通过 `ProviderFailoverAnalyticsService` 聚合 planner child execution 的 provider 切换元数据，前端 Settings 页在“模型与 Provider”区域展示 failover 看板和阈值提示。但这块能力还只是实现层逻辑，没有被正式定义为稳定的 read model，因此很容易和 provider 配置、planner 路由或 model selection 语义混淆。

本次 change 只把 failover 观测面收口，不改路由器、不改调度器，不新增模型市场或 provider 调度引擎。

## Goals / Non-Goals

**Goals:**
- 统一 failover analytics 输出字段，作为稳定 read model 供 Settings 页和运维诊断使用。
- 明确统计窗口、limit、切换率、切换子任务、总切换次数、平均切换次数以及 top provider/model 路径的语义。
- 让 Settings 页的 failover 看板成为可复用的观测入口，而不是临时调试面板。

**Non-Goals:**
- 不修改 planner 或 scheduler 的实际路由决策逻辑。
- 不把 failover analytics 升级为自动化调度或 provider market 选择器。
- 不替代 provider configuration control plane，也不替代 `provider-onboarding` / `service-providers`。

## Decisions

1. **failover analytics 作为只读聚合层**
   - 选择：继续从 child execution 元数据聚合，而不是再引入新的表或执行链。
   - 原因：数据已经在现有运行时对象里，最小成本是稳定 read model。
   - 备选：新建专门的 failover 事件存储。
   - 为什么不选：会额外增加存储和迁移复杂度。

2. **Settings 页仅消费聚合结果**
   - 选择：Settings 页显示 summary、阈值和 top 路径，不自己计算 failover 统计。
   - 原因：避免前端再次推导业务语义。
   - 备选：前端直接从 child execution 原始数据计算。
   - 为什么不选：会制造重复逻辑和统计口径漂移。

3. **窗口和 limit 保持受控**
   - 选择：只允许有限的窗口和结果条数。
   - 原因：避免过大查询拖慢设置页，也避免读模型无限膨胀。
   - 备选：开放任意查询参数。
   - 为什么不选：会让简单观测面变成通用分析查询。

4. **failover 观测与 provider config 分离**
   - 选择：failover analytics 只解释切换行为，不管理 API key/base URL/model 名。
   - 原因：这两者分别属于观测与配置控制面。
   - 备选：把配置和 failover 合并到一个更大的 provider dashboard。
   - 为什么不选：会稀释职责边界，增加维护风险。

## Risks / Trade-offs

- [Risk] 只读聚合会受限于现有 child execution 元数据质量。 → [Mitigation] 在 spec 和测试中固定必须字段，缺字段时保持统计可解释。
- [Risk] 统计窗口变化会影响用户对趋势的解读。 → [Mitigation] 通过 Settings 页清楚展示窗口值，并限制可选范围。
- [Risk] UI 上的 failover 看板会被误解为路由控制台。 → [Mitigation] 文案明确“看板/诊断”，并在 docs 中强调不是路由引擎。

## Migration Plan

1. 固化 failover observability 规格。
2. 增加后端单测，覆盖聚合口径和窗口过滤。
3. 增加前端单测，确保 Settings 页继续渲染 failover 看板和阈值信息。
4. 更新 docs 真源，明确该面板与配置控制面的边界。
5. 验证通过后归档 change。

Rollback:
- 如统计口径存在偏差，可回退到仅保留 Settings 页展示而不依赖该 read model 的增强字段。
- 如窗口或 limit 引发性能问题，可收紧参数范围而不改变现有路由语义。

## Open Questions

- 是否需要为 failover analytics 增加更细粒度的时间分桶？
- 是否需要在后续把该 read model 暴露给独立运维页，而不是只放在 Settings 页？
- 是否需要把 top provider/model 路径与 planner 任务标题进一步关联，用于更可解释的排障？
