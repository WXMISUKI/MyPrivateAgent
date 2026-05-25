## Why

当前 child executor 输出已经不再只停留在 `output_payload`，而是进入了：

- replay record
- compact artifact summary
- Runtime Surface 前端消费面

这说明 child output 语义已经具备继续升级的基础。下一步真正缺的，不再是“多展示几个字段”，而是：

- 不同 child intent 应该怎样合并到 parent
- 哪些语义应该 `replace_latest`
- 哪些语义应该 `append_dedup`
- 哪些结果只适合进入 replay / artifact，不应直接污染 parent 主摘要

如果不先把 merge behavior contract 写清，后续 child executor 很容易退化成“每种输出都往 parent metadata 随便塞一点”的状态。

## What Changes

- 为 child executor output 增加正式 `intent taxonomy`
- 为 parent merge 增加明确 `merge_behavior` / `merge_mode`
- 让 replay、summary、parent metadata 同步暴露 merge 语义
- 为后续真实 child executor 和 worker runtime 提供稳定 merge contract

## Impact

- `backend/agent_framework/sdk.py`
- `tests/agent_framework/test_embedded_runtime_sdk.py`
- `tests/agent_framework/test_agent_harness_facade.py`
- `docs/architecture/runtime_contracts.md`
- `docs/roadmap/next_phase_hardening.md`

