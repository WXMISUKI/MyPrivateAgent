## ADDED Requirements

### Requirement: Embedded SDK recovery acceptance MUST remain readiness evidence only
The Phase II exit gate MUST treat Embedded SDK recovery acceptance smoke as explicit recovery consumption readiness evidence, not as production recovery authorization.

#### Scenario: Recovery smoke evidence is bounded
- **WHEN** Phase II exit readiness cites Embedded SDK recovery acceptance smoke
- **THEN** it MUST preserve the boundary that worker lease enforcement, background auto recovery, distributed executor, and default chat behavior remain out of scope
- **AND** it MUST identify any production recovery gap as a future Phase III or final-blocker slice rather than silently promoting readiness evidence
