# Frontend Minimal Regression Checklist

## Goal
This checklist is the minimum manual verification baseline for the reusable Vue demo before merge or release.

It focuses on the current highest-risk chat surface:

- empty conversation rendering
- send and stop flow
- tool call rendering
- feedback submission flow

## Preconditions

1. Backend service is running and chat API is reachable.
2. Vue frontend starts normally or production build succeeds.
3. Use a clean browser session when possible to avoid stale local state interference.

## Checklist

### 1. Empty Conversation

- Open the chat homepage.
- Verify the empty-state view is visible when there are no messages.
- Verify the input area is enabled.
- Verify typing `/` opens the command palette.

Expected result:

- No console error.
- Empty-state copy and command hint render correctly.

### 2. Send And Stop

- Send a normal user message.
- Verify the user message appears immediately.
- Verify assistant generation state appears.
- If the model supports streaming/thinking, click stop during generation.

Expected result:

- The request enters loading state without page freeze.
- Stop action interrupts the current generation without breaking the conversation.
- Input area returns to editable state after completion or stop.

### 3. Tool Call Rendering

- Trigger one prompt that causes tool execution, such as weather or search.
- Verify the assistant message shows tool call sections when tool events are returned.
- If a structured card is returned, verify the card renders instead of raw duplicated payload text.

Expected result:

- Tool name, status, args, and result area render without layout break.
- Structured card content is readable on desktop and mobile widths.

### 4. Feedback Submission

- After an assistant reply, click positive feedback once.
- For another assistant reply, open negative feedback.
- Select one or more reasons, optionally enter comment, then submit.

Expected result:

- Feedback buttons show submitted state correctly.
- Negative feedback panel can open, submit, and close normally.
- Submitted feedback summary is visible on the message.
- Duplicate clicks during submission are blocked.

## Merge Gate

Before merge, at minimum confirm:

- `npm run build` passes in `frontend-vue`
- The four checklist scenarios above pass manually

## Recommended Follow-up

- Add component-level tests for `MessageList` and `ChatMessageItem`
- Add one lightweight end-to-end smoke test for send/tool/feedback chain
