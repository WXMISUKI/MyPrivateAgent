## Design Summary

Add a standalone FastAPI wrapper provider that implements the Stage 3B async VLM API while delegating heavy parsing to an upstream sync HTTP provider.

Default local topology:

- OCR provider: `http://127.0.0.1:8080`
- Layout provider: `http://127.0.0.1:8081`
- VLM async wrapper provider: `http://127.0.0.1:8082`
- MyPrivateAgent: `http://127.0.0.1:8000`

## Runtime Shape

The wrapper provider owns only local development job orchestration:

- store jobs in process memory
- start background worker per submitted job
- mark lifecycle as `queued -> running -> succeeded|failed`
- return stable status payloads to MyPrivateAgent polling

The upstream sync provider owns actual document parsing. The default upstream is PP-StructureV3:

```text
POST http://127.0.0.1:8081/layout-parsing
```

## Request Mapping

Input from MyPrivateAgent async adapter:

```json
{
  "file": "<base64>",
  "fileType": 0,
  "task": "summarize",
  "question": "",
  "maxPages": 3
}
```

Forwarded upstream payload:

```json
{
  "file": "<base64>",
  "fileType": 0,
  "outputFormat": "markdown",
  "includeTables": true,
  "includeLayout": true,
  "maxPages": 3
}
```

## Job Output

The wrapper returns:

```json
{
  "result": {
    "job_id": "vlm-job-...",
    "status": "succeeded",
    "progress": 1.0,
    "result": {
      "summary": "...",
      "sections": [],
      "entities": [],
      "answers": [],
      "evidence": [],
      "raw": {}
    },
    "error": {},
    "warnings": [],
    "raw": {}
  }
}
```

## Boundaries

- This is not a production queue.
- Jobs are lost on process restart.
- Artifact storage is excluded.
- Real PaddleOCR-VL runtime integration can replace the upstream sync call later without changing MyPrivateAgent.
