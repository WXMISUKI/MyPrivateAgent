import { describe, expect, it, vi } from 'vitest'
import { createStreamingEventParser, normalizeAgentEvent } from '../agentEvents'

describe('normalizeAgentEvent', () => {
  it('merges payload fields into the normalized event', () => {
    const event = normalizeAgentEvent({
      payload: {
        type: 'done',
        content: 'hello',
        card_schema: 'weather.v1',
        render_mode: 'structured_card'
      }
    })

    expect(event.type).toBe('done')
    expect(event.content).toBe('hello')
    expect(event.card_schema).toBe('weather.v1')
    expect(event.render_mode).toBe('structured_card')
  })

  it('keeps planner payloads available for planner refresh', () => {
    const event = normalizeAgentEvent({
      type: 'plan_updated',
      payload: {
        plan: {
          id: 9,
          status: 'in_progress'
        }
      }
    })

    expect(event.type).toBe('plan_updated')
    expect(event.plan).toMatchObject({
      id: 9,
      status: 'in_progress'
    })
  })

  it('keeps execution progress metadata available for UI summary rendering', () => {
    const event = normalizeAgentEvent({
      type: 'status',
      payload: {
        status_kind: 'execution_progress',
        phase: 'tool_execution',
        content: '正在检索天气信息'
      }
    })

    expect(event.status_kind).toBe('execution_progress')
    expect(event.phase).toBe('tool_execution')
    expect(event.content).toBe('正在检索天气信息')
  })

  it('keeps completion check metadata available for framework fallback rendering', () => {
    const event = normalizeAgentEvent({
      type: 'content',
      payload: {
        content: '阶段性建议',
        framework_notice: true,
        completion_check: {
          should_finalize: true,
          missing_parts: ['transport']
        }
      }
    })

    expect(event.framework_notice).toBe(true)
    expect(event.completion_check).toMatchObject({
      should_finalize: true,
      missing_parts: ['transport']
    })
  })
})

describe('createStreamingEventParser', () => {
  it('parses multiple complete stream events', () => {
    const onEvent = vi.fn()
    const parser = createStreamingEventParser(onEvent)

    parser.processResponseText(
      'data: {"type":"content","content":"A"}\n' +
      'data: {"type":"done","content":"AB"}\n'
    )

    expect(onEvent).toHaveBeenCalledTimes(2)
    expect(onEvent).toHaveBeenNthCalledWith(1, { type: 'content', content: 'A' })
    expect(onEvent).toHaveBeenNthCalledWith(2, { type: 'done', content: 'AB' })
  })

  it('buffers partial json until flush', () => {
    const onEvent = vi.fn()
    const parser = createStreamingEventParser(onEvent)

    parser.processResponseText('data: {"type":"content","content":"hel')
    expect(onEvent).not.toHaveBeenCalled()

    parser.flush('data: {"type":"content","content":"hello"}\n')
    expect(onEvent).toHaveBeenCalledTimes(1)
    expect(onEvent).toHaveBeenCalledWith({ type: 'content', content: 'hello' })
  })
})
