## ADDED Requirements

### Requirement: Trial surface can consume live provider evidence
The existing grounded-answer trial surface SHALL accept evidence produced by the live domain-agent provider retrieve trial without changing its side-effect-free behavior.

#### Scenario: Live trial feeds evidence pack into trial surface
- **WHEN** the live trial obtains a provider `evidence_pack`
- **THEN** the grounded-answer trial surface consumes that evidence pack as caller-provided evidence
- **AND** the trial surface still does not call providers, chat, models, tools, memory writes, audit writes, or source binding.
