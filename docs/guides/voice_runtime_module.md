# 统一语音运行时模块

## 定位
语音能力作为独立可选模块接入 MyPrivateAgent，不随主运行层强制打包。主项目负责统一接口、能力探测、权限与治理入口；ASR/TTS provider 只作为可替换执行器。

当前 v1 收口：
- ASR：预留 `vosk_server`，推荐把 Vosk 模型和实时识别服务作为独立进程部署。
- TTS：预留 `edge_tts`，通过可选 Python 依赖生成音频。
- Chat：不改变 `/api/chat`，前端仍可把转写文本送入现有对话链路。

## 目录
```text
backend/voice_runtime/
  contracts.py
  service.py
  providers/
    edge_tts_provider.py
  requirements-voice.txt
backend/routers/voice.py
frontend-vue/src/api/index.js
```

## 环境变量
默认不开启：

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

启用可选依赖：

```powershell
pip install -r backend\voice_runtime\requirements-voice.txt
```

Vosk 模型文件不进入仓库。生产部署建议把 Vosk 服务、模型目录、资源限制、进程监控放在独立容器或独立服务中管理，再通过 `VOSK_SERVER_URL` 暴露给后端。

## 后端接口
### `GET /api/voice/capabilities`
返回当前能力合同。即使未启用或未安装可选依赖也必须可用。

关键字段：
- `contract_version`: 固定为 `voice-runtime-v1`
- `enabled`: 是否启用语音运行时
- `asr.provider`: 当前 ASR provider
- `asr.status`: `disabled / unconfigured / missing_dependency / ready / unsupported`
- `tts.provider`: 当前 TTS provider
- `tts.status`: `disabled / missing_dependency / ready / unsupported`

### `POST /api/voice/asr`
文件转写入口。当前 v1 主要用于统一接口占位和不可用状态治理；实时 Vosk 推荐走 WebSocket。

不可用时返回：

```json
{
  "error": {
    "code": "VOICE_RUNTIME_DISABLED",
    "message": "Voice runtime is disabled. Set ENABLE_VOICE_RUNTIME=true to enable it.",
    "provider": "vosk_server"
  }
}
```

### `WS /api/voice/asr/ws`
实时 ASR 入口。客户端发送二进制 PCM 音频块，后端代理到 `VOSK_SERVER_URL`，并把 Vosk 返回的 `partial/text` 结果包装为统一 JSON。

结束一次识别时，客户端可以发送文本帧：

```text
__end__
```

返回示例：

```json
{
  "ok": true,
  "provider": "vosk_server",
  "language": "zh-cn",
  "text": "查询订单状态",
  "partial": false,
  "raw": {
    "text": "查询订单状态"
  }
}
```

### `POST /api/voice/tts`
文本转语音入口。启用 `edge_tts` 并安装可选依赖后返回音频 blob，默认媒体类型为 `audio/mpeg`。

请求示例：

```json
{
  "text": "您好，请问有什么可以帮您？",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%",
  "volume": "+0%",
  "pitch": "+0Hz"
}
```

## 前端调用
前端统一使用 `voiceApi`：

```js
import { voiceApi } from '@/api'

const capabilities = await voiceApi.getCapabilities()
const audioBlob = await voiceApi.synthesizeSpeech({ text: '您好' })
const transcript = await voiceApi.transcribeAudio(file, { language: 'zh-cn' })
```

浏览器端 Web Speech 输入仍是最低成本输入方案；后端 Vosk ASR 用于需要统一审计、统一部署或浏览器兼容性不足的场景。

## 企业级边界
- 主包不强制安装 `vosk`、`edge-tts`、`websockets`。
- Provider 只允许懒加载，禁止模块 import 时触发模型下载或外部连接。
- 能力探测优先于直接执行，前端应先读取 `capabilities` 再决定展示哪些语音控件。
- 真实音频存储、审计、脱敏、权限策略应作为后续 OpenSpec change 单独推进。
