import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const STORAGE_KEY = 'mirofish-settings'

const PROVIDERS = [
  { id: 'anthropic', name: 'Claude (Anthropic)', model: 'claude-sonnet-4-20250514' },
  { id: 'openai', name: 'OpenAI (GPT-4o)', model: 'gpt-4o' },
  { id: 'gemini', name: 'Google Gemini', model: 'gemini-2.5-flash' },
]

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const saved = loadFromStorage()

  const provider = ref(saved.provider || 'anthropic')
  const apiKey = ref(saved.apiKey || '')
  const zepKey = ref(saved.zepKey || '')
  const connectionStatus = ref({ llm: null, zep: null })

  const providers = PROVIDERS

  const currentProvider = computed(() =>
    PROVIDERS.find((p) => p.id === provider.value),
  )

  function persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        provider: provider.value,
        apiKey: apiKey.value,
        zepKey: zepKey.value,
      }),
    )
  }

  function setProvider(id) {
    provider.value = id
    persist()
  }

  function setApiKey(key) {
    apiKey.value = key
    persist()
  }

  function setZepKey(key) {
    zepKey.value = key
    persist()
  }

  function setConnectionStatus(service, status) {
    connectionStatus.value[service] = status
  }

  return {
    provider,
    apiKey,
    zepKey,
    connectionStatus,
    providers,
    currentProvider,
    setProvider,
    setApiKey,
    setZepKey,
    setConnectionStatus,
  }
})
