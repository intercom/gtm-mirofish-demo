import { ref, computed } from 'vue'
import { API_BASE } from '../api/client'

const DB_NAME = 'mirofish-sync-queue'
const DB_VERSION = 1
const STORE_NAME = 'queue'
const MAX_QUEUE_SIZE = 100
const WARN_THRESHOLD = 80
const MAX_RETRIES = 3

// ── Reactive state (consumed by OfflineBanner and other UI) ──

const queueSize = ref(0)
const isSyncing = ref(false)
const syncProgress = ref({ current: 0, total: 0 })
const lastSyncError = ref(null)

const syncMessage = computed(() => {
  if (!isSyncing.value) return ''
  const { current, total } = syncProgress.value
  return `Syncing ${total - current} queued change${total - current !== 1 ? 's' : ''}...`
})

const isNearLimit = computed(() => queueSize.value >= WARN_THRESHOLD)

// ── IndexedDB helpers ──

let dbPromise = null

function openDB() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = (event) => {
      const db = event.target.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
  return dbPromise
}

function withStore(mode, fn) {
  return openDB().then((db) => {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, mode)
      const store = tx.objectStore(STORE_NAME)
      const result = fn(store)
      tx.oncomplete = () => resolve(result?.result ?? result)
      tx.onerror = () => reject(tx.error)
    })
  })
}

// ── Queue operations ──

async function refreshSize() {
  const db = await openDB()
  return new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const req = tx.objectStore(STORE_NAME).count()
    req.onsuccess = () => {
      queueSize.value = req.result
      resolve(req.result)
    }
    req.onerror = () => resolve(0)
  })
}

async function getAll() {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const req = tx.objectStore(STORE_NAME).getAll()
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

async function remove(id) {
  await withStore('readwrite', (store) => store.delete(id))
  await refreshSize()
}

async function clear() {
  await withStore('readwrite', (store) => store.clear())
  queueSize.value = 0
}

/**
 * Add a failed/offline request to the sync queue.
 * Returns false if queue is full.
 */
async function enqueue({ endpoint, method, body }) {
  if (queueSize.value >= MAX_QUEUE_SIZE) {
    return { queued: false, reason: 'Queue is full (100 items). Clear or sync before adding more.' }
  }

  const entry = {
    endpoint,
    method: method.toUpperCase(),
    body: body ?? null,
    timestamp: Date.now(),
    retries: 0,
  }

  await withStore('readwrite', (store) => store.add(entry))
  await refreshSize()

  return { queued: true, size: queueSize.value, nearLimit: isNearLimit.value }
}

/**
 * Replay a single queued request against the API.
 * Returns { ok, conflict } to guide conflict resolution.
 */
async function replay(entry) {
  const url = `${API_BASE}${entry.endpoint}`
  const options = {
    method: entry.method,
    headers: { 'Content-Type': 'application/json' },
  }
  if (entry.body && entry.method !== 'GET') {
    options.body = JSON.stringify(entry.body)
  }

  const res = await fetch(url, options)

  if (res.ok) return { ok: true, conflict: false }
  if (res.status === 409) return { ok: false, conflict: true }
  throw new Error(`${res.status} ${res.statusText}`)
}

/**
 * Process the entire queue in order. Called when connectivity is restored.
 * Conflict resolution: server wins — user is notified via the returned results.
 */
async function processQueue() {
  if (isSyncing.value) return { synced: 0, conflicts: [], errors: [] }

  const items = await getAll()
  if (items.length === 0) return { synced: 0, conflicts: [], errors: [] }

  isSyncing.value = true
  lastSyncError.value = null
  syncProgress.value = { current: 0, total: items.length }

  const results = { synced: 0, conflicts: [], errors: [] }

  for (const item of items) {
    syncProgress.value.current++
    try {
      const { ok, conflict } = await replay(item)
      if (ok) {
        results.synced++
        await remove(item.id)
      } else if (conflict) {
        results.conflicts.push({
          endpoint: item.endpoint,
          method: item.method,
          timestamp: item.timestamp,
        })
        await remove(item.id)
      }
    } catch (err) {
      item.retries = (item.retries || 0) + 1
      if (item.retries >= MAX_RETRIES) {
        results.errors.push({
          endpoint: item.endpoint,
          method: item.method,
          error: err.message,
        })
        await remove(item.id)
      } else {
        await withStore('readwrite', (store) => store.put(item))
      }
    }
  }

  isSyncing.value = false
  syncProgress.value = { current: 0, total: 0 }
  await refreshSize()
  return results
}

// ── Online/offline auto-sync ──

let listenersBound = false

function bindListeners() {
  if (listenersBound || typeof window === 'undefined') return
  listenersBound = true

  window.addEventListener('online', async () => {
    const results = await processQueue()
    if (results.conflicts.length > 0) {
      console.warn(
        `[SyncQueue] ${results.conflicts.length} conflict(s) resolved (server wins):`,
        results.conflicts,
      )
    }
  })
}

/**
 * Initialize the sync queue — call once at app startup.
 * Loads the current queue size and binds online/offline listeners.
 */
async function init() {
  await refreshSize()
  bindListeners()

  if (navigator.onLine && queueSize.value > 0) {
    await processQueue()
  }
}

export const syncQueue = {
  // State (reactive, read-only for consumers)
  queueSize,
  isSyncing,
  syncProgress,
  syncMessage,
  lastSyncError,
  isNearLimit,

  // Actions
  init,
  enqueue,
  processQueue,
  clear,
  getAll,
  remove,

  // Constants (exposed for UI warnings)
  MAX_QUEUE_SIZE,
  WARN_THRESHOLD,
}
