## Context

The local knowledge path now has a proven minimal chain:

```text
unifiedKnowledgeRAG provider
  -> company_profile_2025_trial source
  -> MyPrivateAgent company_profile manifest
  -> POST /api/domain-agents/company_profile/live-grounded-answer
  -> company_profile explicit API local smoke
```

The remaining usability gap is not another evidence layer. It is a single local doctor report that tells a developer whether the above path is usable and, if not, which concrete local action to take next.

## Goals

- Extend the existing doctor entrypoint instead of creating a parallel readiness tool.
- Reuse the existing explicit API smoke service.
- Produce a compact local report suitable for CLI and API consumers.
- Keep the report deterministic and machine-readable.
- Preserve the same boundaries as the explicit API smoke.

## Non-Goals

- Do not connect retrieval to `/api/chat`.
- Do not start, stop, or supervise the provider process.
- Do not create source-to-agent bindings.
- Do not write memory, audit, trace, learning, or remediation records from CLI mode.
- Do not parse PDFs, run OCR, mutate provider data, execute GraphRAG, or call a real LLM.
- Do not add frontend UI in this phase.
- Do not implement the broader multi-agent scheduler roadmap.

## Approach

Add a `knowledge_runtime` doctor scope that delegates to the current company-profile smoke exporter in memory and normalizes the result:

```text
doctor.py --knowledge-runtime
  -> DoctorRuntimeService.run_knowledge_runtime_report(...)
  -> run_company_profile_explicit_api_local_smoke(...)
  -> local doctor report
```

The report should include:

- `scope = "knowledge_runtime"`
- `status = "ok" | "warn" | "fail"`
- `decision = "go" | "review" | "blocked"`
- `reason_code`
- normalized checks
- blockers and warnings
- recommended next action
- endpoint, provider URL, agent id, domain, query
- boundary
- compact smoke summary

## Decision Rules

- `go`: explicit API smoke returns `decision=go`.
- `review`: explicit API smoke returns `decision=review`.
- `blocked`: explicit API smoke returns `decision=blocked` or throws a local runtime error.

CLI exit code:

- `0` for `go`
- `2` for `review`
- `1` for `blocked`

## Recovery Actions

The doctor should map common reason codes to actionable local next steps:

- provider unreachable: start `unifiedKnowledgeRAG` on the selected provider URL.
- route or contract failure: run the focused MyPrivateAgent smoke tests.
- missing citation/source/evidence: rerun the provider corpus trial and verify `company_profile_2025_trial`.
- unsafe boundary or secret leakage: stop using the result and fix MyPrivateAgent boundary handling.

## API Parity

The CLI is the primary target. `/api/doctor?knowledge_runtime=true` may expose the same report as a read-only runtime API for later settings-page integration, but this phase does not add UI.
