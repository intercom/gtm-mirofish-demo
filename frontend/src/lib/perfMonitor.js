const MAX_ENTRIES = 100
const SLOW_THRESHOLD_MS = 2000

const isDev = import.meta.env.DEV

const metrics = {
  pageLoad: [],
  routeNavigation: [],
  apiResponse: [],
  componentRender: [],
  wsLatency: [],
}

function push(metricName, value, meta) {
  const bucket = metrics[metricName]
  if (!bucket) return
  const entry = { value, timestamp: Date.now() }
  if (meta) entry.meta = meta
  bucket.push(entry)
  if (bucket.length > MAX_ENTRIES) bucket.shift()
  if (isDev && value > SLOW_THRESHOLD_MS) {
    console.warn(`[perf] Slow ${metricName}: ${value.toFixed(1)}ms`)
  }
}

function getRawEntries(metricName) {
  return metrics[metricName] ? [...metrics[metricName]] : []
}

function percentile(metricName, p) {
  const bucket = metrics[metricName]
  if (!bucket.length) return 0
  const sorted = bucket.map((e) => e.value).sort((a, b) => a - b)
  const idx = Math.ceil((p / 100) * sorted.length) - 1
  return sorted[Math.max(0, idx)]
}

function avg(metricName) {
  const bucket = metrics[metricName]
  if (!bucket.length) return 0
  return bucket.reduce((sum, e) => sum + e.value, 0) / bucket.length
}

function getStats(metricName) {
  const bucket = metrics[metricName]
  if (!bucket.length) return { avg: 0, p95: 0, p99: 0, count: 0 }
  return {
    avg: avg(metricName),
    p95: percentile(metricName, 95),
    p99: percentile(metricName, 99),
    count: bucket.length,
  }
}

function recordPageLoad() {
  const entries = performance.getEntriesByType('navigation')
  if (!entries.length) return
  const nav = entries[0]
  push('pageLoad', nav.loadEventEnd - nav.startTime)
}

function trackRouteNavigation(router) {
  let navStart = 0
  let navTarget = ''
  router.beforeEach((to, _from, next) => {
    navStart = performance.now()
    navTarget = to.name || to.path
    next()
  })
  router.afterEach(() => {
    if (navStart) {
      push('routeNavigation', performance.now() - navStart, { route: navTarget })
      navStart = 0
    }
  })
}

function createAxiosTimingInterceptors(client) {
  client.interceptors.request.use((config) => {
    config._perfStart = performance.now()
    return config
  })
  client.interceptors.response.use(
    (response) => {
      if (response.config._perfStart) {
        push('apiResponse', performance.now() - response.config._perfStart, {
          url: response.config.url,
          method: response.config.method,
        })
      }
      return response
    },
    (error) => {
      if (error.config?._perfStart) {
        push('apiResponse', performance.now() - error.config._perfStart, {
          url: error.config.url,
          method: error.config.method,
        })
      }
      return Promise.reject(error)
    },
  )
}

function getWebVitals() {
  const nav = performance.getEntriesByType('navigation')[0]
  if (!nav) return null
  const paints = performance.getEntriesByType('paint')
  const fcp = paints.find((p) => p.name === 'first-contentful-paint')
  return {
    dns: nav.domainLookupEnd - nav.domainLookupStart,
    tcp: nav.connectEnd - nav.connectStart,
    ttfb: nav.responseStart - nav.requestStart,
    download: nav.responseEnd - nav.responseStart,
    domParsing: nav.domInteractive - nav.responseEnd,
    domContentLoaded: nav.domContentLoadedEventEnd - nav.startTime,
    load: nav.loadEventEnd - nav.startTime,
    fcp: fcp ? fcp.startTime : 0,
    transferSize: nav.transferSize || 0,
  }
}

function trackComponentRender(name, durationMs) {
  push('componentRender', durationMs)
  if (isDev && durationMs > 100) {
    console.warn(`[perf] Slow render <${name}>: ${durationMs.toFixed(1)}ms`)
  }
}

function trackWsLatency(durationMs) {
  push('wsLatency', durationMs)
}

function getAllStats() {
  return Object.fromEntries(
    Object.keys(metrics).map((k) => [k, getStats(k)]),
  )
}

function clear() {
  Object.values(metrics).forEach((bucket) => (bucket.length = 0))
}

export const perfMonitor = {
  push,
  avg,
  percentile,
  getStats,
  getAllStats,
  getRawEntries,
  getWebVitals,
  recordPageLoad,
  trackRouteNavigation,
  createAxiosTimingInterceptors,
  trackComponentRender,
  trackWsLatency,
  clear,
}
