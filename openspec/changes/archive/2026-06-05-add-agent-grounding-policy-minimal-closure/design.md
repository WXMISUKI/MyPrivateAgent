## Context

The previous grounding policy contract normalized `grounding_policy` and legacy `retrieval` manifest fields into the domain-agent registry and Runtime Surface. It remained visibility-only. After the provider trial closure, the next useful step is not direct chat injection; it is a deterministic decision gate that says whether a caller-owned response path may use returned evidence.

## Goals / Non-Goals

**Goals:**
- Preserve current manifest normalization and Runtime Surface visibility.
- Add a pure decision function over agent policy, business domain, evidence pack, and graph usage intent.
- Return `allowed`, `blocked`, or `review` with machine-readable reason codes.
- Keep all behavior side-effect-free and testable.

**Non-Goals:**
- Do not call the knowledge provider.
- Do not alter `/api/chat` execution, prompt injection, memory injection, or context packing.
- Do not create source-to-agent binding, approvals, audit records, or runtime policy writes.
- Do not execute or promote GraphRAG.

## Decisions

- The decision service reads the domain-agent registry contract rather than parsing manifests independently.
  - Rationale: registry normalization already handles `grounding_policy` and legacy `retrieval` compatibility.

- The service accepts an evidence pack-shaped dictionary instead of invoking retrieval.
  - Rationale: retrieval invocation remains a separate capability/runtime concern; this gate only decides whether already-returned evidence is usable.

- `require_citations=true` requires `evidence_pack.status=answerable` and non-empty `allowed_citations`.
  - Rationale: caller answer paths must not infer citations from raw text or fabricate citations.

- Graph usage remains blocked/review unless a later GraphRAG promotion gate exists.
  - Rationale: provider RAG readiness and graph schema discovery do not prove executable graph evidence.

## Risks / Trade-offs

- The gate may initially feel conservative -> This is intentional until representative eval scenarios approve behavior promotion.
- The service does not call live provider readiness -> Keep it deterministic; provider readiness belongs to trial/handoff artifacts.
- Existing `/api/chat` users see no behavior improvement yet -> This phase creates the safety gate needed before a later chat injection change.
