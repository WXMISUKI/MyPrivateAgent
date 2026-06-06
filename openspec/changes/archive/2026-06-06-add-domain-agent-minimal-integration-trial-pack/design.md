# Design

## Boundary

The minimal integration trial pack is an orchestration layer over existing read-only services:

1. Read a compact caller evidence payload.
2. Run `DomainAgentGroundedAnswerTrialService`.
3. Feed the trial report into `DomainAgentGroundedAnswerPackageService`.
4. Feed the package into `DomainAgentGroundedAnswerCompositionTrialService`.
5. Return one compact status report.

It must not invoke FastAPI, `/api/chat`, providers, models, tools, memory writers, audit writers, trace writers, or source-binding state.

## Payload Shape

The payload is intentionally close to the existing trial endpoint request:

- `agent_id`
- `domain`
- `query`
- `graph_requested`
- `evidence_pack`
- `provider_evidence`
- `promptops_evidence`
- `memoryops_evidence`
- `eval_evidence`

The example payload is documentation and a smoke input. It is not a production credential, provider fixture, or generated artifact.

## Status Aggregation

The pack reports:

- `go` when trial is `go`, package is `ready`, and composition is `ready`.
- `review` when no stage is blocked and at least one stage is `review`.
- `blocked` when any stage is blocked.

The report includes stage statuses, recommended next action, blockers, warnings, citation allowlist, preview availability, and a boundary section.

## Script

Add `backend/scripts/domain_agent_trial_smoke.py`.

Default behavior:

- load `docs/examples/domain_agent_trial_payload.json`
- run the pack using repository domain-agent manifests
- print compact JSON to stdout
- return exit code `0` for `go` and `review`
- return exit code `2` for `blocked`
- return exit code `1` for invalid input or unexpected execution errors

The non-zero blocked exit code lets CI or a caller distinguish "script failed" from "trial completed and found blockers".

## Testing

Use focused unittest coverage:

- `go` payload produces `overall_status = go`
- missing PromptOps evidence produces `overall_status = review`
- degraded provider evidence produces `overall_status = blocked`
- script payload loader can run from the checked-in example

## Documentation

Update the domain-agent guide with the minimal caller sequence:

```text
GET /api/agents
inspect capability_linkage
POST /api/domain-agents/{agent_id}/grounded-answer-trial
POST /api/domain-agents/{agent_id}/grounded-answer-package-dry-run
POST /api/domain-agents/{agent_id}/grounded-answer-composition-trial
optional: python backend/scripts/domain_agent_trial_smoke.py --payload docs/examples/domain_agent_trial_payload.json
```
