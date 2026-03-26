import axios from 'axios'
import { perfMonitor } from '../lib/perfMonitor'

export const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

function getCookie(name) {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// Attach CSRF token from cookie to state-changing requests
client.interceptors.request.use((config) => {
  const method = config.method?.toUpperCase()
  if (method && method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    const token = getCookie('csrf_token')
    if (token) {
      config.headers['X-CSRFToken'] = token
    }
  }
  return config
})

// --- Request deduplication ---
// Concurrent identical GET requests share a single network call.
// Map<key, Promise<AxiosResponse>> — entries removed when the request settles.
const inflight = new Map()
const isDev = import.meta.env.DEV

function buildKey(config) {
  const params = config.params
    ? JSON.stringify(config.params, Object.keys(config.params).sort())
    : ''
  return `${config.method}:${config.baseURL || ''}${config.url}${params}`
}

const defaultAdapter = axios.getAdapter(axios.defaults.adapter)

client.defaults.adapter = (config) => {
  if (config.method !== 'get') return defaultAdapter(config)

  const key = buildKey(config)
  const existing = inflight.get(key)
  if (existing) {
    if (isDev) console.debug(`[DEDUP] Reusing in-flight request: ${key}`)
    return existing
  }

  const promise = defaultAdapter(config).finally(() => {
    inflight.delete(key)
  })
  inflight.set(key, promise)
  return promise
}

perfMonitor.createAxiosTimingInterceptors(client)

// Attach Bearer token from localStorage (avoids circular Pinia import)
client.interceptors.request.use((config) => {
  try {
    const saved = localStorage.getItem('mirofish-auth')
    if (saved) {
      const { token } = JSON.parse(saved)
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
  } catch {
    // Corrupted storage — skip
  }
  return config
})

// Normalize errors so callers always get { message, status, data }
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const normalized = {
      message:
        error.response?.data?.error ||
        error.response?.data?.message ||
        error.message ||
        'Network error',
      status: error.response?.status || 0,
      data: error.response?.data || null,
    }
    return Promise.reject(normalized)
  },
)

export default client
