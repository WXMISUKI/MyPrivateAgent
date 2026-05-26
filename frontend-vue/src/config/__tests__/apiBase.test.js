import { afterEach, describe, expect, it, vi } from 'vitest'
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
    vi.unstubAllEnvs()
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

  it('ignores stale build-time api base on vercel host', () => {
    setHostname('my-private-agent.vercel.app')
    vi.stubEnv('VITE_API_BASE_URL', 'https://stale-railway.example.com/api')

    expect(getApiBaseUrl()).toBe('/api')
  })

  it('uses local /api proxy for localhost', () => {
    setHostname('localhost')

    expect(getApiBaseUrl()).toBe('/api')
    expect(buildApiUrl('/auth/me')).toBe('/api/auth/me')
  })
})
