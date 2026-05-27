# Voice Input Web Speech

## Why

当前聊天输入区只支持键盘输入。用户希望像 Codex App 对话框一样，在输入框中通过麦克风语音输入，并实时转成文字后继续走现有 `/api/chat`。小米 MiMo 示例和文档是 TTS 文本转语音，不是实时语音识别；因此 v1 先采用浏览器 Web Speech API 实现输入增强，避免引入后端音频上传和未确认的 ASR provider contract。

## What Changes

- 在 ChatView 输入区新增麦克风按钮，支持开始/停止语音识别。
- 使用浏览器 `SpeechRecognition` / `webkitSpeechRecognition`，`lang = zh-CN`、`continuous = true`、`interimResults = true`。
- interim result 实时进入 textarea，final result 保留在输入框，发送仍走现有 `/api/chat`。
- 浏览器不支持时按钮禁用并展示不可用提示。
- `.env` 预留小米 MiMo TTS 配置占位，不参与本轮语音输入。

## Non-goals

- 不新增后端 ASR API。
- 不上传用户音频。
- 不改变 `ChatRequest` 或 `/api/chat`。
- 不实现助手回复朗读。
- 不调用小米 TTS。

## Impact

- Frontend: `frontend-vue/src/views/ChatView.vue` 和其 focused tests。
- Config: `.env` 增加未来 TTS provider 占位变量。
- Specs: 新增 `voice-input-web-speech` 规格并归档。
