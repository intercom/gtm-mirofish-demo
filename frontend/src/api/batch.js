/**
 * API request batching — collects multiple requests within a short time
 * window and sends them as a single HTTP call to /api/batch.
 *
 * Usage:
 *   import { batchGet, batchPost } from '@/api/batch'
 *   const res = await batchGet('/simulation/123/run-status')
 *   // res looks like { data: {...}, status: 200 }
 */

import client from './client'

const BATCH_DELAY_MS = 50
const MAX_BATCH_SIZE = 20

let queue = []
let flushTimer = null

function createDeferred() {
  let resolve, reject
  const promise = new Promise((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

function dedupeKey(method, path, body) {
  return `${method}:${path}:${body ? JSON.stringify(body) : ''}`
}

function scheduleFlush() {
  if (flushTimer) return
  flushTimer = setTimeout(flush, BATCH_DELAY_MS)
}

async function flush() {
  flushTimer = null
  if (queue.length === 0) return

  const batch = queue.splice(0, MAX_BATCH_SIZE)

  // Deduplicate: group identical requests so only one is sent
  const deduped = []
  const dupeMap = new Map() // dedupeKey → [deferred, ...]

  for (const item of batch) {
    const key = dedupeKey(item.method, item.path, item.body)
    if (dupeMap.has(key)) {
      dupeMap.get(key).push(item.deferred)
    } else {
      dupeMap.set(key, [item.deferred])
      deduped.push(item)
    }
  }

  try {
    const res = await client.post('/batch', {
      requests: deduped.map((item, i) => ({
        id: String(i),
        method: item.method,
        path: `/api/v1${item.path}`,
        body: item.body,
      })),
    })

    const responses = res.data?.responses || []
    for (const resp of responses) {
      const idx = parseInt(resp.id, 10)
      const item = deduped[idx]
      if (!item) continue

      const key = dedupeKey(item.method, item.path, item.body)
      const deferreds = dupeMap.get(key) || [item.deferred]
      const fakeResponse = { data: resp.body, status: resp.status }

      if (resp.status >= 400) {
        const err = {
          message: resp.body?.error || resp.body?.message || 'Request failed',
          status: resp.status,
          data: resp.body,
        }
        deferreds.forEach((d) => d.reject(err))
      } else {
        deferreds.forEach((d) => d.resolve(fakeResponse))
      }
    }
  } catch (err) {
    for (const item of batch) {
      item.deferred.reject(err)
    }
  }

  // If more items were queued during flush, schedule another round
  if (queue.length > 0) scheduleFlush()
}

function enqueue(method, path, body = null) {
  const deferred = createDeferred()
  queue.push({ method, path, body, deferred })

  if (queue.length >= MAX_BATCH_SIZE) {
    clearTimeout(flushTimer)
    flushTimer = null
    flush()
  } else {
    scheduleFlush()
  }

  return deferred.promise
}

/** Queue a GET request for batching. Returns a promise shaped like an axios response. */
export function batchGet(path) {
  return enqueue('GET', path)
}

/** Queue a POST request for batching. */
export function batchPost(path, body) {
  return enqueue('POST', path, body)
}

/** Force-flush the queue immediately (useful in tests or before unmount). */
export function flushBatchQueue() {
  clearTimeout(flushTimer)
  flushTimer = null
  return flush()
}
