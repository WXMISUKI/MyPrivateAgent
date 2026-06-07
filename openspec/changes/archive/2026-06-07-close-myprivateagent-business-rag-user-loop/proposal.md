## Why

The provider and MyPrivateAgent explicit grounded-answer API can already run against the local company profile corpus, but the project still needs one small caller-side closure that answers: can a user-facing local business RAG trial proceed now?

This change keeps the next step lightweight by summarizing existing trial artifacts into a single `go / review / blocked` decision instead of expanding provider evidence or wiring RAG into default `/api/chat`.

## What Changes

- Add a caller-side business RAG user-loop closure report that reads the existing local corpus trial and company-profile explicit API smoke artifacts.
- Export JSON and Markdown artifacts under `docs/integration/business-rag-user-loop-closure/`.
- Add a focused test for `go`, missing artifact, and boundary failure cases.
- Update local architecture/docs with the new closure entrypoint.

收口对象：`company_profile_2025_trial` 本地语料通过 MyPrivateAgent 显式接口完成业务问答试用闭环。

非目标：不启用默认 `/api/chat` 检索注入，不创建 source-to-agent binding，不写 memory/audit/trace，不启动或修改 provider 服务，不接入 GraphRAG，不引入新向量数据库，不改变真实 LLM 生成链路。

## Capabilities

### New Capabilities

- `myprivateagent-business-rag-user-loop`: Caller-side local business RAG closure over provider corpus trial and explicit grounded-answer API smoke.

### Modified Capabilities

- None.

## Impact

- Affected code:
  - `backend/capability_runtime/`
  - `scripts/`
  - `tests/agent_framework/`
- Affected docs/artifacts:
  - `docs/integration/business-rag-user-loop-closure/`
  - `docs/architecture/current_architecture.md`
- APIs: none. This is an explicit local export script and report only.
- Dependencies: none.

