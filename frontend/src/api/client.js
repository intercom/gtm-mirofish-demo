import axios from 'axios'
import { perfMonitor } from '../lib/perfMonitor'

export const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
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
