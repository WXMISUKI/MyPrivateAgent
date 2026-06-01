## 1. Spec

- [ ] 1.1 Add `document.layout.parse` requirement deltas in `unified-capability-runtime`.
- [ ] 1.2 Define input/output schema examples for markdown and table extraction.

## 2. Backend

- [x] 2.1 Add layout capability provider registration behind explicit env toggle.
- [x] 2.2 Implement provider payload mapping for PP-StructureV3.
- [x] 2.3 Normalize provider output to `markdown/elements/tables/pages/artifacts/warnings/raw`.
- [x] 2.4 Add structured error mapping for invalid input and provider failures.

## 3. Frontend

- [x] 3.1 Add diagnostics invoke action for `document.layout.parse`.
- [x] 3.2 Render markdown, tables, and raw JSON sections in diagnostics panel.

## 4. Verification

- [ ] 4.1 Run `python -m pytest tests/agent_framework/test_capability_http_provider.py -q`.
- [ ] 4.2 Run `npm run test -- CapabilityProviderDiagnosticsPanel`.
