const DB_NAME = 'mirofish-reports'
const DB_VERSION = 1
const STORE_NAME = 'reports'

let dbPromise = null

function openDB() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'taskId' })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
  return dbPromise
}

function tx(mode) {
  return openDB().then(db => db.transaction(STORE_NAME, mode).objectStore(STORE_NAME))
}

function idbRequest(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
}

export async function cacheReport(taskId, { reportId, sections, isComplete }) {
  const store = await tx('readwrite')
  await idbRequest(store.put({
    taskId,
    reportId,
    sections,
    isComplete,
    cachedAt: Date.now(),
  }))
}

export async function getCachedReport(taskId) {
  const store = await tx('readonly')
  return idbRequest(store.get(taskId))
}

export async function getAllCachedTaskIds() {
  const store = await tx('readonly')
  return idbRequest(store.getAllKeys())
}

export async function deleteCachedReport(taskId) {
  const store = await tx('readwrite')
  await idbRequest(store.delete(taskId))
}
