## Overview

This slice promotes already-computed `parent_state_surface` evidence into overview contracts. The dedicated merged semantics read model remains the richer source, while runtime core and governance overview expose the stable parent-facing subset.

## Contract Additions

Add to runtime core and `governance_overview.run`:

- `child_merge_section_source`
- `child_merge_section_ids`
- `child_merge_section_counts`

Also formalize existing overview fields in the response schema:

- `child_merge_entity_count`
- `child_merge_focus_count`
- `child_merge_action_count`
- `child_merge_primary_entities`

## Data Flow

`_resolve_runtime_scope(...)` already reads `parent_state_surface` from `summarize_child_executor_merged_semantics(...)`. It should additionally copy:

- `section_source` -> `child_merge_section_source`
- `section_ids` -> `child_merge_section_ids`
- `section_counts` -> `child_merge_section_counts`

`_build_child_merge_state_contract(...)` should pass those fields through to runtime core and governance overview.

## Compatibility

Existing consumers keep using:

- `child_merge_intent`
- `child_merge_entities`
- `child_merge_conclusion`

The new fields are additive and empty by default when no merged semantics are available.

## Testing Strategy

- Runtime profile test verifies both `runtime_core` and `governance_overview.run` expose section source/count evidence.
- Schema test verifies `RuntimeSurfaceRunOverview` accepts existing count fields and new section evidence.
- OpenSpec validation verifies canonical spec sync.

