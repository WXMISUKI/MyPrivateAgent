## 1. Specification

- [x] 1.1 Validate the OpenSpec change and confirm proposal, design, and specs are internally consistent.
- [x] 1.2 Confirm `agent-grounding-policy` captures policy fields, readiness semantics, and enforcement non-goals.
- [x] 1.3 Confirm delta specs only extend `domain-agent-asset-registry` and `unified-knowledge-capability-runtime` without changing default chat behavior.

## 2. Backend Contract

- [ ] 2.1 Add grounding policy normalization for `grounding_policy` and compatibility `retrieval` manifest fields.
- [ ] 2.2 Preserve normalized grounding policy in `domain_agent_registry.agents[]`.
- [ ] 2.3 Add a focused grounding policy readiness read model or status block that stays visibility-only.
- [ ] 2.4 Keep `/api/chat` retrieval injection disabled and explicitly document the enforcement boundary in the contract.

## 3. Documentation

- [ ] 3.1 Update `docs/guides/domain_agent_development_guide.md` with the durable `grounding_policy` manifest section.
- [x] 3.2 Update roadmap docs to mark grounding policy as the active internal control-plane slice while external provider work is paused.
- [ ] 3.3 Document the later promotion path for default chat retrieval injection and required eval gate.

## 4. Verification

- [ ] 4.1 Add focused tests for manifest grounding policy normalization.
- [ ] 4.2 Add focused tests for Runtime Surface visibility and stable existing knowledge registries.
- [ ] 4.3 Run `python -m pytest tests/agent_framework/test_domain_agent_registry_service.py -q`.
- [ ] 4.4 Run `cmd /c openspec validate add-agent-grounding-policy-contract --strict`.
- [ ] 4.5 Run `cmd /c openspec validate --all --strict`.

## 5. Archive

- [ ] 5.1 Archive the change after implementation tasks are complete.
- [ ] 5.2 Confirm canonical specs contain the final grounding policy decisions.
