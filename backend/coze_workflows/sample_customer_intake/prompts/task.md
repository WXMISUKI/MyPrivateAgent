# Task Prompt

Process the customer message according to the workflow input schema.

Return:

- `summary`: one short summary
- `next_action`: `ask_followup`, `create_ticket`, or `route_to_human`
- `extracted_fields`: compact fields useful for downstream routing
