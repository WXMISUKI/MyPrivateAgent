## 1. Persistence Boundary

- [x] 1.1 Add a durable conversation compact summary ORM model.
- [x] 1.2 Add a service that creates and reads latest compact summaries for owned conversations.

## 2. Command And API

- [x] 2.1 Add an authenticated manual compact API endpoint.
- [x] 2.2 Intercept `/compact` chat messages and return compact confirmation without invoking the orchestrator.

## 3. Context Packing

- [x] 3.1 Update context packing to consume latest durable summary and post-summary recent messages.
- [x] 3.2 Preserve transient summary fallback when no durable summary exists.

## 4. Verification And Docs

- [x] 4.1 Run targeted backend tests or smoke checks for compact service, slash command, and existing chat flow.
- [x] 4.2 Update architecture documentation and complete OpenSpec task status.
