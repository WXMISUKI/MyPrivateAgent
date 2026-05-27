# Design

## Frontend Interaction

Chat input keeps the existing `textarea + send` layout and adds a compact microphone button before the send button.

States:

- `unsupported`: Web Speech API not available, button disabled, hint shows browser unsupported.
- `idle`: button available, click starts recognition.
- `listening`: button active, click stops recognition, hint shows listening.
- `error`: recognition error is shown as a low-noise hint.

## Recognition Behavior

At start, capture the current `inputMessage` as `speechBaseText`. Recognition final transcripts are appended after that base text. Interim transcripts are appended after final transcripts and may be replaced by later interim results.

The implementation creates a new recognition instance per session and wires:

- `onresult`: merge final and interim transcripts into textarea.
- `onerror`: stop listening and show compact error hint.
- `onend`: stop listening and clear transient interim state.

Sending a message stops active recognition before clearing the input.

## Provider Boundary

Xiaomi MiMo TTS config is only reserved:

- `MIMO_API_KEY=`
- `MIMO_BASE_URL=https://api.xiaomimimo.com/v1`
- `MIMO_TTS_MODEL=mimo-v2.5-tts`
- `MIMO_TTS_VOICE=Chloe`

No backend service consumes these values in this change.
