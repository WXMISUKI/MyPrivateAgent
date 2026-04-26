# Agent Framework Card Schemas

## Purpose

This document defines the structured card contract shared by:

- backend tool/runtime events
- frontend event normalization
- frontend structured card registry

The goal is to avoid page-level special cases and make deterministic results render through a stable schema.

---

## Core Rules

1. Every structured card must include:
   - `kind`
   - `schema`
2. `schema` is the primary dispatch key on the frontend.
3. `kind` is descriptive, but renderer lookup should prefer `schema`.
4. A tool may support multiple schemas; do not assume one tool maps to exactly one card schema.
4. Backend events should include:
   - `render_mode = structured_card`
   - `card`
   - `card_schema`
5. `card_schema` should match `card.schema`.

---

## Event Shape

Example event payload:

```json
{
  "type": "content",
  "render_mode": "structured_card",
  "card_schema": "weather.v1",
  "card": {
    "kind": "weather",
    "schema": "weather.v1"
  }
}
```

---

## Implemented Schemas

### `weather.v1`

Used for weather query results.

Example shape:

```json
{
  "kind": "weather",
  "schema": "weather.v1",
  "city": "舟山",
  "current": {
    "weather": "小雨",
    "temperature": "15.7°C",
    "wind_speed": "22.6 km/h",
    "wind_direction": "西北"
  },
  "forecast": [
    {
      "date": "2026/04/22",
      "weather": "中雨",
      "min_temp": "14.9°C",
      "max_temp": "18.6°C",
      "precipitation": "38.9mm"
    }
  ]
}
```

### `datetime.v1`

Used for current date/time tool results.

Example shape:

```json
{
  "kind": "datetime",
  "schema": "datetime.v1",
  "date": "2026/04/22",
  "time": "21:06:32",
  "weekday": "星期三"
}
```

### `search_summary.v1`

Used for generic search / retrieval summaries.

Example shape:

```json
{
  "kind": "search_summary",
  "schema": "search_summary.v1",
  "query": "OpenAI",
  "status": "success",
  "summary": "一家人工智能公司。",
  "source": "knowledge_base",
  "source_label": "知识库",
  "source_count": 1
}
```

Recommended semantics:

- `source`: stable machine-readable source key
- `source_label`: user-facing source label
- `source_count`: how many concrete sources were used or matched

---

## Artifact Alignment

Structured tool results should also be persisted as schema-aware artifacts.

Recommended artifact fields:

- `kind`
- `content`
- `render_mode`
- `card_schema`
- `card`
- `metadata.tool_name`

This lets replay, audit, and future artifact UIs reuse the same schema contract as SSE events.

---

## Extension Workflow

When adding a new schema:

1. Add backend schema builder / parser
2. Add `card_schema` or `supported_card_schemas` to the relevant tool metadata if appropriate
3. Emit `card` and `card_schema` from runtime events
4. Register the schema in `frontend-vue/src/components/cards/registry.js`
5. Add the renderer component
6. Add at least one backend test

---

## Versioning

Use versioned schema names:

- `weather.v1`
- `datetime.v1`

If the card shape changes incompatibly, create a new schema version rather than silently mutating the existing one.
