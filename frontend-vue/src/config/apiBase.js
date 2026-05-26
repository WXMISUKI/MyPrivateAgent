const DEFAULT_API_BASE_URL = '/api'

function normalizeBaseUrl(url) {
  const value = String(url || '').trim()
  if (!value) return ''
  return value.replace(/\/+$/, '')
}

function inferApiBaseByHostname(hostname) {
  const host = String(hostname || '').toLowerCase()
  if (!host) return ''
  if (host === 'localhost' || host === '127.0.0.1') return '/api'
  if (host.endsWith('.vercel.app')) return '/api'
  return ''
}

function isVercelHost() {
  const host =
    typeof globalThis !== 'undefined' ? String(globalThis.location?.hostname || '').toLowerCase() : ''
  return host.endsWith('.vercel.app')
}

export function getApiBaseUrl() {
  if (typeof globalThis !== 'undefined') {
    const runtime = normalizeBaseUrl(globalThis.__APP_CONFIG__?.apiBaseUrl)
    if (runtime) return runtime
  }

  if (isVercelHost()) return DEFAULT_API_BASE_URL

  const envValue = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL)
  if (envValue) return envValue

  const inferred = normalizeBaseUrl(
    typeof globalThis !== 'undefined' ? inferApiBaseByHostname(globalThis.location?.hostname) : ''
  )
  if (inferred) return inferred

  return DEFAULT_API_BASE_URL
}

export function buildApiUrl(path = '') {
  const base = getApiBaseUrl()
  const normalizedPath = String(path || '').startsWith('/') ? String(path || '') : `/${String(path || '')}`
  return `${base}${normalizedPath}`
}
