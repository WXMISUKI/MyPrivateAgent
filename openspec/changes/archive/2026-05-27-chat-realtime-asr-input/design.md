# Design: Chat Realtime ASR Input

## Backend
Add `WS /api/capabilities/voice.asr.vosk/stream` in the capability router. The route accepts browser PCM chunks and proxies them to the configured external provider stream path from the capability metadata.

The backend proxy:
- accepts the browser WebSocket only after resolving `voice.asr.vosk`;
- requires an HTTP capability provider with `provider_base_url` and `provider_stream_path` metadata;
- converts `http://` to `ws://` and `https://` to `wss://`;
- forwards binary chunks and text control frames such as `__end__`;
- forwards provider JSON messages back to the browser;
- returns structured error messages over WebSocket before closing when provider metadata is missing or unreachable.

## Frontend
The chat microphone button should prefer managed realtime ASR when browser APIs are available:

1. Check `capabilityApi.health('voice.asr.vosk')`.
2. If ready, open `WS /api/capabilities/voice.asr.vosk/stream` against the current MyPrivateAgent origin.
3. Start `navigator.mediaDevices.getUserMedia` with one channel and common speech enhancement constraints.
4. Use `AudioContext` and a script processor to downsample microphone float samples to 16kHz and encode PCM s16le chunks.
5. Merge partial/final ASR messages into the existing textarea using the current `speechBaseText`, `speechFinalTranscript`, and `speechInterimTranscript` state.
6. On stop/unmount/send, send `__end__`, stop tracks, disconnect nodes, close context and WebSocket.
7. If managed ASR cannot start, fallback to existing browser `SpeechRecognition` when available.

## Error Handling
- Provider not ready: show a concise input hint and fallback if possible.
- Permission denied: show the existing microphone permission hint.
- WebSocket/provider errors: stop capture, show a concise ASR unavailable hint, leave existing typed text intact.

## Testing
- Backend tests should verify the stream URL resolver maps external provider metadata to WebSocket URLs and rejects non-external/local capabilities with a structured error helper.
- Frontend tests should verify the microphone button uses managed realtime ASR when available, updates textarea from partial/final WebSocket messages, and falls back to browser speech recognition when ASR health is not ready.
