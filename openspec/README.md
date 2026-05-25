# OpenSpec 使用说明

## 1. 在本仓库里，OpenSpec 用来做什么

`MyPrivateAgent` 中，OpenSpec 主要用于承接：

- 新增或重定义 runtime contract
- 新增 read model / governance summary / query detail / timeline filter
- 跨 `Runtime Core / Capability / Governance / Delivery` 两层以上的变更
- 吸收外部参考项目后的正式设计输入

它**不**替代：

- `docs/architecture/*` 的架构真源
- `docs/roadmap/*` 的阶段任务与进度面板
- `.specify/memory/constitution.md` 的项目级开发原则

## 2. 推荐阅读顺序

1. `.specify/memory/constitution.md`
2. `openspec/config.yaml`
3. `openspec/specs/`
4. `openspec/changes/`
5. `docs/architecture/runtime_contracts.md`
6. `docs/roadmap/next_phase_hardening.md`

## 3. 当前仓库的 OpenSpec 结构

```text
openspec/
├── config.yaml
├── specs/
│   └── query-run-read-model/
│       └── spec.md
└── changes/
    ├── archive/
    └── decouple-main-chat-query-read-model/
        ├── proposal.md
        ├── design.md
        ├── tasks.md
        └── specs/
            └── query-run-read-model/
                └── spec.md
```

说明：

- `openspec/specs/`：canonical spec 真源
- `openspec/changes/`：进行中的 change proposal
- `openspec/changes/archive/`：已归档 change

当前 canonical specs：

- `openspec/specs/query-run-read-model/spec.md`
- `openspec/specs/query-workspace-generalization/spec.md`
- `openspec/specs/channel-promotion-gate/spec.md`

## 4. 当前项目中的推荐工作流

### 4.1 新建一个变更

适用：中等以上复杂度、会影响 contract/read model/governance 的变更

1. 先确认是否命中 `.specify/memory/constitution.md` 中“必须走 OpenSpec”的条件
2. 阅读相关 canonical spec
3. 在 `openspec/changes/<change-name>/` 中创建：
   - `proposal.md`
   - `design.md`
   - `tasks.md`
   - `specs/<capability>/spec.md`
4. 再进入实现
5. 完成后同步：
   - `docs/architecture/*`
   - `docs/roadmap/*`
   - 测试

### 4.2 当前 change 命名建议

建议使用：

- 动词 + 对象 + 目标

例如：

- `decouple-main-chat-query-read-model`
- `add-recent-query-history-pagination`
- `align-artifact-and-snapshot-reference`

避免使用：

- `fix-stuff`
- `phase-h-work`
- `tmp-change`

## 5. proposal / design / tasks 最小要求

### proposal.md

至少回答：

1. 为什么做
2. 改什么
3. 不改什么
4. 风险点
5. 怎么验证

### design.md

至少回答：

1. 影响哪些模块
2. contract 边界怎么变
3. 为什么这么分层
4. 为什么不选其他做法

### tasks.md

至少回答：

1. 最小实现切片
2. 验证步骤
3. 文档同步步骤
4. follow-up 还有什么没做

## 6. 当前项目里的一个真实样板

第一份真实样板：

- `openspec/changes/decouple-main-chat-query-read-model/`

它展示了如何把一个已经进入 `Phase H` 的真实需求，写成：

- proposal
- design
- tasks
- delta spec

第二份真实样板：

- `openspec/changes/add-main-chat-query-history-pagination/`

它展示了如何在第一份 read model 收口之后，继续沿 canonical spec 扩展下一层能力边界。

第三份真实样板：

- `openspec/changes/generalize-query-workspace-boundary/`

它展示了如何在某条专项能力做深之后，反过来收口“哪些已经可以上升成通用边界、哪些仍然保持专项实现”的高层判断。

第四份真实样板：

- `openspec/changes/pilot-subagent-lane-recent-summary/`

它展示了如何在高层边界写清之后，只推进某个 channel 的**轻量试点层**，而不是直接越级实现完整 query 模式。

后续新需求建议优先参考这四个目录，而不是从空白开始写。

当前建议：

- 如果某条能力还在“从无到有”阶段，优先参考前两份样板
- 如果某条能力已经做深、开始接近阶段完成线，优先参考第三份样板，先收口通用边界再决定是否继续扩
- 如果高层边界已经写清、准备做某个 channel 的第一步推广试点，优先参考第四份样板
- 如果要判断“哪些能力可以从某个 channel 上升成长期通用模式”，优先先读 `query-workspace-generalization` canonical spec
- 如果要判断一个新 channel 能否进入 `recent summary / query detail / query history / query workspace`，先看 `channel-promotion-gate` canonical spec
- 如果一个阶段已经同时具备 canonical spec、read model、最小前端壳和试点边界判断，优先先做阶段收束，再决定是否继续扩新试点

## 7. 与 Spec Kit 的分工

- `Spec Kit constitution`：约束项目级原则
- `OpenSpec`：承接功能/变更规格

简化理解：

- constitution 决定“我们怎么做事”
- OpenSpec 决定“这次具体改什么、怎么改、怎么验收”

## 8. 当前不建议怎么用

- 不建议每一个小 bugfix 都新开 OpenSpec change
- 不建议只写 proposal 不写 tasks 就直接进入实现
- 不建议让 OpenSpec 脱离 roadmap 和 architecture 独立演化
- 不建议只写变更 delta spec，却没有 canonical spec 真源
