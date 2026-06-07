## Overview

The closure uses existing local trial artifacts as inputs:

- `docs/integration/local-knowledge-provider-corpus-trial/local-knowledge-provider-corpus-trial.json`
- `docs/integration/company-profile-explicit-api-local-smoke/company-profile-explicit-api-local-smoke.json`

It produces a compact caller-side result:

- `go`: both inputs are present, both are `go`, source ids/citations align, and explicit invocation boundaries remain disabled/read-only.
- `review`: inputs are present but contain non-blocking warnings or partial evidence that needs human review.
- `blocked`: required inputs are missing, failed, inconsistent, leaked boundaries, or show side effects.

## Boundaries

The closure is read-only. It does not invoke `/api/chat`, does not call the provider, does not mutate domain-agent manifests, and does not create bindings or memory/audit records.

GraphRAG remains out of scope. The closure can record that graph execution is not promoted, but it cannot promote or execute graph capabilities.

## Implementation

Add a small service in `backend/capability_runtime/business_rag_user_loop_closure.py` that:

1. Loads the corpus trial artifact.
2. Loads the explicit API smoke artifact.
3. Checks required decisions and boundary fields.
4. Extracts source id/citation evidence.
5. Exports JSON and Markdown reports.

Add `scripts/export_business_rag_user_loop_closure.py` so the user can refresh the closure after rerunning the lower-level trial scripts.

## Risks

- Stale artifacts can make the closure appear current when it is not. The report includes each input `generated_at` value and recommended next action.
- The closure proves local explicit business RAG usability, not production chat integration.

