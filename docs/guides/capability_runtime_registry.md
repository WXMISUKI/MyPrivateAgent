# 统一能力运行时注册中心

## 定位
`capability_runtime` 是 MyPrivateAgent 面向 OCR、ASR、TTS、多模态、视频生成等 AI 能力的统一注册和调用层。它不替代具体模型或工具服务，而是把不同运行环境的能力收口到统一合同里，供前端、垂域智能体、ToolRuntime、MCP、治理台共同使用。

## 当前实现
当前最小切片已注册现有语音能力：

```text
voice.tts.edge
voice.asr.vosk
```

它们仍由 `backend/voice_runtime/` 执行。后续可以平滑迁移为独立 HTTP/MCP 服务，外部调用方不需要改能力接口。

## 目录
```text
backend/capability_runtime/
  contracts.py
  registry.py
  service.py
  providers/
    voice_provider.py
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
短任务同步调用。当前用于 TTS、短音频 ASR 这类小输入。大文件 OCR、视频生成、批处理任务后续应走 jobs/artifacts。

不可用时返回统一错误：

```json
{
  "ok": false,
  "capability_id": "voice.tts.edge",
  "provider": "edge_tts",
  "error": {
    "code": "VOICE_RUNTIME_DISABLED",
    "message": "Voice runtime is disabled. Set ENABLE_VOICE_RUNTIME=true to enable it.",
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

## 对接 unifiedTTSandASR
`.env` 中启用外部语音能力服务：

```env
ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true
VOICE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8010
VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=5
```

启用后，`voice.tts.edge` 和 `voice.asr.vosk` 会以 `transport=http` 注册，并通过 `unifiedTTSandASR` 的 `/api/capabilities/*` 实时查询状态和执行调用。

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
