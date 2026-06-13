# Knowledge Provider Caller Loop

## Purpose

This runbook closes the MyPrivateAgent-side caller loop for using `unifiedKnowledgeRAG` as a lightweight external knowledge provider.

It proves explicit local caller use. It does not enable default `/api/chat` retrieval injection, source-to-agent binding automation, GraphRAG execution, provider runtime promotion, or final answer policy changes.

## Preconditions

Start `unifiedKnowledgeRAG` first:

```powershell
cd D:\AI\AIcode\unifiedKnowledgeRAG
conda activate GRAPHRAG
uvicorn app.main:app --reload --port 8020
```

Confirm the provider is reachable:

```powershell
Invoke-RestMethod http://127.0.0.1:8020/health
Invoke-RestMethod http://127.0.0.1:8020/api/provider/preflight
Invoke-RestMethod http://127.0.0.1:8020/api/provider/source-bindings
```

Provider-side local closure evidence lives in:

```text
D:\AI\AIcode\unifiedKnowledgeRAG\docs\integration\myprivateagent-provider-use-loop\myprivateagent-provider-use-loop.md
```

## MyPrivateAgent Configuration

Enable the provider for the current MyPrivateAgent process:

```powershell
cd D:\AI\AIcode\MyPrivateAgent
$env:ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER="true"
$env:KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL="http://127.0.0.1:8020"
```

Optional timeout:

```powershell
$env:KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS="5"
```

These are caller-owned runtime settings. Do not write provider API keys into generated JSON or Markdown artifacts.

## Provider Discovery Expectations

When enabled, the capability registry should expose:

- `knowledge.rag.retrieve`
- `knowledge.graph.query`

Document RAG retrieve is the usable path for this closure. Graph query remains a planned or separately gated boundary and must not be treated as production GraphRAG execution.

## Caller Smoke

Run the explicit caller smoke:

```powershell
python backend/scripts/company_profile_explicit_api_local_smoke.py `
  --provider-base-url http://127.0.0.1:8020
```

Expected artifacts:

```text
docs/integration/company-profile-explicit-api-local-smoke/company-profile-explicit-api-local-smoke.json
docs/integration/company-profile-explicit-api-local-smoke/company-profile-explicit-api-local-smoke.md
```

Expected result:

- `decision=go`
- HTTP 200
- document count is greater than zero
- citations are present
- boundary fields show no chat invocation, model invocation, tool execution, memory write, audit write, trace write, GraphRAG execution, or runtime behavior change

## Provider Feedback Payload

Refresh the provider feedback-compatible trial outcome:

```powershell
python scripts/export_unified_knowledge_provider_trial_outcome.py `
  --provider-base-url http://127.0.0.1:8020 `
  --agent-id company_profile
```

Expected artifacts:

```text
docs/integration/unified-knowledge-provider-trial/unified-knowledge-provider-trial-outcome.json
docs/integration/unified-knowledge-provider-trial/unified-knowledge-provider-trial-outcome.md
```

The JSON artifact should include `provider_feedback_input`. This payload is the bridge back to `unifiedKnowledgeRAG` provider-side feedback classification if a future real caller issue appears.

## Boundary

This closure does not do any of the following:

- Enable default `/api/chat` retrieval injection.
- Create source-to-agent bindings.
- Mutate provider data.
- Execute GraphRAG.
- Promote retrieval backends or provider runtime defaults.
- Change final answer policy, approvals, audit, permissions, memory, or governance semantics.

## Success Criteria

The caller loop is closed when:

- The provider health/preflight/source-binding endpoints are reachable.
- MyPrivateAgent has documented local provider environment settings.
- Explicit company-profile caller smoke returns `go`.
- Unified knowledge provider trial outcome exports `provider_feedback_input`.
- Focused backend tests and OpenSpec validation pass.
- Active OpenSpec changes are clean after archive.
