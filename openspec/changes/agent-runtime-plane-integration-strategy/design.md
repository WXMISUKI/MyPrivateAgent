## Context

MyPrivateAgent already owns a strong control-plane surface: runtime contracts, query/run read models, governance timeline, approval, audit, provider management, domain agent registry, and framework adapter SPI. The missing piece is a disciplined runtime-plane strategy that lets the project use mature execution systems without becoming a second LangGraph, AgentRun, or low-code orchestration platform.

The team needs a path that supports future runtime development while keeping the project bounded. The main risk is not technical impossibility; it is uncontrolled expansion. Once the project starts solving execution, deployment, sandboxing, checkpointing, and worker concerns all at once, the control plane will become hard to reason about and hard to maintain.

Stakeholders:

- Core maintainers who need clear architecture boundaries.
- Domain agent authors who need a predictable runtime entry path.
- Governance consumers who need normalized events, approvals, and traces.
- Future adapter authors who need an authoring and promotion contract.

## Goals / Non-Goals

**Goals:**

- Make the runtime-plane strategy explicit and durable.
- Separate control-plane ownership from execution-plane ownership.
- Define a first-class adapter contract for mature runtimes and frameworks.
- Keep future execution work behind a bounded envelope so the project does not grow into a platform clone.
- Provide phased adoption and review checkpoints so the team can stop, reflect, and adjust after each stage.
- Ensure new code follows explicit directory and contract boundaries.

**Non-Goals:**

- Do not implement a new execution engine inside MyPrivateAgent.
- Do not move all existing modules into new directories in one pass.
- Do not change the default `/api/chat` behavior in this change.
- Do not promote `AgentHarnessFacade` out of preview.
- Do not replace current governance surfaces with framework-native payloads.
- Do not introduce a new low-code builder or visual workflow platform.

## Decisions

### 1. Use mature runtimes as execution dependencies, not as project identity

We will treat AgentRun, LangGraph, ADK, and OpenAI Agents SDK as execution/runtime candidates that can be consumed through adapters.

Rationale:

- They already solve the hard runtime problems we do not want to rebuild.
- They can be swapped or combined if the adapter boundary stays stable.
- They let MyPrivateAgent stay focused on what it uniquely owns: contracts, governance, approvals, audit, and cataloging.

Alternatives considered:

- Self-build the runtime plane. Rejected because it duplicates mature infrastructure and increases maintenance risk.
- Promote MyPrivateAgent execution helpers into the production runtime. Rejected because it blurs control-plane and execution-plane ownership.

### 2. Introduce a normalized `ExecutionAdapter v1`

Every runtime integration will pass through a normalized adapter shape that converts framework-native requests, events, results, interruptions, and errors into local contracts.

Rationale:

- Governance and UI should consume one stable envelope.
- Adapter mapping makes framework choice a deployment detail rather than a domain-wide dependency.
- It creates a clean place to record readiness, promotion, and non-goals.

Alternatives considered:

- Allow framework-native payloads directly into governance and frontend contracts. Rejected because it creates hidden coupling and makes migration expensive.

### 3. Enforce directory boundaries for future work

New work will be organized by role:

- `control_plane` for governance, contracts, registry, approval, trace, audit, and read models.
- `runtime_plane` for execution-facing contracts, runtime abstractions, and adapter-facing types.
- `framework_adapters` for framework-specific normalization code.
- `domain_agents` for agent assets, prompts, tools, policies, and evaluation data.
- `capability_runtime` for tool/MCP/skill/provider wiring.

Rationale:

- Directory boundaries are the easiest way to keep teams from mixing concerns.
- They make review and ownership visible.
- They give us a future path for gradual extraction without forcing a large rewrite now.

Alternatives considered:

- Keep everything in the current mixed service tree. Rejected because it keeps ownership fuzzy.

### 4. Treat the first phase as a freeze-and-align stage

Before expanding runtime work, the team will close the current control-plane positioning, lock the stop conditions, and define what not to build.

Rationale:

- The project already has enough surface area to become noisy.
- A freeze stage gives the team a shared checkpoint before adding runtime work.

Alternatives considered:

- Continue expanding harness functionality immediately. Rejected because it risks growing the wrong subsystem.

### 5. Adopt a stage-gated rollout model

The rollout stages will be:

- Stage 0: freeze and close the control-plane story.
- Stage 1: build minimal runtime-plane slices through adapters.
- Stage 2: connect read-only governance and approval bridge.
- Stage 3: harden templates, quality gates, and promotion rules.

Rationale:

- This sequence keeps the system useful while preventing uncontrolled scope creep.
- Each stage has a natural review point.

Alternatives considered:

- Build the full runtime plane first, then add governance later. Rejected because it hides risk until late.

## Risks / Trade-offs

- [Risk] The adapter layer becomes too abstract and slows delivery. → Mitigation: keep the first version minimal and encode only the contract fields we need for governance and execution normalization.
- [Risk] Directory boundaries are adopted in theory but ignored in practice. → Mitigation: require new work to land in the new boundaries, while treating old locations as compatibility zones only.
- [Risk] The team still tries to extend `AgentHarnessFacade` as the main runtime. → Mitigation: keep it preview-only, and require promotion decisions for anything that touches production execution.
- [Risk] The runtime-plane strategy is too open-ended. → Mitigation: use stage gates, explicit non-goals, and review tasks at the end of each phase.

## Migration Plan

1. Freeze the current control-plane story in docs and specs.
2. Add the runtime-plane integration strategy spec and adapter checklist delta.
3. Update the project entrypoint and roadmap docs to show the new direction.
4. Start the first runtime-plane slice as a small adapter-backed proof, not a framework rewrite.
5. After each stage, perform a written review:
   - Did we stay within the agreed boundary?
   - Did we avoid growing a hidden platform?
   - Did the adapter contract remain stable?
   - Is the next stage still justified?

Rollback strategy:

- If runtime work starts to balloon, stop adding capability and return to the freeze stage.
- If an adapter boundary proves wrong, adjust the adapter contract first instead of leaking framework details into control-plane contracts.
- If a new runtime concern appears that is not essential to governance, keep it outside MyPrivateAgent until explicitly promoted.

## Open Questions

- Which runtime candidate should be used for the first production-style slice: AgentRun first, LangGraph first, or a dual prototype?
- Which normalized events are required in the first adapter envelope beyond request, event, result, approval interrupt, and error?
- Which governance read models must be available on day one versus later stages?
- Should the first stage create a dedicated `backend/runtime_plane/` tree immediately, or only document it while keeping implementation under the existing tree for one cycle?
