import { afterEach, describe, expect, it } from 'vitest'
import { buildApiUrl, getApiBaseUrl } from '../apiBase'

function setHostname(hostname) {
  Object.defineProperty(globalThis, 'location', {
    value: { hostname },
    configurable: true
  })
}

describe('apiBase', () => {
  afterEach(() => {
    delete globalThis.__APP_CONFIG__
    setHostname('localhost')
  })

  it('prefers runtime app config over inferred host', () => {
    globalThis.__APP_CONFIG__ = {
      apiBaseUrl: 'https://runtime-config.example.com/api/'
    }
    setHostname('demo.vercel.app')

    expect(getApiBaseUrl()).toBe('https://runtime-config.example.com/api')
    expect(buildApiUrl('/chat')).toBe('https://runtime-config.example.com/api/chat')
  })

  it('uses same-origin /api on vercel host', () => {
    setHostname('my-private-agent.vercel.app')

    expect(getApiBaseUrl()).toBe('/api')
    expect(buildApiUrl('/models')).toBe('/api/models')
  })

  it('uses local /api proxy for localhost', () => {
    setHostname('localhost')

    expect(getApiBaseUrl()).toBe('/api')
    expect(buildApiUrl('/auth/me')).toBe('/api/auth/me')
  })
})
