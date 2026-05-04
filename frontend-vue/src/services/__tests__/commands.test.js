import { describe, expect, it } from 'vitest'

import { getCommandById, parseCommand } from '../commands'

describe('commands service', () => {
  it('parses doctor governance command with params', () => {
    const parsed = parseCommand('/doctor governance')

    expect(parsed.command.id).toBe('doctor')
    expect(parsed.command.hasParam).toBe(true)
    expect(parsed.params).toEqual(['governance'])
  })

  it('includes framework commands in local fallback registry', () => {
    expect(getCommandById('doctor')?.action).toBe('run_doctor')
    expect(getCommandById('doctor')?.paramHint).toBe('/doctor <startup|governance> [warning]')
    expect(getCommandById('snapshot')?.action).toBe('open_snapshot')
    expect(getCommandById('snapshot')?.paramHint).toBe('/snapshot <snapshot_id>')
    expect(getCommandById('plan')?.action).toBe('open_planner')
    expect(getCommandById('memory')?.action).toBe('open_memory')
    expect(getCommandById('gaps')?.paramHint).toBe('/gaps <all|warning|snapshot <id>>')
    expect(getCommandById('permissions')?.paramHint).toBe('/permissions <all|warning|snapshot <id>>')
    expect(getCommandById('mcp')?.paramHint).toBe('/mcp <all|warning|snapshot <id>>')
  })
})
