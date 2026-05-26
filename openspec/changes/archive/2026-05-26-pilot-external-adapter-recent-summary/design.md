## Context

`main_chat` is the complete query workspace baseline. `subagent_lane` already has a recent summary pilot and a dedicated query detail contract. `external_adapter` currently records Query Control timeline events through the external adapter runtime service, but Runtime Surface still reports its promotion evidence as `recent_summary_status = unavailable`.

The previous change made promotion records mandatory before implementation resumes. This change records the resume decision implicitly through specs and implements only the shallowest eligible target layer: `recent_summary`.

## Goals / Non-Goals

**Goals:**

- Build `external_adapter_recent_summary` from persisted Query Control trace events where `payload.channel = external_adapter`.
- Reuse the same stable recent summary field set: `query_id`, `latest_stage`, `latest_summary`, `latest_timestamp`, and `recording_state`.
- Expose the contract in Runtime Profile and through a dedicated read endpoint.
- Let Channel Promotion Gate use the real summary status while continuing to block `query_detail`, `query_history`, and `query_workspace`.

**Non-Goals:**

- No query detail contract.
- No history pagination.
- No workspace UI shell.
- No generic recent summary service extraction.
- No changes to external adapter execution, event recording, adapter registry, or provider behavior.

## Decisions

1. Add an `ExternalAdapterRecentSummaryBuilder` next to the existing query read model builders.

   Rationale: `subagent_lane` uses a channel-specific builder. Keeping the external adapter builder channel-specific follows the current recent summary abstraction note and avoids premature generic abstraction.

2. Use Query Control trace payloads as the only source.

   Rationale: external adapter already records mapped lifecycle events into `source = query_control`. The summary must not infer state from framework adapter-specific payloads that the frontend would need to interpret.

3. Add a dedicated endpoint mirroring `subagent-lane-recent-summary`.

   Rationale: Runtime Surface can expose the field in the profile for summary views, while the endpoint provides the same narrow read-model boundary without requiring consumers to fetch the full profile.

4. Keep deeper layers blocked in Channel Promotion Gate.

   Rationale: recent summary evidence proves only latest-stage summary semantics. It does not prove stable stage-chain detail, history pagination, or workspace readiness.

## Risks / Trade-offs

- Summary behavior may duplicate subagent builder logic -> Mitigation: keep the duplication intentionally small until a third real recent summary sample exists.
- Existing traces may be absent in local environments -> Mitigation: return `recording_state = no_records` with a machine-readable reason.
- Consumers may over-read this as detail readiness -> Mitigation: promotion gate keeps `query_detail / query_history / query_workspace` blocked for `external_adapter`.
