import { ref, reactive, readonly } from 'vue'

const MAX_HISTORY = 60

const enabled = ref(false)
const components = reactive({})

function getOrCreate(name) {
  if (!components[name]) {
    components[name] = {
      renderCount: 0,
      lastRenderMs: 0,
      avgRenderMs: 0,
      maxRenderMs: 0,
      fps: 0,
      domNodes: 0,
      history: [],
      // FPS tracking internals
      _frameTimes: [],
      _lastFrameTs: 0,
    }
  }
  return components[name]
}

function measure(name, renderFn) {
  if (!enabled.value) {
    renderFn()
    return
  }

  const entry = getOrCreate(name)
  const t0 = performance.now()
  renderFn()
  const elapsed = performance.now() - t0

  entry.renderCount++
  entry.lastRenderMs = Math.round(elapsed * 100) / 100
  entry.maxRenderMs = Math.max(entry.maxRenderMs, entry.lastRenderMs)
  entry.history.push(entry.lastRenderMs)
  if (entry.history.length > MAX_HISTORY) entry.history.shift()
  entry.avgRenderMs =
    Math.round((entry.history.reduce((s, v) => s + v, 0) / entry.history.length) * 100) / 100
}

function trackFrame(name) {
  if (!enabled.value) return

  const entry = getOrCreate(name)
  const now = performance.now()

  if (entry._lastFrameTs) {
    entry._frameTimes.push(now - entry._lastFrameTs)
    if (entry._frameTimes.length > MAX_HISTORY) entry._frameTimes.shift()
    const avgFrameMs =
      entry._frameTimes.reduce((s, v) => s + v, 0) / entry._frameTimes.length
    entry.fps = avgFrameMs > 0 ? Math.round(1000 / avgFrameMs) : 0
  }
  entry._lastFrameTs = now
}

function countDomNodes(name, container) {
  if (!enabled.value || !container) return

  const entry = getOrCreate(name)
  entry.domNodes = container.querySelectorAll('*').length
}

function clear() {
  for (const key of Object.keys(components)) {
    delete components[key]
  }
}

export function useD3PerfMonitor() {
  return {
    enabled,
    components: readonly(components),
    measure,
    trackFrame,
    countDomNodes,
    clear,
  }
}
