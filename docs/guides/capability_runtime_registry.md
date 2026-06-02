# 统一能力运行时注册中心

## 定位
`capability_runtime` 是 MyPrivateAgent 面向 OCR、ASR、TTS、RAG、知识图谱、多模态、视频生成等 AI 能力的统一注册和调用层。它不替代具体模型或工具服务，而是把不同运行环境的能力收口到统一合同里，供前端、垂域智能体、ToolRuntime、MCP、治理台共同使用。

## 当前实现
当前能力注册中心已注册语音能力，并可按配置接入外部知识能力：

```text
voice.tts.edge
voice.asr.vosk
knowledge.rag.retrieve
knowledge.graph.query
```

语音能力的推荐路径是外部 `unifiedTTSandASR` HTTP/WebSocket provider。`backend/voice_runtime/` 仅作为 disabled-by-default 的 legacy local fallback 和旧 `/api/voice/*` 兼容层保留。知识能力只通过外部 `unifiedKnowledgeProvider` 接入，主项目不内置向量库、图数据库、Embedding、OCR、文档解析或重排依赖。

## 目录
```text
backend/capability_runtime/
  contracts.py
  registry.py
  service.py
  providers/
    voice_provider.py
    voice_http_provider.py
    knowledge_http_provider.py
backend/routers/capabilities.py
```

## 统一接口
### `GET /api/capabilities`
列出全部能力：

```json
{
  "contract_version": "capability-runtime-v1",
  "capabilities": [
    {
      "capability_id": "voice.tts.edge",
      "kind": "tts",
      "transport": "local",
      "provider": "edge_tts",
      "status": "disabled",
      "input_schema": {},
      "output_schema": {}
    }
  ]
}
```

### `GET /api/capabilities/{capability_id}`
读取单个能力合同。

### `GET /api/capabilities/{capability_id}/health`
读取能力健康状态。状态值应尽量复用：

- `ready`
- `disabled`
- `missing_dependency`
- `unconfigured`
- `unsupported`
- `error`

### `POST /api/capabilities/{capability_id}/invoke`
短任务同步调用。当前用于 TTS、短音频 ASR、RAG 检索和图谱查询这类小输入。大文件 OCR、视频生成、批处理、文档导入和增量索引应走外部 provider 自己的 jobs/artifacts，不进入 MyPrivateAgent 主后端。

不可用时返回统一错误：

```json
{
  "ok": false,
  "capability_id": "voice.tts.edge",
  "provider": "edge_tts",
  "error": {
    "code": "VOICE_RUNTIME_DISABLED",
    "message": "Legacy local voice runtime is disabled. Prefer the external unifiedTTSandASR provider with ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true; set ENABLE_VOICE_RUNTIME=true only for local fallback compatibility.",
    "provider": "edge_tts"
  }
}
```

### `POST /api/capabilities/{capability_id}/test`
由 MyPrivateAgent 控制面发起的主动能力测试。它用于设置页和运维验收，不替代业务调用链。

请求：

```json
{
  "payload": {},
  "mode": "default"
}
```

TTS 默认测试会补入一段短文本，调用 provider 的 invoke 接口，并只把音频摘要返回给控制面：

```json
{
  "ok": true,
  "capability_id": "voice.tts.edge",
  "status": "ok",
  "latency_ms": 123,
  "result_summary": {
    "media_type": "audio/mpeg",
    "audio_base64_length": 1024
  }
}
```

ASR 在未传入 `audio_base64` 时只做 readiness 检查，避免把“服务在线”误判成“真实识别成功”：

```json
{
  "ok": true,
  "capability_id": "voice.asr.vosk",
  "status": "ready",
  "mode": "health_only"
}
```

ASR 在传入 `audio_base64` 时只接受 `16kHz / mono / PCM s16le` 原始音频。`audio/mpeg`、`audio/wav`、`audio/webm` 等压缩或容器格式必须先由调用方或专门音频服务转码，否则控制面会返回：

```json
{
  "ok": false,
  "status": "invalid_input",
  "error": {
    "code": "CAPABILITY_TEST_UNSUPPORTED_MEDIA_TYPE"
  }
}
```

### `GET /api/capabilities/heartbeat`
实时探测外部能力服务。该接口用于治理台、前端或运维面板展示“当前有哪些能力可调用、对应服务是否在线”。

返回内容包含 provider 级别状态和每个 capability 的健康状态：

```json
{
  "contract_version": "capability-runtime-v1",
  "providers": [
    {
      "provider_id": "unifiedTTSandASR",
      "base_url": "http://127.0.0.1:8010",
      "transport": "http",
      "status": "ok",
      "capabilities": [
        {
          "capability_id": "voice.tts.edge",
          "status": "ready"
        }
      ]
    }
  ]
}
```

### `WS /api/capabilities/{capability_id}/stream`
实时流式能力代理。当前用于 `voice.asr.vosk` 主对话麦克风输入。

前端只连接 MyPrivateAgent：

```text
WS /api/capabilities/voice.asr.vosk/stream
```

MyPrivateAgent 根据 capability metadata 中的 `provider_base_url` 和 `provider_stream_path` 转发到外部 provider，例如：

```text
ws://127.0.0.1:8010/api/voice/asr/ws
```

客户端发送内容：

- 二进制帧：`16kHz / mono / PCM s16le` 音频 chunk。
- 文本帧：`__end__` 表示结束当前识别。

服务端返回 provider 的识别消息：

