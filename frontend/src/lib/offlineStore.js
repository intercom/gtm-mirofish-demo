import { openDB } from 'idb'

const DB_NAME = 'mirofish-offline'
const DB_VERSION = 1
const MAX_BYTES = 50 * 1024 * 1024 // 50MB

const STORE_NAMES = ['simulations', 'dashboards', 'reports', 'settings', 'recentData']

let dbPromise = null

function getDB() {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        for (const name of STORE_NAMES) {
          if (!db.objectStoreNames.contains(name)) {
            const store = db.createObjectStore(name)
            store.createIndex('updatedAt', '_updatedAt')
          }
        }
      },
    })
  }
  return dbPromise
}

function assertStore(storeName) {
  if (!STORE_NAMES.includes(storeName)) {
    throw new Error(`Unknown store: ${storeName}. Valid: ${STORE_NAMES.join(', ')}`)
  }
}

function stamp(data) {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    return { ...data, _updatedAt: Date.now() }
  }
  return { _value: data, _updatedAt: Date.now() }
}

function unstamp(record) {
  if (!record) return record
  if ('_value' in record) {
    return record._value
  }
  const { _updatedAt, ...rest } = record
  return rest
}

export async function get(storeName, key) {
  assertStore(storeName)
  const db = await getDB()
  const record = await db.get(storeName, key)
  return unstamp(record)
}

export async function getAll(storeName) {
  assertStore(storeName)
  const db = await getDB()
  const records = await db.getAll(storeName)
  return records.map(unstamp)
}

export async function getAllKeys(storeName) {
  assertStore(storeName)
  const db = await getDB()
  return db.getAllKeys(storeName)
}

export async function put(storeName, key, data) {
  assertStore(storeName)
  await evictIfNeeded()
  const db = await getDB()
  await db.put(storeName, stamp(data), key)
}

export async function del(storeName, key) {
  assertStore(storeName)
  const db = await getDB()
  await db.delete(storeName, key)
}

export async function clear(storeName) {
  assertStore(storeName)
  const db = await getDB()
  await db.clear(storeName)
}

async function estimateUsage() {
  if (navigator.storage?.estimate) {
    const { usage } = await navigator.storage.estimate()
    return usage || 0
  }
  return 0
}

async function evictIfNeeded() {
  const usage = await estimateUsage()
  if (usage < MAX_BYTES) return

  const db = await getDB()
  const candidates = []

  for (const storeName of STORE_NAMES) {
    if (storeName === 'settings') continue
    const tx = db.transaction(storeName, 'readonly')
    let cursor = await tx.store.index('updatedAt').openCursor()
    while (cursor) {
      candidates.push({ storeName, key: cursor.primaryKey, updatedAt: cursor.value._updatedAt || 0 })
      cursor = await cursor.continue()
    }
  }

  candidates.sort((a, b) => a.updatedAt - b.updatedAt)

  for (const item of candidates) {
    const currentUsage = await estimateUsage()
    if (currentUsage < MAX_BYTES * 0.8) break
    await db.delete(item.storeName, item.key)
  }
}

/**
 * Fetch from an async source, auto-cache to IndexedDB, and fall back
 * to cached data when the fetch fails (e.g. offline).
 *
 * @param {string} storeName - IndexedDB object store
 * @param {string} key - Cache key
 * @param {() => Promise<*>} fetchFn - Async function that returns fresh data
 * @returns {{ data: *, fromCache: boolean }}
 */
export async function cachedFetch(storeName, key, fetchFn) {
  try {
    const data = await fetchFn()
    await put(storeName, key, data).catch(() => {})
    return { data, fromCache: false }
  } catch {
    const cached = await get(storeName, key).catch(() => null)
    if (cached != null) {
      return { data: cached, fromCache: true }
    }
    throw new Error(`Offline and no cached data for ${storeName}/${key}`)
  }
}

export const offlineStore = { get, getAll, getAllKeys, put, delete: del, clear, cachedFetch }
export default offlineStore
