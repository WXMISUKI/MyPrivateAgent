## Why

MyPrivateAgent has a working Framework Adapter SPI, precheck flow, external pilot boundary, and query-control mapping, but new adapter authors still need a single machine-readable checklist that explains the required contracts before any framework can be promoted. After the RAG provider closure, the next highest-value step is to make external framework/provider onboarding repeatable without touching default main chat execution.

## What Changes

- Add a side-effect-free framework adapter authoring checklist contract.
- Add a bounded promotion gate summary for an adapter candidate based on checklist sections and existing precheck evidence.
- Require checklist sections for adapter identity, lifecycle mapping, readiness/precheck, governance/timeline, promotion gate, and non-goals.
- Preserve the boundary that framework adapters do not enter default main chat without a later explicit promotion.

收口对象：Framework Adapter authoring checklist / promotion review contract.

非目标：

- Do not add a new real framework adapter.
- Do not enable LangGraph/CrewAI/OpenAI Agents SDK/Qwen-Agent execution by default.
- Do not change `/api/chat` routing.
- Do not create background workers, tool execution changes, or source/provider bindings.
- Do not redesign existing Framework Adapter Runtime Service.

## Capabilities

### New Capabilities

- `framework-adapter-authoring-checklist`: defines the minimum machine-readable checklist and promotion review contract for new framework adapters.

### Modified Capabilities

- None.

## Impact

- Backend: add a compact side-effect-free checklist/promotion review method around the existing framework adapter runtime service.
- Tests: focused tests for checklist fields, blocked default promotion, and ready/review status based on adapter precheck evidence.
- Docs/specs: runtime contracts and next phase hardening roadmap.
- APIs: no new public endpoint in this slice.