```json
{
  "ok": true,
  "provider": "vosk_server",
  "language": "zh-cn",
  "text": "实时识别文本",
  "partial": true
}
```

主聊天输入框会把 `partial=true` 作为临时文本，把 `partial=false` 的 `text` 合并进最终输入内容。用户发送消息时仍然走原有 `/api/chat` 流程。

## 对接 unifiedTTSandASR
`.env` 中启用外部语音能力服务：

```env
ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true
VOICE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8010
VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=5
```

启用后，`voice.tts.edge` 和 `voice.asr.vosk` 会以 `transport=http` 注册，并通过 `unifiedTTSandASR` 的 `/api/capabilities/*` 实时查询状态和执行调用。正常开发和生产部署应优先走这个路径。

## 对接 unifiedKnowledgeProvider

`.env` 中启用外部知识能力服务：

```env
ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER=true
KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8020
KNOWLEDGE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=5
```

启用后，`knowledge.rag.retrieve` 和 `knowledge.graph.query` 会以 `transport=http` 注册。MyPrivateAgent 通过 provider 的 `/health` 读取健康状态，通过 `/api/rag/retrieve` 和 `/api/graph/query` 执行调用。具体外部项目开发规范见 [external_rag_provider_development.md](./external_rag_provider_development.md)。

## 对接 PaddleOCR OCR/Layout

`.env` 中启用基础 OCR 与 layout 解析服务：

```env
ENABLE_OCR_CAPABILITY_PROVIDER=true
OCR_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8080
OCR_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=30
ENABLE_LAYOUT_CAPABILITY_PROVIDER=true
LAYOUT_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8081
LAYOUT_CAPABILITY_PROVIDER_INVOKE_PATH=/layout-parsing
LAYOUT_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=60
```

启用后，MyPrivateAgent 会注册：

- `document.ocr.extract`（kind=`ocr`，transport=`http`） -> 默认调用 `/ocr`
- `document.layout.parse`（kind=`layout`，transport=`http`） -> 默认调用 `/layout-parsing`

两者均通过 `heartbeat` 展示运行状态；`document.layout.parse` 的返回会被规范化为 `markdown/elements/tables/pages/artifacts/warnings/raw`。

## 对接 document.vlm

VLM 能力通过外部文档模型服务接入，建议将同步与异步能力分路管理：

- 同步：`document.vlm.parse`
- 异步：`document.vlm.parse.async`

`ENABLE_VLM_CAPABILITY_PROVIDER=true` 后，服务端读取以下配置：

```env
VLM_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8082
VLM_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=120
VLM_CAPABILITY_PROVIDER_INVOKE_PATH=/layout-parsing
VLM_CAPABILITY_PROVIDER_ASYNC_SUBMIT_PATH=/api/vlm/jobs
VLM_CAPABILITY_PROVIDER_ASYNC_STATUS_PATH_TEMPLATE=/api/vlm/jobs/{job_id}
```

异步能力建议采用如下契约：

- `operation=submit`：提交任务，返回 `job_id/status/progress`
- `operation=status`：查询任务，必须带 `job_id`
- status 支持并对齐为 `queued/running/succeeded/failed/expired`

## 前端调用
```js
import { capabilityApi } from '@/api'

const list = await capabilityApi.list()
const tts = await capabilityApi.get('voice.tts.edge')
const health = await capabilityApi.health('voice.tts.edge')
const result = await capabilityApi.invoke('voice.tts.edge', { text: '您好' })
const test = await capabilityApi.test('voice.tts.edge')
```

设置页“模型与 Provider”区域提供“能力 Provider 测试”面板，统一展示 `/api/capabilities`、`/api/capabilities/heartbeat` 和主动测试结果。TTS 测试成功后可直接播放返回音频；ASR 默认展示 health-only 结果，如需真实识别可上传已经符合 provider 要求的音频载荷。实时录音、PCM 下采样和 WebSocket 验收仍由 `unifiedTTSandASR/static/index.html` 作为服务自身调试台承担。

## Legacy local voice fallback

`backend/voice_runtime/` 和 `/api/voice/*` 当前只作为兼容层保留：

- 旧调用方仍可访问 `/api/voice/capabilities`、`/api/voice/tts`、`/api/voice/asr`、`/api/voice/asr/ws`。
- 主聊天麦克风和能力诊断应优先使用 `/api/capabilities/voice.asr.vosk/*`、`/api/capabilities/voice.tts.edge/*`。
- 主后端不应为了语音能力默认安装 `edge-tts`、Vosk 模型或本地实时识别依赖。
- 若后续要删除 `/api/voice/*` 或 `backend/voice_runtime/`，必须另开 breaking-change OpenSpec。

## 后续服务化规则
新增 OCR、多模态、视频生成时优先按以下顺序：

1. 先定义 `capability_id`、`kind`、`input_schema`、`output_schema`。
2. 再选择 transport：
   - `local`: 轻依赖、主环境可承载。
   - `http`: 独立服务，适合 OCR、视频生成、多模态模型。
   - `mcp`: 工具/资源/提示词能力适合被 Agent 动态发现。
   - `websocket`: 实时 ASR、流式推理。
3. 能力服务自己管理 Python、CUDA、FFmpeg、模型文件和容器。
4. 主项目只保留注册、调用、权限、审计、任务状态和 artifact 合同。

## 当前非目标
- 不把 OCR/视频生成服务直接塞进主后端。
- 不在本切片实现长任务队列和 artifact 存储。
- 不删除已有 `/api/voice/*` 兼容接口。
