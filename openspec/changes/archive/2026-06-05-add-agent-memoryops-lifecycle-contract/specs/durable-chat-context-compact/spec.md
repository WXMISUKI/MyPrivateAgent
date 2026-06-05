## ADDED Requirements

### Requirement: Durable summaries can be represented in MemoryOps
Durable chat compact summaries SHALL be representable as `conversation_summary` entries in the MemoryOps lifecycle registry without changing compact behavior.

#### Scenario: Summary maps to MemoryOps entry
- **WHEN** a latest durable conversation summary is available
- **THEN** MemoryOps can expose its `conversation_id`, `message_count`, `last_message_id`, `trigger`, and `created_at`
- **AND** compact summary persistence and context packing behavior remain unchanged
