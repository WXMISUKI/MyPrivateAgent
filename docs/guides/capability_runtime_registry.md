# 统一能力运行时注册中心

## 定位
`capability_runtime` 是 MyPrivateAgent 面向 OCR、ASR、TTS、RAG、知识图谱、多模态、视频生成等 AI 能力的统一注册和调用层。它不替代具体模型或工具服务，而是把不同运行环境的能力收口到统一合同里，供前端、垂域智能体、ToolRuntime、MCP、治理台共同使用。

外接能力服务的管理面由 `provider-service-consumption-v1` 承接。它位于 `capability_runtime` 之上，只负责 provider 注册视图、readiness 归一化、显式 invoke 包装和 compact evidence preview；真实执行仍委托给 `/api/capabilities/{capability_id}/invoke`，不会新建第二套 provider 调用链。

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
  provider_consumption_service.py
  registry.py
  service.py
  providers/
    voice_provider.py
    voice_http_provider.py
    knowledge_http_provider.py
backend/routers/capabilities.py
backend/routers/service_providers.py
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

### `GET /api/service-providers`
读取外接服务 provider 管理列表。该接口面向治理台、设置页和集成调试，返回 provider 级别 readiness，而不是模型 provider 配置。

```json
{
  "contract_version": "provider-service-consumption-v1",
  "providers": [
    {
      "provider_id": "unifiedKnowledgeProvider",
      "kind": "knowledge",
      "transport": "http",
      "base_url": "http://127.0.0.1:8020",
      "configured": true,
      "enabled": true,
      "overall_status": "ready",
      "capabilities": [
        {
          "capability_id": "knowledge.rag.retrieve",
          "kind": "rag",
          "transport": "http",
          "status": "ready",
          "invocation_boundary": "explicit_only"
        }
      ],
      "gates": [],
      "warnings": [],
      "boundaries": {
        "default_chat_grounding": "disabled",
        "source_binding_automation": "disabled",
        "graphrag_execution": "not_promoted",
        "final_answer_policy": "not_changed"
      }
    }
  ]
}
```

已知 provider 会携带 `onboarding_id` 与 `onboarding_path`，用于跳转到静态接入说明。例如 `unifiedKnowledgeProvider` 会引用 `/api/provider-onboarding/knowledge-rag-provider`。

状态词表统一收敛为：

- `ready`
- `review`
- `blocked`
- `unreachable`
- `gated`
- `disabled`
- `unconfigured`
- `unknown`

### `GET /api/service-providers/{provider_id}`
读取单个 provider 的 compact readiness 与 capability health 摘要。它可以包含 `governance_readiness`、catalog summary、gates 和 warnings，但不得包含 API key、检索正文、完整 provider raw payload 或生成答案。

### `GET /api/service-providers/{provider_id}/evidence-preview`
生成 caller-owned provider evidence preview，用于接入审查和治理诊断。该 preview 包含 provider identity、readiness、capability statuses、gates、warnings、boundaries、recommended action 和 provider reopen gate，不创建 audit/memory/source binding。

### `POST /api/service-providers/{provider_id}/capabilities/{capability_id}/invoke`
显式调用 provider 拥有的 capability。该接口先校验 provider 是否拥有 `capability_id`，再委托给现有 capability runtime；若 capability 不属于该 provider，则 fail-closed：

```json
{
  "ok": false,
  "provider_id": "unifiedKnowledgeProvider",
  "capability_id": "voice.tts.edge",
  "error": {
    "code": "SERVICE_PROVIDER_CAPABILITY_NOT_OWNED"
  }
}
```

成功调用仍保持显式边界：不启用默认 `/api/chat` grounding，不创建 source-to-agent binding，不写 memory/audit，不改变最终答案策略。

### `GET /api/provider-onboarding`
读取已知外接项目的接入目录。这个接口是静态/配置导向的 onboarding catalog，不做 live probe，也不启动服务。它用于回答“这个外接项目怎么接入 MyPrivateAgent”：

