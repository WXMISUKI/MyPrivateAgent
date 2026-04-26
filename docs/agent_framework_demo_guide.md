# Agent Framework Demo Guide

## Goal
This repository now contains two layers:

- `backend/agent_framework`: reusable runtime primitives
- `backend/agent_server`: reusable FastAPI server assembly

The current app is still `MyPrivateAgent`, but the codebase can already be reused as a demo framework for new domain agents.

## Recommended Reuse Boundary

Reuse these parts directly:

- Runtime state, events, tool metadata, artifacts, cache
- Server app factory, auth provider, router registry, HTTP/SSE helpers
- Structured card protocol and frontend card registry

Keep domain-specific code isolated:

- Weather service
- Domain prompts
- Domain tools
- Domain card schemas

## Frontend Boundary

`frontend-vue` is now the primary client surface for the reusable demo framework.

- Default `full_stack` mode serves the built Vue SPA from `frontend-vue/dist`
- The legacy template frontend has been removed from the default demo
- New domain demos should target `frontend-vue` only

## Current Server Presets

- `full_stack`: current product shape with primary Vue SPA
- `api_only`: API-focused deployment without legacy UI
- `embedded`: lightweight embedding mode
- `learning_demo`: chat + learnings + permissions demo, suited for runtime knowledge experiments
- `weather_demo`: weather/realtime lookup oriented starter preset
- `knowledge_demo`: knowledge and learnings oriented starter preset

Example:

```python
from backend.agent_server import create_app

app = create_app(preset="learning_demo")
```

For starter-oriented examples, see:

- [agent_framework_starter_guide.md](D:/AI/AIcode/MyPrivateAgent/docs/agent_framework_starter_guide.md)
- [weather_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/weather_demo_app.py)
- [knowledge_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/knowledge_demo_app.py)

## Runtime Knowledge Governance

Runtime knowledge is now injected through `RuntimeLearningService`.

Supported governance levels:

- `enforced`: injected as strict runtime rules
- `advisory`: injected as suggestions
- `diagnostic`: recorded in metadata only, not injected into the model

Current classification rules are intentionally simple:

- `SystemPrompt.tags` containing `enforced` => enforced
- `SystemPrompt.tags` containing `diagnostic` => diagnostic
- `prompt_type in {"tool_usage", "workflow"}` or `priority >= 5` => enforced
- High-priority `BestPractice` => enforced
- `diagnostic` tagged practices => diagnostic

## How To Build a New Domain Agent

1. Add domain tools and `ToolSpec`
2. Add domain card schema if deterministic output needs structured rendering
3. Add domain prompts / best practices through learnings APIs or seed data
4. Choose a preset:
   - `api_only` for backend integration
   - `learning_demo` for iterative runtime tuning
5. Add a small domain-specific service layer instead of editing runtime core

## Recommended Next Steps

- Keep `frontend-vue` as the single primary client
- Add starter templates for new domain agents
- Add end-to-end tests for `tool_result -> done -> structured_card`
- Add runtime knowledge rollback and scope controls
