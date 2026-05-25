import { beforeEach, describe, expect, it, vi } from 'vitest'

import { writeTextToClipboard } from '../governanceClipboard'

describe('governanceClipboard', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('falls back to execCommand copy when clipboard api is unavailable', async () => {
    const appendChild = vi.fn()
    const removeChild = vi.fn()
    const focus = vi.fn()
    const select = vi.fn()
    const execCommand = vi.fn().mockReturnValue(true)
    const createElement = vi.fn(() => ({
      value: '',
      setAttribute: vi.fn(),
      style: {},
      focus,
      select,
    }))

    globalThis.navigator = {}
    globalThis.document = {
      createElement,
      body: { appendChild, removeChild },
      execCommand,
    }

    await writeTextToClipboard('hello world')

    expect(createElement).toHaveBeenCalledWith('textarea')
    expect(execCommand).toHaveBeenCalledWith('copy')
    expect(appendChild).toHaveBeenCalled()
    expect(removeChild).toHaveBeenCalled()
  })
})
