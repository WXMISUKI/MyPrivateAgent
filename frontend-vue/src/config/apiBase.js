const DEFAULT_REMOTE_API_BASE_URL = 'https://myprivateagent-backend-production.up.railway.app/api'

function normalizeBaseUrl(url) {
  const value = String(url || '').trim()
  if (!value) return ''
  return value.replace(/\/+$/, '')
}

function inferApiBaseByHostname(hostname) {
  const host = String(hostname || '').toLowerCase()
  if (!host) return ''
  if (host === 'localhost' || host === '127.0.0.1') return '/api'
  if (host.endsWith('.vercel.app')) return DEFAULT_REMOTE_API_BASE_URL
  return ''
}

export function getApiBaseUrl() {
  if (typeof globalThis !== 'undefined') {
    const runtime = normalizeBaseUrl(globalThis.__APP_CONFIG__?.apiBaseUrl)
    if (runtime) return runtime
  }

  const envValue = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL)
  if (envValue) return envValue

  const inferred = normalizeBaseUrl(
    typeof globalThis !== 'undefined' ? inferApiBaseByHostname(globalThis.location?.hostname) : ''
  )
  if (inferred) return inferred

  return DEFAULT_REMOTE_API_BASE_URL
}

export function buildApiUrl(path = '') {
  const base = getApiBaseUrl()
  const normalizedPath = String(path || '').startsWith('/') ? String(path || '') : `/${String(path || '')}`
  return `${base}${normalizedPath}`
}

