## Why

当前 `EmbeddedAgentRuntimeSDK / AgentHarnessFacade / continuation recovery` 这条线已经从边界澄清走到可运行 seam，但后续再继续推进 `child executor / worker runtime / multi-process recovery / permission coordination` 时，如果完全闭门增量实现，容易重复踩成熟项目已经踩过的坑。

仓库外已有两类高价值参考源：

- `D:\AI\AIcode\learn-claude-code`
  - 更适合校正 harness 的概念分层、术语边界和演化顺序
- `D:\AI\AIcode\claude-code`
  - 更适合参考真实多 agent / swarm / permission sync / reconnection / backend abstraction 的控制面设计

为了避免“看到什么就抄什么”或“完全不参考自己硬写”，需要先建立正式的 reference alignment 规范：

- 哪些设计值得吸收
- 哪些实现不该照搬
- 它具体如何影响 II-1.6、child executor 和后续 runtime core

## What Changes

- 为 Runtime Harness 增加一份正式的 reference alignment spec
- 明确 `learn-claude-code` 与 `claude-code` 在当前项目中的借鉴定位
- 产出针对我方 Runtime Core / Governance / Approval / Read Model 语义的吸收边界
- 为 II-1.6 之后的实现列出推荐参考切面与非目标

## Impact

- `openspec/changes/ii1-runtime-harness-reference-alignment/*`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

