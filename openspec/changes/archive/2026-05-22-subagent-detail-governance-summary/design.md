# Design: subagent detail governance summary

## Decision

Reuse `formatRuntimeContractGateSummary()` because Governance Timeline and event cards already consume it through `formatPayloadSummary()`. The change only adds one fragment to the existing summary string.

## Display Contract

Runtime contract warning summaries should become:

```text
runtime_contract=degraded · failed=1 · missing_payloads=2 · approval_replay=missing · subagent_detail=covered
```

When gate status is `unknown`, the label should be `subagent_detail=unknown`.

When coverage is absent or false and status is not unknown, the label should be `subagent_detail=missing`.
