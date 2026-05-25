import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useConversationStore } from '../conversation'
import { useSettingsStore } from '../settings'
import storage from '../../services/storage'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

class FakeXMLHttpRequest {
  static responseText = ''
  static autoComplete = true
  static lastInstance = null

  constructor() {
    this.headers = {}
    this.readyState = 0
    this.responseText = ''
    this.status = 200
    this.timeout = 0
    this.onload = null
    this.onprogress = null
    this.onerror = null
    this.ontimeout = null
    this.onabort = null
    FakeXMLHttpRequest.lastInstance = this
  }

  open(method, url) {
    this.method = method
    this.url = url
  }

  setRequestHeader(key, value) {
    this.headers[key] = value
  }

  send(body) {
    this.body = body
    if (!FakeXMLHttpRequest.autoComplete) {
      return
    }
    this.complete()
  }

  complete() {
    this.readyState = 3
    this.responseText = FakeXMLHttpRequest.responseText
    if (typeof this.onprogress === 'function') {
      this.onprogress()
    }
    this.readyState = 4
    if (typeof this.onload === 'function') {
      this.onload()
    }
  }

  abort() {
    this.status = 0
    if (typeof this.onabort === 'function') {
      this.onabort()
    }
  }
}

describe('conversation store', () => {
  const originalXMLHttpRequest = global.XMLHttpRequest

  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.restoreAllMocks()
    vi.spyOn(storage, 'saveConversations')
    vi.spyOn(storage, 'setActiveId')
    global.XMLHttpRequest = FakeXMLHttpRequest
    FakeXMLHttpRequest.autoComplete = true
    FakeXMLHttpRequest.responseText = ''
    FakeXMLHttpRequest.lastInstance = null
  })

  afterEach(() => {
    global.XMLHttpRequest = originalXMLHttpRequest
  })

  it('streams assistant response into the active conversation', async () => {
    FakeXMLHttpRequest.responseText = [
      'data: {"type":"conversation_id","conversation_id":321}',
      'data: {"type":"status","status_kind":"execution_progress","phase":"intent_routing","content":"正在识别你的复合需求"}',
      'data: {"type":"content","content":"你好"}',
      'data: {"type":"done","message_id":654,"content":"你好，世界"}',
      ''
    ].join('\n')

    const store = useConversationStore()

    await store.addMessage({
      id: 1,
      role: 'user',
      content: '测试一下',
      timestamp: Date.now()
    })

    const result = await store.sendMessage('测试一下', 'doubao')

    expect(result.id).toBe(654)
    expect(store.currentConversation.id).toBe(321)
    expect(store.currentConversation.messages).toHaveLength(2)
    expect(store.currentConversation.messages[1]).toMatchObject({
      id: 654,
      role: 'assistant',
      content: '你好，世界',
      isGenerating: false
    })
    expect(store.currentConversation.messages[1].executionProgress).toHaveLength(1)
    expect(store.currentConversation.messages[1].executionProgress[0]).toMatchObject({
      phase: 'intent_routing',
      content: '正在识别你的复合需求'
    })
    expect(store.isLoading).toBe(false)
  })

  it('includes typed execution_context when main chat runtime trace is enabled', async () => {
    FakeXMLHttpRequest.responseText = [
      'data: {"type":"done","content":"你好"}',
      ''
    ].join('\n')

    const store = useConversationStore()
    const settingsStore = useSettingsStore()
    settingsStore.setEnableMainChatRuntimeTrace(true)

    await store.addMessage({
      id: 1,
      role: 'user',
      content: '测试 runtime trace',
      timestamp: Date.now()
    })

    await store.sendMessage('测试 runtime trace', 'doubao')

    const body = JSON.parse(FakeXMLHttpRequest.lastInstance.body)
    expect(body.execution_context).toMatchObject({
      run_kind: 'chat',
      enable_main_chat_query_control_timeline: true,
      agent_id: 'chat-ui-doubao'
    })
    expect(body.execution_context.run_id).toMatch(/^manual-chat-/)
  })

  it('stores completion check metadata on assistant message when framework fallback content is emitted', async () => {
    FakeXMLHttpRequest.responseText = [
      'data: {"type":"content","content":"阶段性建议","framework_notice":true,"completion_check":{"should_finalize":true,"missing_parts":["transport","play"]}}',
      'data: {"type":"done","content":"阶段性建议"}',
      ''
    ].join('\n')

    const store = useConversationStore()

    await store.addMessage({
      id: 1,
      role: 'user',
      content: '测试阶段性建议',
      timestamp: Date.now()
    })

    await store.sendMessage('测试阶段性建议', 'doubao')

    expect(store.currentConversation.messages[1].frameworkNotice).toBe(true)
    expect(store.currentConversation.messages[1].completionCheck).toMatchObject({
      should_finalize: true,
      missing_parts: ['transport', 'play']
    })
  })

  it('finalizes assistant message when stream emits error event', async () => {
    FakeXMLHttpRequest.responseText = [
      'data: {"type":"conversation_id","conversation_id":321}',
      'data: {"type":"error","error":"模型调用失败"}',
      ''
    ].join('\n')

    const store = useConversationStore()

    await store.addMessage({
      id: 1,
      role: 'user',
      content: '测试错误态',
      timestamp: Date.now()
    })

    const result = await store.sendMessage('测试错误态', 'doubao')

    expect(result.content).toBe('模型调用失败')
    expect(store.currentConversation.messages[1]).toMatchObject({
      role: 'assistant',
      content: '模型调用失败',
      isGenerating: false
    })
    expect(store.isLoading).toBe(false)
  })

  it('uses fallback content when stream returns empty successful response', async () => {
    FakeXMLHttpRequest.responseText = ''

    const store = useConversationStore()

    await store.addMessage({
      id: 1,
      role: 'user',
      content: '测试空响应',
      timestamp: Date.now()
    })

    const result = await store.sendMessage('测试空响应', 'doubao')

    expect(result.content).toBe('')
    expect(store.currentConversation.messages[1]).toMatchObject({
      role: 'assistant',
      content: '',
      isGenerating: false
    })
    expect(store.isLoading).toBe(false)
  })

  it('aborts the active generation request and finalizes the assistant message', async () => {
    FakeXMLHttpRequest.autoComplete = false
    FakeXMLHttpRequest.responseText = [
      'data: {"type":"content","content":"正在生成"}',
      ''
    ].join('\n')

    const store = useConversationStore()

    await store.addMessage({
      id: 1,
      role: 'user',
      content: '测试停止生成',
      timestamp: Date.now()
    })

    const pendingResult = store.sendMessage('测试停止生成', 'doubao')
    expect(store.isLoading).toBe(true)
    expect(FakeXMLHttpRequest.lastInstance).toBeTruthy()

    store.abortCurrentRequest()
    const result = await pendingResult

    expect(result.content).toBe('已停止生成')
    expect(store.currentConversation.messages[1]).toMatchObject({
      role: 'assistant',
      content: '已停止生成',
      isGenerating: false
    })
    expect(store.isLoading).toBe(false)
  })

  it('shows timeout message instead of user-stop message when stream watchdog aborts the request', async () => {
    FakeXMLHttpRequest.autoComplete = false
    FakeXMLHttpRequest.responseText = [
      'data: {"type":"content","content":"正在整理"}',
      ''
    ].join('\n')

    const store = useConversationStore()

    await store.addMessage({
      id: 1,
      role: 'user',
      content: '测试超时',
      timestamp: Date.now()
    })

    const pendingResult = store.sendMessage('测试超时', 'doubao')
    expect(FakeXMLHttpRequest.lastInstance).toBeTruthy()

    FakeXMLHttpRequest.lastInstance._abortReason = 'timeout'
    FakeXMLHttpRequest.lastInstance.abort()
    const result = await pendingResult

    expect(result.content).toBe('生成超时，请稍后重试')
    expect(store.currentConversation.messages[1]).toMatchObject({
      role: 'assistant',
      content: '生成超时，请稍后重试',
      isGenerating: false
    })
  })

  it('submits positive feedback and updates the assistant message', async () => {
    axios.post.mockResolvedValue({
      data: {
        feedback_type: 'positive',
        score: 5,
        comment: '很有帮助',
        runtime_scope: 'conversation',
        created_learning_id: 88,
        feedback_metadata: {
          selected_reasons: ['accurate']
        }
      }
    })

    localStorage.setItem('token', 'test-token')

    const store = useConversationStore()
    store.conversations = [{
      id: 123,
      title: '测试会话',
      modelName: 'doubao',
      messages: [
        {
          id: 456,
          role: 'assistant',
          content: '初始回答',
          timestamp: Date.now()
        }
      ],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    store.activeId = 123

    const result = await store.submitMessageFeedback({
      messageId: 456,
      feedbackType: 'positive',
      score: 5,
      comment: '  很有帮助  ',
      selectedReasons: [' accurate ', '', '']
    })

    expect(axios.post).toHaveBeenCalledWith(
      '/api/conversations/123/feedback',
      {
        message_id: 456,
        feedback_type: 'positive',
        score: 5,
        comment: '很有帮助',
        selected_reasons: ['accurate']
      },
      {
        headers: {
          Authorization: 'Bearer test-token',
          'Content-Type': 'application/json'
        }
      }
    )
    expect(result.feedback_type).toBe('positive')
    expect(store.currentConversation.messages[0].feedback).toMatchObject({
      type: 'positive',
      score: 5,
      comment: '很有帮助',
      runtime_scope: 'conversation',
      created_learning_id: 88,
      metadata: {
        selected_reasons: ['accurate']
      }
    })
    expect(storage.saveConversations).toHaveBeenCalled()
  })

  it('submits negative feedback without message id and preserves response payload', async () => {
    axios.post.mockResolvedValue({
      data: {
        feedback_type: 'negative',
        score: 1,
        comment: '原因已记录',
        feedback_metadata: {
          selected_reasons: ['incorrect', 'incomplete']
        }
      }
    })

    const store = useConversationStore()
    store.conversations = [{
      id: 99,
      title: '测试会话',
      modelName: 'doubao',
      messages: [
        {
          id: 'assistant_local',
          role: 'assistant',
          content: '待反馈回答',
          timestamp: Date.now()
        }
      ],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    store.activeId = 99

    await store.submitMessageFeedback({
      messageId: 'assistant_local',
      feedbackType: 'negative',
      score: 1,
      comment: '  原因已记录 ',
      selectedReasons: ['incorrect', 'incomplete']
    })

    expect(axios.post).toHaveBeenCalledWith(
      '/api/conversations/99/feedback',
      {
        feedback_type: 'negative',
        score: 1,
        comment: '原因已记录',
        selected_reasons: ['incorrect', 'incomplete']
      },
      {
        headers: {}
      }
    )
    expect(store.currentConversation.messages[0].feedback).toMatchObject({
      type: 'negative',
      score: 1,
      comment: '原因已记录',
      metadata: {
        selected_reasons: ['incorrect', 'incomplete']
      }
    })
  })

  it('rejects feedback submission when there is no active conversation', async () => {
    const store = useConversationStore()

    await expect(store.submitMessageFeedback({
      feedbackType: 'positive'
    })).rejects.toThrow('当前没有活动会话')
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('rejects feedback submission when the conversation is still local', async () => {
    const store = useConversationStore()
    store.conversations = [{
      id: 'local_123',
      title: '本地会话',
      modelName: 'doubao',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    store.activeId = 'local_123'

    await expect(store.submitMessageFeedback({
      feedbackType: 'positive'
    })).rejects.toThrow('会话尚未同步，暂不可提交反馈')
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('rejects invalid feedback types before calling the API', async () => {
    const store = useConversationStore()
    store.conversations = [{
      id: 777,
      title: '测试会话',
      modelName: 'doubao',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    store.activeId = 777

    await expect(store.submitMessageFeedback({
      feedbackType: 'bad_type'
    })).rejects.toThrow('feedback_type 无效')
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('rethrows feedback API errors and keeps local message state unchanged', async () => {
    const apiError = new Error('request failed')
    axios.post.mockRejectedValue(apiError)

    const store = useConversationStore()
    store.conversations = [{
      id: 222,
      title: '测试会话',
      modelName: 'doubao',
      messages: [
        {
          id: 333,
          role: 'assistant',
          content: '待反馈回答',
          timestamp: Date.now()
        }
      ],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }]
    store.activeId = 222

    await expect(store.submitMessageFeedback({
      messageId: 333,
      feedbackType: 'negative',
      score: 1,
      comment: '不准确'
    })).rejects.toBe(apiError)
    expect(store.currentConversation.messages[0].feedback).toBeUndefined()
  })
})
