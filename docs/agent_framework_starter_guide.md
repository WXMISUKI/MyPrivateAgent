# Agent Framework Starter Guide

## Purpose
Use this guide when creating a new domain agent from the current framework instead of cloning product-specific behavior blindly.

## Recommended Starting Point

Choose the closest preset first:

- `weather_demo`
  - Focus: deterministic tools, realtime lookup, structured cards
  - Route groups: `auth`, `core`, `permissions`
- `knowledge_demo`
  - Focus: runtime knowledge injection, learnings, governance
  - Route groups: `auth`, `core`, `learning`, `permissions`
- `learning_demo`
  - Focus: runtime knowledge experiments without full product shell
- `api_only`
  - Focus: backend integration without UI

## Example Entrypoints

- [weather_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/weather_demo_app.py)
- [knowledge_demo_app.py](D:/AI/AIcode/MyPrivateAgent/examples/knowledge_demo_app.py)

Run example:

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python -m uvicorn examples.weather_demo_app:app --port 8010
```

For the knowledge-oriented starter:

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python -m uvicorn examples.knowledge_demo_app:app --port 8011
```

## Build a New Domain Agent

1. Pick a preset close to your target shape.
2. Add domain tools and `ToolSpec`.
3. Add domain card schema only for deterministic output worth rendering structurally.
4. Add domain prompts / best practices through learnings APIs or seed data.
5. Keep domain logic in dedicated services instead of editing runtime core.
6. For evaluable agent behavior, wire user feedback back into runtime effect review instead of only recording chat logs.

## Minimal Domain Checklist

- Tool layer:
  - define tool
  - define `ToolSpec`
  - define permission level
  - define cache policy if deterministic
- Output layer:
  - decide `plain_text` vs `structured_card`
  - add card schema only when reusable
- Knowledge layer:
  - decide which prompts are `enforced`
  - decide scope tags such as `scope:chat`
  - mark rollback entries explicitly
- Feedback layer:
  - expose a feedback API for assistant messages
  - ensure streaming done event includes persisted assistant `message_id`
  - enforce message-level feedback idempotency (same user + same message -> update, not duplicate insert)
  - link feedback to `runtime_knowledge_effect`
  - convert repeated negative feedback into reviewable learnings
  - provide feedback analytics endpoint (scope / prompt_key / practice_id) for governance
- Demo layer:
  - add one example app entrypoint
  - document expected routes and required services

## Feedback Data Maintenance

Use dry-run first:

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python backend/scripts/dedupe_message_feedback.py --preview-limit 20
```

Apply cleanup in batches:

```powershell
cd D:\AI\AIcode\MyPrivateAgent
python backend/scripts/dedupe_message_feedback.py --apply --limit-groups 50
```

## Current Reuse Rule

Treat these as framework code:

- `backend/agent_framework`
- `backend/agent_server`
- shared runtime services

Treat these as domain/application code:

- weather service
- domain prompts
- domain practices
- product-specific pages and copy
