# Layout Capability Acceptance Report (2026-06-01)

## Scope

Capability under validation: `document.layout.parse` and baseline `document.ocr.extract` runtime availability.

Environment:

- MyPrivateAgent: `http://127.0.0.1:8003`
- OCR provider: `http://127.0.0.1:8080`
- Layout provider: `http://127.0.0.1:8081` (`/layout-parsing`)

## Sample Set

- `D:\AI\ocr\picture.jpg`
- `D:\AI\ocr\table.png`
- `D:\AI\ocr\入职通知书.pdf`

## OCR Invocation Summary

All three samples completed successfully via capability runtime invoke endpoint.

| File | HTTP | ok | text_length | pages | blocks | warnings |
|---|---:|---:|---:|---:|---:|---:|
| picture.jpg | 200 | true | 447 | 1 | 21 | 0 |
| table.png | 200 | true | 155 | 1 | 24 | 0 |
| 入职通知书.pdf | 200 | true | 423 | 1 | 19 | 0 |

## Quality Notes

1. Content extraction is stable for all three files and no structured provider errors were returned.
2. `table.png` recognized tabular textual content; however, this is still OCR text/blocks output, not structured table reconstruction from `document.layout.parse`.
3. Minor OCR character-level noise is present in long text (`7000.00` recognized with occasional character drift), acceptable for baseline OCR but should be tracked for downstream precision-sensitive workflows.

## Layout Invocation Summary

All three samples completed successfully via `document.layout.parse`.

| File | ok | markdown_len | elements | tables | pages | warnings |
|---|---:|---:|---:|---:|---:|---:|
| picture.jpg | true | 1255 | 0 | 0 | 1 | 0 |
| table.png | true | 813 | 0 | 1 | 1 | 0 |
| 入职通知书.pdf | true | 1245 | 0 | 0 | 1 | 0 |

Layout provider metadata snapshot:

- `LAYOUT_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8081`
- `LAYOUT_CAPABILITY_PROVIDER_INVOKE_PATH=/layout-parsing`

## Acceptance Decision

Current decision for Stage `2C`:

- `Pass` for baseline runtime connectivity and OCR extraction stability.
- `Pass` for `document.layout.parse` provider endpoint alignment and sample-set acceptance.

## Next Actions

1. Add one dense multi-page PDF sample to verify `max_pages` and multi-page merge behavior.
2. Add one complex multi-column sample to improve `elements` extraction completeness checks.
3. Use this report as the baseline when enabling VLM comparison in Stage `3A/3B`.
