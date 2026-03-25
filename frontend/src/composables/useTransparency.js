import { ref, computed } from 'vue'

const STORAGE_KEY = 'mirofish-transparency'

// Module-level state shared across all component instances
const showThinking = ref(false)
const transparentAgentIds = ref(new Set())
let initialized = false

export function useTransparency() {
  if (!initialized) {
    initialized = true
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        showThinking.value = !!parsed.showThinking
        if (Array.isArray(parsed.agentIds)) {
          transparentAgentIds.value = new Set(parsed.agentIds)
        }
      }
    } catch {
      // Corrupted storage — use defaults
    }
  }

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        showThinking: showThinking.value,
        agentIds: [...transparentAgentIds.value],
      }))
    } catch {
      // Storage full — silently ignore
    }
  }

  function toggleThinking() {
    showThinking.value = !showThinking.value
    if (!showThinking.value) {
      transparentAgentIds.value = new Set()
    }
    persist()
  }

  function toggleAgent(agentId) {
    const ids = transparentAgentIds.value
    if (ids.has(agentId)) {
      ids.delete(agentId)
    } else {
      ids.add(agentId)
    }
    transparentAgentIds.value = new Set(ids)
    persist()
  }

  function isAgentTransparent(agentId) {
    if (!showThinking.value) return false
    if (transparentAgentIds.value.size === 0) return true
    return transparentAgentIds.value.has(agentId)
  }

  const hasAgentFilter = computed(() => transparentAgentIds.value.size > 0)

  function clearAgentFilter() {
    transparentAgentIds.value = new Set()
    persist()
  }

  return {
    showThinking,
    transparentAgentIds,
    hasAgentFilter,
    toggleThinking,
    toggleAgent,
    isAgentTransparent,
    clearAgentFilter,
  }
}
