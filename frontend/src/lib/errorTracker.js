import client from '../api/client.js'

const MAX_ERRORS = 50
const errors = []
let _router = null

function getBrowserInfo() {
  return {
    userAgent: navigator.userAgent,
    language: navigator.language,
    url: window.location.href,
    viewport: { width: window.innerWidth, height: window.innerHeight },
  }
}

function getCurrentRoute() {
  if (!_router?.currentRoute?.value) return null
  const { path, name, params, query } = _router.currentRoute.value
  return { path, name, params: { ...params }, query: { ...query } }
}

function pushError(entry) {
  if (errors.length >= MAX_ERRORS) errors.shift()
  errors.push(entry)
  sendToBackend(entry)
}

function buildEntry(source, error, extra = {}) {
  return {
    id: crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    source,
    message: error?.message || String(error),
    stack: error?.stack || null,
    route: getCurrentRoute(),
    browser: getBrowserInfo(),
    timestamp: new Date().toISOString(),
    ...extra,
  }
}

function getComponentTree(instance) {
  const tree = []
  let current = instance
  while (current) {
    const name = current.type?.__name || current.type?.name || 'Anonymous'
    tree.push(name)
    current = current.parent
  }
  return tree
}

async function sendToBackend(entry) {
  try {
    await client.post('/errors', entry)
  } catch {
    // Backend may be unavailable — error is still kept in memory
  }
}

function captureWindowError(message, source, lineno, colno, error) {
  pushError(
    buildEntry('window.onerror', error || { message }, {
      file: source,
      line: lineno,
      column: colno,
    }),
  )
}

function captureUnhandledRejection(event) {
  const reason = event.reason
  pushError(buildEntry('unhandledrejection', reason))
}

function captureVueError(error, instance, info) {
  pushError(
    buildEntry('vue', error, {
      componentTree: instance ? getComponentTree(instance) : [],
      lifecycleHook: info || null,
    }),
  )
}

function captureApiError(error, context = {}) {
  pushError(
    buildEntry('api', error, {
      status: error?.status || null,
      endpoint: context.endpoint || null,
      method: context.method || null,
    }),
  )
}

function install(app, { router } = {}) {
  _router = router
  app.config.errorHandler = captureVueError
  window.addEventListener('error', (event) => {
    captureWindowError(event.message, event.filename, event.lineno, event.colno, event.error)
  })
  window.addEventListener('unhandledrejection', captureUnhandledRejection)
}

function getErrors() {
  return [...errors]
}

function clear() {
  errors.length = 0
}

export default {
  install,
  captureApiError,
  getErrors,
  clear,
}
