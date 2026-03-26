import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { API_BASE } from '../api/client'

const STORAGE_KEY = 'mirofish-settings'

const PROVIDERS = [
  { id: 'anthropic', name: 'Claude (Anthropic)', model: 'claude-sonnet-4-20250514' },
  { id: 'openai', name: 'OpenAI (GPT-4o)', model: 'gpt-4o' },
  { id: 'gemini', name: 'Google Gemini', model: 'gemini-2.5-flash' },
]

export const useSettingsStore = defineStore('settings', () => {
  const provider = ref('anthropic')
  const apiKey = ref('')
  const zepKey = ref('')
  const statusBarEnabled = ref(false)
  const showPresence = ref(true)
  const connectionStatus = ref({ llm: null, zep: null })

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const s = JSON.parse(saved)
        provider.value = s.provider || 'anthropic'
        apiKey.value = s.apiKey || ''
        zepKey.value = s.zepKey || ''
        statusBarEnabled.value = !!s.statusBarEnabled
        showPresence.value = s.showPresence !== false
      }
    } catch {
      // Corrupted data — reset to defaults
    }
  }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      provider: provider.value,
      apiKey: apiKey.value,
      zepKey: zepKey.value,
      statusBarEnabled: statusBarEnabled.value,
      showPresence: showPresence.value,
    }))
  }

  // Auto-persist on changes
  watch([provider, apiKey, zepKey, statusBarEnabled, showPresence], save, { flush: 'post' })

  async function testConnection(service) {
    if (!navigator.onLine) {
      connectionStatus.value[service] = 'offline'
      return
    }
    connectionStatus.value[service] = 'testing'
    try {
      const res = await fetch(`${API_BASE}/health`)
      connectionStatus.value[service] = res.ok ? 'success' : 'error'
    } catch {
      connectionStatus.value[service] = navigator.onLine ? 'error' : 'offline'
    }
  }

  // Load on creation
  load()

  return {
    provider,
    apiKey,
    zepKey,
    statusBarEnabled,
    showPresence,
    connectionStatus,
    providers: PROVIDERS,
    load,
    save,
    testConnection,
  }
})
