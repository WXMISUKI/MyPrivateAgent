# Design: Local RAG Question Trial Entrypoint

## Intent
Provide a small caller-side operator endpoint that answers the practical question: "Given this already-ingested local source, can MyPrivateAgent ask a business question and inspect grounded evidence?"

## Contract
Input:
- `source_id`: local provider source to query.
- `question`: business question.
- `provider_base_url`: unifiedKnowledgeRAG provider base URL.
- `top_k`: retrieval count.
- Optional `provider_api_key`, `timeout_seconds`, `output_dir`.

Output:
- `decision`: `go`, `review`, or `blocked`.
- `reason_code`: stable machine-readable reason.
- `answer_status`: provider answer status, usually `answered` or `insufficient_evidence`.
- `answer`: returned grounded answer text when present.
- `citations`: answer citations.
- `evidence_pack.status`: provider evidence status when present.
- `retrieval`: compact retrieval summary.
- `report_path`: JSON and Markdown report paths when exported.

## Decision Rules
- `blocked`: provider request fails, response contract is malformed, or source/question input is missing.
- `review`: provider answers with citations outside retrieved documents or returns an unexpected answer status.
- `go`: provider returns `answered` with valid retrieved citations, or returns `insufficient_evidence` without unsupported citations.

## Boundary
The entrypoint is a local diagnostics/use-trial surface only. It does not decide final business answer policy and does not become the main chat path. If repeated local trials are successful, later work may productize a caller-side business workflow, but that is outside this change.
