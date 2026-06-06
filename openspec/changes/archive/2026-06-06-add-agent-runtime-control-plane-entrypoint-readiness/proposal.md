# Agent Runtime Control Plane Entrypoint Readiness

## Why

MyPrivateAgent now has many completed runtime, governance, provider-boundary, and domain-agent trial contracts. The next bottleneck is no longer a missing control surface; it is discoverability. A new maintainer or caller still has to jump across architecture docs, roadmap notes, OpenSpec specs, and historical changes to understand what the project is, how to verify it, and where to extend it.

This change creates a lightweight entrypoint layer so the repository itself explains the current control-plane posture without relying on conversation memory.

## What Changes

- Add a concise Agent Runtime Control Plane entrypoint document.
- Add a project entrypoint checklist for maintainers and caller-side integrators.
- Update README and architecture reading order to point at the new entrypoint.
- Mark the domain-agent evidence/trial line as a completed trial-readiness branch and route future work back to runtime/control-plane priorities.

## Non-goals

- Do not change backend runtime behavior, `/api/chat`, provider invocation, tool execution, memory, audit, trace, or source binding.
- Do not introduce a new framework adapter, default RAG injection, agent marketplace, or agent chat wrapper endpoint.
- Do not rewrite existing architecture docs or move historical `docs/change` content.
- Do not run heavy test/build commands; OpenSpec validation is enough for this documentation-only slice.

## Impact

- Documentation: new entrypoint and checklist docs, plus README/current architecture/roadmap pointers.
- OpenSpec: add canonical entrypoint readiness requirements.
- Verification: strict OpenSpec validation.
