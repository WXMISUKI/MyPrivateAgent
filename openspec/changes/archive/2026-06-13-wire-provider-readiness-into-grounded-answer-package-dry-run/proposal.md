## Why

The grounded-answer trial surface now exposes compact `provider_readiness` from caller-supplied Knowledge Provider governance readiness. The next useful closure is to carry that same readiness evidence into the deterministic package dry-run, so future answer composition can consume one bounded package without reinterpreting promotion payloads.

## What Changes

- Extend grounded-answer package dry-run output to preserve trial report `provider_readiness`.
- Keep package status aligned with trial status for ready, review, blocked, provider unreachable, catalog degraded, and GraphRAG gated cases.
- Preserve provider blockers, warnings, and promotion boundaries in the package.
- Keep package dry-run deterministic and side-effect-free.

收口对象：MyPrivateAgent grounded-answer package dry-run input bundle.

非目标：

- Do not call `unifiedKnowledgeRAG` from package dry-run.
- Do not enable default `/api/chat` retrieval injection.
- Do not generate final answers or invoke models.
- Do not execute GraphRAG.
- Do not create source binding, audit, trace, approval, or memory state.
- Do not optimize provider retrieval strategy.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `domain-agent-grounded-answer-package-dry-run`: package dry-run must preserve trial-supplied provider readiness evidence and boundaries.

## Impact

- Backend service: grounded-answer package dry-run assembly.
- Tests: focused package dry-run cases for provider ready, catalog degraded review, provider unreachable blocked, and GraphRAG gated blocked.
- Docs/specs: package dry-run spec, runtime contracts, and next-phase hardening notes.
- APIs: no new endpoint is required; existing package dry-run response may gain compact provider readiness fields.
