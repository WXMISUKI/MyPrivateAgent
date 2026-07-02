## 1. Spec

- [x] 1.1 Extend Runtime Surface and governance-view specs for read-only provider ops visibility.

## 2. Backend

- [x] 2.1 Add `provider_ops` to the runtime profile assembler using the existing provider ops service.
- [x] 2.2 Keep the runtime profile stable when provider ops data is empty or degraded.

## 3. Frontend

- [x] 3.1 Render a compact Provider Ops contract section in `RuntimeSurfacePanel`.
- [x] 3.2 Keep the panel diagnostic-only and mutation-free.

## 4. Verification

- [x] 4.1 Add focused backend coverage for `provider_ops` in runtime profile.
- [x] 4.2 Add focused frontend coverage for Runtime Surface provider ops rendering.
- [x] 4.3 Run strict OpenSpec validation and focused tests.

## 5. Archive

- [x] 5.1 Archive the change after implementation and validation complete.
