## 1. Provider Consumption Contract

- [x] 1.1 Inspect existing capability runtime service, routers, and knowledge provider health/readiness shapes.
- [x] 1.2 Add a provider consumption read model/service that lists configured providers and normalizes status into `ready / review / blocked / unreachable / gated / disabled / unconfigured / unknown`.
- [x] 1.3 Map the existing knowledge capability provider into the generic provider entry, including compact boundaries for default chat grounding, GraphRAG, and source binding automation.

## 2. Management API

- [x] 2.1 Add read-only provider management endpoints for provider list and provider detail/readiness.
- [x] 2.2 Add an explicit provider capability invoke endpoint that validates provider ownership and delegates to capability runtime.
- [x] 2.3 Add a compact provider evidence preview endpoint that returns readiness, capabilities, gates, warnings, boundaries, and recommended next action.

## 3. Verification

- [x] 3.1 Add focused backend tests for disabled/unconfigured provider behavior.
- [x] 3.2 Add focused backend tests for configured knowledge provider readiness and boundary preservation.
- [x] 3.3 Add focused backend tests for explicit invoke delegation and fail-closed capability ownership validation.
- [x] 3.4 Run focused pytest for the provider consumption contract.
- [x] 3.5 Run `openspec validate --all --strict`.

## 4. Documentation and Archive

- [x] 4.1 Update `docs/architecture/runtime_contracts.md` with the provider consumption contract and boundaries.
- [x] 4.2 Update `docs/roadmap/next_phase_hardening.md` with the completed next-stage provider consumption direction.
- [x] 4.3 Update `docs/guides/capability_runtime_registry.md` with the generic provider management interface.
- [x] 4.4 Archive the completed OpenSpec change after implementation and validation.
