# SZZG Agent Encapsulation Route

This workflow is a Coze migration sample for the `szzg` collaboration track.

It acts as an encapsulation route for agent plaza protocol jumps, and the original
Coze export included HTTP routing steps plus LLM-driven response generation.

## Source

- Original platform: Coze
- Original workflow export: `source/coze_export/` (placeholder)
- Original Coze workflow name: `SZZG_Agent_Encapsulation_ROUTE`
- Original Coze description: `智能体广场协议跳转`
- Business name in MyPrivateAgent: `智能体封装路由`

The original Coze export name is preserved only as source evidence. The MyPrivateAgent workflow id is `szzg_agent_encapsulation_route`.

## Runtime Shape

The original Coze workflow structure involved `start`, `end`, `loop`, `llm`, `condition`, `question`, `http` nodes.
The MyPrivateAgent migration target is now callable through the migration capability
entrypoint and uses supported runtime capabilities only:

```text
input (query_url, user_input)
  -> http.request (for route-capability compatibility)
  -> llm.structured_json.generate (for intelligent response)
  -> result envelope (code, msg, data)
```

## Status

Current status is `active`.

This workflow is registered as an asset and acceptance sample, and it is callable through the migration capability entrypoint.
