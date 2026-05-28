## Context

The capability runtime already supports external HTTP voice capabilities via `voice_http_provider.py`, and the main chat microphone flow uses `/api/capabilities/voice.asr.vosk/stream`. The older `backend/voice_runtime/` package remains useful as a disabled-by-default local fallback and for backward compatibility with `/api/voice/*`.

The problem is not that the directory exists. The problem is that its docs and some runtime strings still read like the primary implementation path.

## Decisions

1. **External provider first.**
   - `unifiedTTSandASR` is the recommended deployment and development path.
   - Main project voice consumers should prefer `/api/capabilities/*`.

2. **Legacy local fallback stays explicit.**
   - `backend/voice_runtime/` remains disabled by default.
   - It must not require optional dependencies during startup.
   - It must clearly identify itself as legacy/local compatibility.

3. **Compatibility APIs stay stable.**
   - `/api/voice/capabilities`, `/api/voice/tts`, `/api/voice/asr`, and `/api/voice/asr/ws` remain available for old callers.
   - New frontend and provider diagnostics should continue using `capabilityApi`.

4. **No dependency migration into core.**
   - No `edge-tts`, Vosk model, or realtime ASR dependency becomes mandatory in the main backend.

## Risks / Trade-offs

- [Risk] Keeping legacy local code can still confuse readers. -> Mitigation: rename docs/metadata text and add explicit legacy warnings.
- [Risk] Deleting compatibility endpoints would be cleaner but disruptive. -> Mitigation: keep endpoints now and define removal as a future breaking change.
- [Risk] External provider outage could make voice unavailable. -> Mitigation: capability heartbeat already reports provider-level `unreachable` without blocking main server startup.
