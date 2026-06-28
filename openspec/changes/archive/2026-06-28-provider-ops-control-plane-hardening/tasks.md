## 1. Spec and Contract Shape

- [x] 1.1 Add the provider ops read model contract and keep it read-only.
- [x] 1.2 Define bounded posture fields for credentials, quota, rate limit, cost, SLA, and fallback.
- [x] 1.3 Define fail-closed behavior for missing or unknown operational evidence.

## 2. Backend Implementation

- [x] 2.1 Implement a provider ops aggregation service that derives posture from existing provider metadata.
- [x] 2.2 Expose the provider ops read model through Runtime Surface or a dedicated read endpoint.
- [x] 2.3 Keep secrets, raw payloads, and runtime mutation out of the response.

## 3. Verification

- [x] 3.1 Add focused backend tests for healthy, degraded, and unknown provider ops posture.
- [x] 3.2 Add focused backend tests ensuring no secrets or raw provider payloads are returned.
- [x] 3.3 Run strict OpenSpec validation and focused provider ops tests.

## 4. Docs And Archive

- [x] 4.1 Update architecture and roadmap docs to mention the provider ops control plane.
- [x] 4.2 Archive the change after implementation and validation are complete.
