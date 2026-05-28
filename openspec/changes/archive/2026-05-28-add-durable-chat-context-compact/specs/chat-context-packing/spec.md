## MODIFIED Requirements

### Requirement: Older turns MUST compact into deterministic summary
The system SHALL compact older conversation turns into a deterministic system summary when the history exceeds the recent window or token budget, unless a durable compact summary is available for the same conversation boundary.

#### Scenario: Older messages exceed recent window
- **WHEN** persisted history contains more turns than the configured recent history window and no durable summary applies
- **THEN** older turns are represented by a compact system summary and recent turns remain available as normal chat messages

#### Scenario: Summary does not require model invocation
- **WHEN** context packing summarizes older messages without a durable summary
- **THEN** the summary is generated deterministically without invoking a language model

#### Scenario: Durable summary takes precedence
- **WHEN** a durable compact summary exists for the conversation
- **THEN** context packing uses the durable summary before transient fallback summary generation
