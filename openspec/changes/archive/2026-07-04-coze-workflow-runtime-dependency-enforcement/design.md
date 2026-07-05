## Context

当前仓库已经把 Coze workflow 迁移拆成了三个面：
- registry：读取 workflow manifest、ready 状态和 capability id。
- Workflow Lab：只读展示 dependency mapping、acceptance examples 和 replay diff。
- invoke：把 promoted workflow 作为 capability 入口调用。

问题是 dependency mapping 的语义目前仍主要存在于 Workflow Lab 侧，而 registry invoke 只做了很粗的 blocker 检查。随着工作流越来越多，如果不把 dependency mapping 提升成共享 preflight contract，团队会在 registry、lab、invoke 三处重复实现“这个节点是否可执行”的判断，导致 blocker 语义不一致。

## Goals / Non-Goals

**Goals:**
- 让 registry detail、Workflow Lab、workflow invoke 共用同一份 dependency mapping 逻辑。
- 在 workflow invoke 前执行 dependency preflight，支持 fail-closed。
- 将 `runtime_capability / provider_backed / artifact_input / explicit_blocker` 作为统一类别继续保持稳定。
- 用 focused tests 锁定 mapping 结果和 invoke 阻断行为。

**Non-Goals:**
- 不把 artifact_input 默认改成强阻断，只在 schema 或 runtime reference 缺失时阻断。
- 不把 provider readiness 计算变成新的数据库表或外部服务。
- 不重写 workflow 的具体 executor。
- 不把 Workflow Lab 变成写操作面。

## Decisions

### Decision 1: 提取 shared dependency mapper helper
- 选择：
  - 用一个纯函数 helper 产出 dependency mapping 与 blocker list。
- 原因：
  - registry 和 Workflow Lab 都需要相同的分类规则与 provider readiness 规则。
  - 纯函数便于测试，也避免两个 service 各自漂移。
- 不选方案：
  - 在 registry 和 lab 里复制两份逻辑。短期最快，但长期 blocker 语义一定会分叉。

### Decision 2: workflow invoke 先做 dependency preflight，再进入 executor
- 选择：
  - invoke 时先取 shared dependency mapping，再判断 `explicit_blocker` / provider-backed readiness / unsupported runtime capability。
- 原因：
  - 这能把“导入能注册、调用前已知会失败”的情况提前拦住。
  - 对多人迁移最友好，错误更早、更可读。

### Decision 3: registry detail 直接暴露 dependency mapping contract
- 选择：
  - `get_workflow_by_id` 返回的 workflow detail 直接带 dependency mapping。
- 原因：
  - registry read surface 是这份 contract 的第一真源之一。
  - 这样 Workflow Lab、router、测试都能消费同一份读模型。

## Risks / Trade-offs

- [Risk] mapping helper 规则更新会影响多个调用方
  → Mitigation：把 helper 设计成纯函数，并让 registry/lab/invoke 都通过 focused tests 约束输出。

- [Risk] provider readiness 判断过严可能误拦已可运行 workflow
  → Mitigation：只把 `explicit_blocker`、unsupported runtime capability、以及明确 unavailable 的 provider-backed 依赖作为阻断条件，artifact_input 仍以 schema / runtime reference 校验为准。

- [Risk] 未来更多 external provider 类型需要 mapping
  → Mitigation：保留 provider-backed category 和 blocker reason 的扩展点，避免把 provider 语义写死在单个 workflow 里。

## Migration Plan

1. 新增 shared dependency mapper helper。
2. 让 registry detail / Workflow Lab / invoke preflight 都消费同一 helper。
3. 补 focused tests，覆盖 mapping、registry detail、invoke fail-closed、Workflow Lab 读取一致性。
4. 更新 runtime contracts 文档与一份上线验收记录。
5. 运行 strict validate 和 focused pytest。

回滚策略：
- 如果 shared helper 引入回归，可先回滚 invoke preflight 到旧 blocker 检查，再保留 registry/lab 的只读 mapping。

## Open Questions

- provider-backed readiness 是否需要缓存，目前先按只读 catalog 即时判断即可。
- artifact_input 的运行时引用是否要在后续 change 中引入更严格的 upload contract，这次先不展开。