```json
{
  "contract_version": "provider-onboarding-catalog-v1",
  "entries": [
    {
      "onboarding_id": "knowledge-rag-provider",
      "provider_id": "unifiedKnowledgeProvider",
      "kind": "knowledge",
      "default_base_url": "http://127.0.0.1:8020",
      "capability_ids": ["knowledge.rag.retrieve", "knowledge.graph.query"],
      "env": {
        "enable_var": "ENABLE_KNOWLEDGE_CAPABILITY_PROVIDER",
        "base_url_var": "KNOWLEDGE_CAPABILITY_PROVIDER_BASE_URL"
      }
    }
  ]
}
```

当前 catalog 第一批固定：

- `knowledge-rag-provider` -> `unifiedKnowledgeProvider`
- `voice-asr-tts-provider` -> `unifiedTTSandASR`
- `document-ocr-provider` -> `paddleOCRProvider`
- `document-layout-provider` -> `paddleLayoutProvider`
- `document-vlm-provider` -> `documentVlmProvider`

### `GET /api/provider-onboarding/{onboarding_id}`
读取单个 provider 接入详情，包括 env var 名称、默认本地 URL、capability ids、文档链接、smoke command、management links 和边界。该接口只返回 env var 名称，不返回 secret 值。

### `GET /api/provider-onboarding/{onboarding_id}/readiness`
读取当前进程配置下的 onboarding checklist。该 checklist 只判断 enable flag/base URL/timeout 等配置项是否存在，并提示后续用 `/api/service-providers/{provider_id}` 或 `/api/capabilities/heartbeat` 做 live probe；它不访问外部 provider。

### Provider onboarding acceptance gate
`backend/scripts/provider_onboarding_acceptance_smoke.py` 可生成外接 provider 接入验收 evidence：

```powershell
python backend\scripts\provider_onboarding_acceptance_smoke.py --onboarding-id knowledge-rag-provider --pretty
python backend\scripts\provider_onboarding_acceptance_smoke.py --provider-id unifiedKnowledgeProvider --pretty
```

该 gate 读取 onboarding detail、onboarding readiness 和 service-provider 管理列表，输出 `provider-onboarding-acceptance-gate-v1` JSON。`decision = accepted` 只表示 provider 可进入显式 managed-provider consumption；`blocked` 会列出配置缺失、未注册、live status 不可用或 capability ownership 不匹配等 blockers。

验收 gate 仍是只读：不调用 capability invoke/test，不执行 RAG/OCR/VLM/ASR/TTS/GraphRAG，不写 `.env`，不启动 provider，不创建 source binding，不改变默认 `/api/chat` grounding 或 final answer policy。

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

能力 health / heartbeat 会在 `provider_health.governance_readiness` 下暴露只读治理 readiness：

- `rag_retrieve.status=ready` 只表示可用于显式 RAG 调用。
- `graph_query.status=gated` 表示 GraphRAG 执行仍需单独 promotion gate。
- `default_chat_grounding.status=gated` 表示默认 `/api/chat` 检索注入仍关闭。
- `source_catalog` 只用于展示 source catalog 数量和 degraded source，不创建 source-to-agent binding。
- readiness payload 不包含 API key、检索正文、完整 provider raw payload 或生成答案。

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

设置页“模型与 Provider”区域提供“外接 Provider 接入”只读面板，消费 `/api/provider-onboarding`、`/api/provider-onboarding/{onboarding_id}/readiness` 与 `/api/service-providers`，用于查看已知外接项目的 env var、默认 URL、capability ids、配置 checklist、live provider status、management/evidence preview path 和 runtime boundaries。该面板只刷新 read model，不写 `.env`，不启动 provider，不调用 capability invoke/test，不改变默认 chat grounding、GraphRAG、source binding 或 final answer policy。

同一区域还提供“能力 Provider 测试”面板，统一展示 `/api/capabilities`、`/api/capabilities/heartbeat` 和主动测试结果。TTS 测试成功后可直接播放返回音频；ASR 默认展示 health-only 结果，如需真实识别可上传已经符合 provider 要求的音频载荷。实时录音、PCM 下采样和 WebSocket 验收仍由 `unifiedTTSandASR/static/index.html` 作为服务自身调试台承担。

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
