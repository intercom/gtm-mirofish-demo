import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish_timeline_annotations'

function loadStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return typeof parsed === 'object' && parsed !== null ? parsed : {}
  } catch {
    return {}
  }
}

function persist(data) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // Storage full or unavailable
  }
}

let nextId = Date.now()

export const useAnnotationsStore = defineStore('annotations', () => {
  // Map of taskId -> annotation[]
  const annotationsByTask = ref(loadStored())

  function getAnnotations(taskId) {
    return annotationsByTask.value[taskId] || []
  }

  function addAnnotation(taskId, { round, text, color }) {
    if (!annotationsByTask.value[taskId]) {
      annotationsByTask.value[taskId] = []
    }
    const annotation = {
      id: String(nextId++),
      round,
      text: text || '',
      color: color || 'var(--color-primary)',
      createdAt: Date.now(),
    }
    annotationsByTask.value[taskId].push(annotation)
    persist(annotationsByTask.value)
    return annotation
  }

  function updateAnnotation(taskId, annotationId, updates) {
    const list = annotationsByTask.value[taskId]
    if (!list) return
    const item = list.find(a => a.id === annotationId)
    if (!item) return
    if (updates.text !== undefined) item.text = updates.text
    if (updates.color !== undefined) item.color = updates.color
    persist(annotationsByTask.value)
  }

  function removeAnnotation(taskId, annotationId) {
    const list = annotationsByTask.value[taskId]
    if (!list) return
    const idx = list.findIndex(a => a.id === annotationId)
    if (idx !== -1) {
      list.splice(idx, 1)
      persist(annotationsByTask.value)
    }
  }

  function exportAnnotations(taskId) {
    return JSON.parse(JSON.stringify(getAnnotations(taskId)))
  }

  function importAnnotations(taskId, annotations) {
    if (!Array.isArray(annotations)) return
    if (!annotationsByTask.value[taskId]) {
      annotationsByTask.value[taskId] = []
    }
    for (const a of annotations) {
      annotationsByTask.value[taskId].push({
        id: String(nextId++),
        round: a.round,
        text: a.text || '',
        color: a.color || 'var(--color-primary)',
        createdAt: a.createdAt || Date.now(),
      })
    }
    persist(annotationsByTask.value)
  }

  function clearAnnotations(taskId) {
    delete annotationsByTask.value[taskId]
    persist(annotationsByTask.value)
  }

  return {
    annotationsByTask,
    getAnnotations,
    addAnnotation,
    updateAnnotation,
    removeAnnotation,
    exportAnnotations,
    importAnnotations,
    clearAnnotations,
  }
})
