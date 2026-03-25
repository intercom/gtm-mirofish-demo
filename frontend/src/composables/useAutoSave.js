import { ref, watch, onUnmounted } from 'vue'

const STORAGE_PREFIX = 'mirofish-draft-'

/**
 * Auto-saves reactive state to localStorage with debouncing.
 *
 * @param {string} key - Unique identifier for this editor draft
 * @param {() => object} serialize - Returns the current state as a plain object
 * @param {(data: object) => void} restore - Applies saved state back to refs
 * @param {import('vue').WatchSource[]} sources - Reactive sources to watch
 * @param {object} [options]
 * @param {number} [options.debounce=500] - Debounce delay in ms
 */
export function useAutoSave(key, serialize, restore, sources, options = {}) {
  const debounceMs = options.debounce ?? 500
  const storageKey = STORAGE_PREFIX + key

  const saveStatus = ref('idle') // 'idle' | 'saving' | 'saved'
  const hasDraft = ref(false)

  let debounceTimer = null
  let statusTimer = null

  function save() {
    saveStatus.value = 'saving'
    try {
      const data = serialize()
      data._savedAt = Date.now()
      localStorage.setItem(storageKey, JSON.stringify(data))
      saveStatus.value = 'saved'
      hasDraft.value = true
      clearTimeout(statusTimer)
      statusTimer = setTimeout(() => { saveStatus.value = 'idle' }, 2000)
    } catch {
      saveStatus.value = 'idle'
    }
  }

  function debouncedSave() {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(save, debounceMs)
  }

  function load() {
    try {
      const raw = localStorage.getItem(storageKey)
      if (!raw) return false
      const data = JSON.parse(raw)
      restore(data)
      hasDraft.value = true
      return true
    } catch {
      return false
    }
  }

  function clear() {
    localStorage.removeItem(storageKey)
    hasDraft.value = false
    clearTimeout(debounceTimer)
  }

  const stopWatch = watch(sources, debouncedSave, { deep: true })

  onUnmounted(() => {
    clearTimeout(debounceTimer)
    clearTimeout(statusTimer)
    stopWatch()
  })

  return { saveStatus, hasDraft, load, clear }
}
