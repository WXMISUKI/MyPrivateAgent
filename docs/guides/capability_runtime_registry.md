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

## 前端调用
```js
import { capabilityApi } from '@/api'

const list = await capabilityApi.list()
const tts = await capabilityApi.get('voice.tts.edge')
const health = await capabilityApi.health('voice.tts.edge')
const result = await capabilityApi.invoke('voice.tts.edge', { text: '您好' })
```

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
