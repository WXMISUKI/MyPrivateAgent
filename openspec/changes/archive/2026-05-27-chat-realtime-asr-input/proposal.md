# Proposal: Chat Realtime ASR Input

## Summary
Move the main chat microphone button from browser-only Web Speech recognition to MyPrivateAgent-managed realtime ASR. The chat UI should stream microphone audio to a backend WebSocket proxy, receive partial/final transcripts, and keep the existing `/api/chat` send path unchanged.

## Why
`unifiedTTSandASR` already provides a tested realtime Vosk WebSocket pipeline. The main chat input is the natural user-facing place for this capability, but the frontend should not hardcode the external provider URL or bypass MyPrivateAgent capability governance.

## Scope
- Add a backend WebSocket proxy for `voice.asr.vosk` realtime streams.
- Prefer the managed realtime ASR path from the chat microphone button.
- Reuse the existing browser audio pipeline pattern from `unifiedTTSandASR/static/index.html`: `getUserMedia` -> `AudioContext` -> downsample to 16k -> PCM s16le -> WebSocket chunks.
- Keep browser `SpeechRecognition` as fallback when managed ASR is unavailable or unsupported.
- Keep final text in the existing textarea and send through the existing chat flow.

## Non-Goals
- Do not add automatic MP3/WAV/WebM transcoding in this slice.
- Do not change `/api/chat` request shape.
- Do not make frontend call the external `8010` provider directly.
- Do not add assistant reply TTS playback in this slice.
