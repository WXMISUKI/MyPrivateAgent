# Design: External Voice Capability HTTP Provider

## Architecture
When configured, MyPrivateAgent registers voice capabilities as HTTP capabilities:

```text
MyPrivateAgent /api/capabilities
        |
        v
CapabilityRuntimeService
        |
        v
HttpCapabilityClient
        |
        v
unifiedTTSandASR /api/capabilities/*
```

The external service remains responsible for Edge-TTS, Vosk, model dependencies, and provider-specific runtime checks.

## Configuration
New environment variables:

```env
ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=false
VOICE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8010
VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=5
```

When `ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true`, the default registry uses HTTP capability definitions for:
- `voice.tts.edge`
- `voice.asr.vosk`

When disabled, the existing local provider bridge remains active.

## Live Status
`GET /api/capabilities` continues to list capabilities, but HTTP capabilities resolve status by querying their remote health endpoint.

`GET /api/capabilities/heartbeat` returns:
- contract version
- provider records
- provider `/health` status
- per-capability health results
- failure reason when the remote service is unreachable

## Invocation
`POST /api/capabilities/{capability_id}/invoke` delegates HTTP capabilities to the remote service's `/api/capabilities/{capability_id}/invoke` endpoint. Successful and failed remote responses keep their provider-neutral shape.

## Failure Behavior
Remote connection or protocol failures become structured errors:
- `CAPABILITY_PROVIDER_UNREACHABLE`
- `CAPABILITY_PROVIDER_PROTOCOL_ERROR`
- `CAPABILITY_NOT_FOUND`

Startup must not fail if the remote service is down.
