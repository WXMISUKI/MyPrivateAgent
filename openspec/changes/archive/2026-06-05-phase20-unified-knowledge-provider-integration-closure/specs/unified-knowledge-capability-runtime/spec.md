## ADDED Requirements

### Requirement: Unified knowledge provider integration closure is explicit
MyPrivateAgent SHALL emit an explicit Phase 20 integration closure decision for the unified knowledge provider after caller-side trial evidence is available.

#### Scenario: Closure emits go after caller-side trial passes
- **WHEN** the Phase 19 trial outcome is `trial_passed`
- **AND** provider health, manifest, preflight, source binding review access, and RAG retrieve checks are all `ready`
- **THEN** the Phase 20 closure decision is `go`
- **AND** the recommended next line is grounding policy or integration hardening, not further handoff evidence expansion

#### Scenario: Closure blocks on failed required evidence
- **WHEN** the trial outcome is missing, invalid, `trial_blocked`, or includes a blocked required check
- **THEN** the Phase 20 closure decision is `blocked`
- **AND** the output identifies required recovery actions before integration can continue

#### Scenario: Closure preserves chat promotion boundary
- **WHEN** the closure decision is generated
- **THEN** default `/api/chat` retrieval injection remains disabled
- **AND** source binding, approval, audit policy, and final answer composition remain outside this phase

### Requirement: GraphRAG promotion remains separately gated
MyPrivateAgent SHALL NOT treat provider readiness evidence or RAG retrieve success as proof that GraphRAG execution is production-ready.

#### Scenario: Closure records GraphRAG boundary
- **WHEN** the Phase 20 closure decision is generated
- **THEN** it records GraphRAG as `not_promoted` unless a later provider-side GraphRAG gate proves executable graph evidence
- **AND** it permits schema discovery or structured not-implemented behavior without blocking the RAG integration closure
