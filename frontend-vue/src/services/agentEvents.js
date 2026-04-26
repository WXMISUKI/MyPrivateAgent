export function normalizeAgentEvent(rawEvent) {
  const event = rawEvent || {}
  const payload = event.payload || {}

  return {
    ...payload,
    ...event,
    payload,
    type: event.type || payload.type || 'unknown',
    status_kind: event.status_kind ?? payload.status_kind ?? '',
    content: event.content ?? payload.content ?? '',
    answer: event.answer ?? payload.answer ?? '',
    reasoning: event.reasoning ?? payload.reasoning ?? '',
    reasoning_content: event.reasoning_content ?? payload.reasoning_content ?? event.reasoning ?? payload.reasoning ?? '',
    tool_spec: event.tool_spec ?? payload.tool_spec ?? null,
    tool_execution: event.tool_execution ?? payload.tool_execution ?? null,
    cache_hit: event.cache_hit ?? payload.cache_hit ?? null,
    duration_ms: event.duration_ms ?? payload.duration_ms ?? null,
    result_source: event.result_source ?? payload.result_source ?? '',
    status: event.status ?? payload.status ?? '',
    selected_items: event.selected_items ?? payload.selected_items ?? [],
    skipped_items: event.skipped_items ?? payload.skipped_items ?? [],
    scope: event.scope ?? payload.scope ?? '',
    prompt_count: event.prompt_count ?? payload.prompt_count ?? 0,
    practice_count: event.practice_count ?? payload.practice_count ?? 0,
    plan: event.plan ?? payload.plan ?? null,
    message_id: event.message_id ?? payload.message_id ?? null,
    card: event.card ?? payload.card ?? event.structured_content ?? payload.structured_content ?? null,
    card_schema: event.card_schema ?? payload.card_schema ?? event.card?.schema ?? payload.card?.schema ?? payload.tool_spec?.card_schema ?? null,
    render_mode: event.render_mode ?? payload.render_mode ?? payload.tool_spec?.render_mode ?? null
  }
}

export function createStreamingEventParser(onEvent) {
  let jsonBuffer = ''
  let lineBuffer = ''
  let lastProcessedIndex = 0

  function processResponseText(responseText) {
    const safeText = String(responseText || '')
    if (lastProcessedIndex >= safeText.length) {
      return
    }

    const newData = safeText.slice(lastProcessedIndex)
    lastProcessedIndex = safeText.length

    const combined = lineBuffer + newData
    const lines = combined.split('\n')
    lineBuffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) {
        continue
      }

      jsonBuffer += line.slice(6)

      try {
        const data = JSON.parse(jsonBuffer)
        jsonBuffer = ''
        onEvent(data)
      } catch (error) {
        // JSON 可能还没完整到齐，继续缓冲
      }
    }
  }

  function flush(responseText) {
    processResponseText(responseText)

    if (lineBuffer.startsWith('data: ')) {
      jsonBuffer += lineBuffer.slice(6)
    }
    lineBuffer = ''

    if (!jsonBuffer.trim()) {
      return
    }

    try {
      const data = JSON.parse(jsonBuffer)
      jsonBuffer = ''
      onEvent(data)
    } catch (error) {
      // 仍然不是完整 JSON 时直接丢弃，避免重复污染后续请求
      jsonBuffer = ''
    }
  }

  function reset() {
    jsonBuffer = ''
    lineBuffer = ''
    lastProcessedIndex = 0
  }

  return {
    processResponseText,
    flush,
    reset
  }
}
