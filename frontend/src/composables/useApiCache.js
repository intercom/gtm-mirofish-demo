import { ref, shallowRef, onUnmounted } from 'vue'
import client from '../api/client'

/**
 * Shared in-memory cache store.
 * Each entry: { data, timestamp, promise? }
 */
const store = new Map()

const DEFAULT_TTL = 60_000 // 1 minute

function isExpired(entry, ttl) {
  return Date.now() - entry.timestamp > ttl
}

/**
 * Clear all cached entries, or entries matching a prefix.
 * @param {string} [prefix] - If provided, only clears keys starting with this prefix.
 */
export function clearApiCache(prefix) {
  if (!prefix) {
    store.clear()
    return
  }
  for (const key of store.keys()) {
    if (key.startsWith(prefix)) store.delete(key)
  }
}

/**
 * Composable for cached GET requests.
 *
 * Deduplicates in-flight requests to the same URL and serves cached data
 * within the TTL window. Uses stale-while-revalidate: returns cached data
 * immediately, then refreshes in the background.
 *
 * @param {string} url - The API path (relative to client baseURL).
 * @param {object} [options]
 * @param {number} [options.ttl=60000] - Cache lifetime in milliseconds.
 * @param {object} [options.params] - Axios query params.
 * @param {boolean} [options.immediate=true] - Fetch on creation.
 * @param {boolean} [options.staleWhileRevalidate=true] - Return stale data while refreshing.
 */
export function useApiCache(url, options = {}) {
  const {
    ttl = DEFAULT_TTL,
    params = null,
    immediate = true,
    staleWhileRevalidate = true,
  } = options

  const data = shallowRef(null)
  const error = ref(null)
  const loading = ref(false)

  const cacheKey = params ? `${url}?${new URLSearchParams(params)}` : url

  async function fetch(force = false) {
    const cached = store.get(cacheKey)

    // Serve from cache if valid and not forced
    if (!force && cached && !isExpired(cached, ttl)) {
      data.value = cached.data
      return cached.data
    }

    // Stale-while-revalidate: return stale data immediately
    if (staleWhileRevalidate && cached?.data) {
      data.value = cached.data
    }

    // Deduplicate in-flight requests
    if (cached?.promise) {
      try {
        const result = await cached.promise
        data.value = result
        return result
      } catch (e) {
        error.value = e
        throw e
      }
    }

    loading.value = true
    error.value = null

    const promise = client
      .get(url, { params })
      .then((res) => {
        const result = res.data
        store.set(cacheKey, { data: result, timestamp: Date.now() })
        data.value = result
        return result
      })
      .catch((e) => {
        error.value = e
        // Remove failed promise so future calls retry
        const entry = store.get(cacheKey)
        if (entry?.promise === promise) {
          if (entry.data) {
            // Keep stale data, just remove the promise
            entry.promise = null
          } else {
            store.delete(cacheKey)
          }
        }
        throw e
      })
      .finally(() => {
        loading.value = false
        // Clean up the promise ref
        const entry = store.get(cacheKey)
        if (entry?.promise === promise) entry.promise = null
      })

    // Store the promise for deduplication
    const existing = store.get(cacheKey)
    if (existing) {
      existing.promise = promise
    } else {
      store.set(cacheKey, { data: null, timestamp: 0, promise })
    }

    return promise
  }

  function refresh() {
    return fetch(true)
  }

  function invalidate() {
    store.delete(cacheKey)
  }

  if (immediate) fetch()

  onUnmounted(() => {
    // Don't clear the cache entry on unmount — other components may use it
  })

  return { data, error, loading, fetch, refresh, invalidate }
}
