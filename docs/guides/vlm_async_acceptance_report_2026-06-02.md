# VLM Async Acceptance Report (2026-06-02)

## Scope

Capability under validation: `document.vlm.parse.async`.

This Stage 3B acceptance validates the async submit/status lifecycle through MyPrivateAgent. The local async wrapper provider delegates parsing to the existing PP-StructureV3 layout service.

## Environment

- MyPrivateAgent: `http://127.0.0.1:8000`
- Layout upstream: `http://127.0.0.1:8081/layout-parsing`
- VLM async wrapper: `http://127.0.0.1:8082`
- Capability endpoint: `POST /api/capabilities/document.vlm.parse.async/invoke`

Wrapper startup:

```bash
python backend/scripts/document_vlm_async_wrapper_provider.py --host 127.0.0.1 --port 8082 --upstream-base-url http://127.0.0.1:8081 --upstream-invoke-path /layout-parsing
```

Smoke command:

```bash
python backend/scripts/document_vlm_async_smoke.py --runtime-base-url http://127.0.0.1:8000 --samples-dir D:\\AI\\ocr --task summarize --poll-timeout 120 --poll-interval 2 --report docs/guides/vlm_async_acceptance_report.json
```

## Result Summary

| File | ok | status | progress | polls | summary_length | warnings |
|---|---:|---|---:|---:|---:|---:|
| picture.jpg | true | succeeded | 1.0 | 7 | 547 | 0 |
| table.png | true | succeeded | 1.0 | 5 | 549 | 0 |
| 入职通知书.pdf | true | succeeded | 1.0 | 7 | 541 | 0 |

## Decision

Stage 3B is accepted for local async lifecycle validation:

- `document.vlm.parse.async` is discoverable through MyPrivateAgent.
- Submit returns a `job_id`.
- Polling reaches terminal `succeeded` status.
- Failed jobs remain queryable through the wrapper contract.
- Report output is compact by default to avoid committing large provider raw payloads.

## Known Boundaries

- The wrapper uses in-memory jobs; restart loses job state.
- This is not a production queue or GPU scheduler.
- Current semantic output is derived from PP-StructureV3 markdown, not a dedicated PaddleOCR-VL model.
- Real PaddleOCR-VL integration can replace the upstream provider later without changing MyPrivateAgent's async capability contract.
