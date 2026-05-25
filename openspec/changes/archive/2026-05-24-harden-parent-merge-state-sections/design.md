## Overview

This slice hardens the existing `child_executor_merged_semantics` read model without changing its current shape. The implementation adds metadata fields to existing sections and parent state, making the contract self-checking for consumers.

## Contract Additions

Each entry in `merged_sections` keeps its current section id and data fields, and adds:

- `section_kind`: `list` for `merged_entities`, `merged_focus`, and `merged_actions`; `text` for `latest_conclusion`
- `item_count`: present for list sections
- `text_length`: present for text sections

`parent_state_surface` adds:

- `section_source`: `merged_sections`
- `section_ids`: stable ordered section ids
- `section_counts`: counts derived from `merged_sections`

The parent state counts must stay coherent:

- `entity_count == section_counts.merged_entities`
- `focus_count == section_counts.merged_focus`
- `action_count == section_counts.merged_actions`
- `latest_conclusion` equals `merged_sections.latest_conclusion.text`

## Compatibility

Existing consumers can continue reading:

- `intent_label`
- `entities`
- `focus_points`
- `action_items`
- `merge_behavior`
- existing `merged_sections.*.section_id`
- existing `parent_state_surface.*_count`

No field removal or rename is allowed in this slice.

## Testing Strategy

- SDK test verifies merged section metadata and parent state coherence.
- Runtime Surface test verifies the same metadata is preserved through the service read model.
- OpenSpec validation proves the updated canonical specs remain valid.

