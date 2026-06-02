## 1. Spec

- [x] 1.1 Add `document.vlm.parse.async` in `unified-capability-runtime` spec delta.
- [x] 1.2 Define async submit/status input and async output schema.
- [x] 1.3 Specify accepted `status` set and normalization rules.
- [x] 1.4 Define async env toggles and provider error contracts.

## 2. Backend

- [x] 2.1 Add env variables:
  - `VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH`
  - `VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE`
- [x] 2.2 Inject async paths through `registry.py` to `build_http_document_vlm_capabilities`.
- [x] 2.3 Implement path normalization for async submit/status and route substitution.
- [x] 2.4 Add async status normalization in provider result mapping.
- [x] 2.5 Add backend tests for status alias and custom async paths.

## 3. Docs/Guides

- [x] 3.1 Update capability runtime and VLM provider docs with async section and env examples.
