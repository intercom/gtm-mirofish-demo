import { ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { useServiceStatus } from '../composables/useServiceStatus'

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
  const connectionStatus = ref({ llm: null, zep: null })

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const s = JSON.parse(saved)
        provider.value = s.provider || 'anthropic'
        apiKey.value = s.apiKey || ''
        zepKey.value = s.zepKey || ''
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
    }))
  }

  // Auto-persist on changes
  watch([provider, apiKey, zepKey], save, { flush: 'post' })

  async function testConnection(service) {
    connectionStatus.value[service] = 'testing'
    try {
      const { services, check } = useServiceStatus()
      await check()
      const result = services.value[service]
      connectionStatus.value[service] = result?.status === 'ok' ? 'success' : 'error'
    } catch {
      connectionStatus.value[service] = 'error'
    }
  }

  // Load on creation
  load()

  return {
    provider,
    apiKey,
    zepKey,
    connectionStatus,
    providers: PROVIDERS,
    load,
    save,
    testConnection,
  }
})
