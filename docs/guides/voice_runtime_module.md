# Legacy local voice runtime fallback

## 定位

`backend/voice_runtime/` 已不再是语音能力的推荐实现路径。当前推荐做法是把 ASR/TTS 放到独立 `unifiedTTSandASR` 服务中启动，再由 MyPrivateAgent 通过 `capability_runtime` 统一注册、健康检查、调用和治理。

本目录仅保留为：

- 旧 `/api/voice/*` 调用方的兼容层。
- 本地离线 fallback / 调试占位。
- capability runtime 在未配置外部 provider 时的 disabled-by-default local contract。

正常开发和生产部署不应把 Vosk 模型、Edge-TTS 依赖或实时识别服务安装进主后端。

## 推荐路径：unifiedTTSandASR

在 MyPrivateAgent `.env` 中启用外部语音 provider：

```env
ENABLE_EXTERNAL_VOICE_CAPABILITY_PROVIDER=true
VOICE_CAPABILITY_PROVIDER_BASE_URL=http://127.0.0.1:8010
VOICE_CAPABILITY_PROVIDER_TIMEOUT_SECONDS=5
```

主项目调用：

```http
GET  /api/capabilities
GET  /api/capabilities/heartbeat
GET  /api/capabilities/voice.tts.edge/health
POST /api/capabilities/voice.tts.edge/invoke
GET  /api/capabilities/voice.asr.vosk/health
POST /api/capabilities/voice.asr.vosk/invoke
WS   /api/capabilities/voice.asr.vosk/stream
```

外部 provider 自己负责：

- Vosk / ASR 服务进程。
- Edge-TTS 或其他 TTS provider。
- 音频转码、采样率、PCM chunk 管理。
- provider 自测页面，例如 `unifiedTTSandASR/static/index.html`。
- 模型、依赖、容器、进程监控和资源限制。

## 兼容目录

```text
backend/voice_runtime/
  contracts.py
  service.py
  providers/
    edge_tts_provider.py
    vosk_server_provider.py
  requirements-voice.txt
backend/routers/voice.py
```

这些文件可以保留，但后续新增功能不应优先落在这里。只有明确为了兼容旧 `/api/voice/*`、本地 fallback 或删除前迁移时，才应修改这个目录。

## Legacy 环境变量

默认保持关闭：

```env
ENABLE_VOICE_RUNTIME=false
VOICE_ASR_PROVIDER=vosk_server
VOICE_TTS_PROVIDER=edge_tts
VOSK_MODE=server
VOSK_SERVER_URL=ws://127.0.0.1:2700
VOSK_LANGUAGE=zh-cn
VOSK_SAMPLE_RATE=16000
EDGE_TTS_DEFAULT_VOICE=zh-CN-XiaoxiaoNeural
EDGE_TTS_RATE=+0%
EDGE_TTS_VOLUME=+0%
EDGE_TTS_PITCH=+0Hz
```

只有确实需要本地 fallback 时才安装：

```powershell
pip install -r backend\voice_runtime\requirements-voice.txt
```

## 兼容接口

### `GET /api/voice/capabilities`

返回 legacy local runtime 状态。响应会包含：

- `runtime_role = legacy_local_fallback`
- `recommended_runtime.provider = unifiedTTSandASR`
- `recommended_runtime.base_path = /api/capabilities`

### `POST /api/voice/asr`

旧文件转写入口。新调用方应优先使用：

```http
POST /api/capabilities/voice.asr.vosk/invoke
```

### `WS /api/voice/asr/ws`

旧实时 ASR 入口。新调用方应优先使用：

```http
WS /api/capabilities/voice.asr.vosk/stream
```

### `POST /api/voice/tts`

旧 TTS 入口。新调用方应优先使用：

```http
POST /api/capabilities/voice.tts.edge/invoke
```

## 前端约束

主聊天麦克风应使用 `capabilityApi.health('voice.asr.vosk')` 和 `/api/capabilities/voice.asr.vosk/stream`。旧 `voiceApi` 仅作为兼容 API wrapper，不应成为新功能入口。

## 企业级边界

- 主包不强制安装 `vosk`、`edge-tts`、`websockets`。
- Provider 只允许懒加载，禁止模块 import 时触发模型下载或外部连接。
- 能力探测优先于直接执行，前端应先读取 capability health 再决定展示哪些语音控件。
- 真实音频存储、审计、脱敏、权限策略应作为后续 OpenSpec change 单独推进。
- 删除 `/api/voice/*` 或 `backend/voice_runtime/` 属于 breaking change，必须另开规格。
