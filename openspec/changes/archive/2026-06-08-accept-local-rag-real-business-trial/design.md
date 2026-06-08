# Design: Local RAG Real Business Trial Acceptance

## Intent
Create one small, operator-friendly acceptance artifact for a real local business document trial. It answers:

- Did the upload-to-use loop complete?
- Can answerable business questions be answered with citations?
- Does an unrelated negative-control question fail closed as insufficient evidence?
- If not, which next workstream should be opened?

## Inputs
- `upload_report`: JSON report from `document-rag-upload-to-use-loop`, optional but preferred.
- `question_reports`: JSON reports from `local-rag-question-trial-entrypoint`.
- Optional identity fields: `source_id`, `document_path`, `provider_base_url`.

## Decision Rules
- `blocked` when upload is blocked, required question reports are missing, provider calls failed, or malformed report contracts are supplied.
- `review` when upload is review, answerable questions return review/insufficient evidence, negative-control questions return answer text/citations, or citations are invalid.
- `go` when upload is go and all supplied question reports meet their expected mode.

## Expected Modes
- `answerable`: expected `decision=go`, `answer_status=answered`, at least one citation, and no invalid citations.
- `insufficient_evidence`: expected `decision=go`, `answer_status=insufficient_evidence`, and no citations.

## Follow-Up Classification
The report should classify the next action without over-prescribing implementation:

- `operator_flow`: upload entrypoint or local operation issue.
- `parser_ocr`: document conversion produced weak or missing RAG text.
- `citation_evidence`: citations, evidence pack, or allowlist behavior is unsafe.
- `retrieval_quality`: source exists but answerable questions cannot retrieve/use evidence.
- `provider_availability`: provider HTTP/service path failed.
- `no_follow_up_required`: the current trial is accepted.

## Boundary
This report is not a production promotion gate. It exists to prevent speculative optimization and to decide whether the next change should be user-flow, parser, citation/evidence, retrieval-quality, or availability focused.
