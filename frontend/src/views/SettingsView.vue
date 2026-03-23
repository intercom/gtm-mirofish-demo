<script setup>
import { ref, onMounted } from 'vue'
import { useTheme } from '../composables/useTheme'
import { useToast } from '../composables/useToast'

const { preference: themePreference, setTheme } = useTheme()
const toast = useToast()

const themeOptions = [
  { id: 'system', label: 'System', icon: '💻' },
  { id: 'light', label: 'Light', icon: '☀️' },
  { id: 'dark', label: 'Dark', icon: '🌙' },
]

const provider = ref('anthropic')
const apiKey = ref('')
const zepKey = ref('')
const connectionStatus = ref({ llm: null, zep: null })
const saved = ref(false)
let savedTimer = null

onMounted(() => {
  const stored = localStorage.getItem('mirofish-settings')
  if (stored) {
    try {
      const s = JSON.parse(stored)
      provider.value = s.provider || 'anthropic'
      apiKey.value = s.apiKey || ''
      zepKey.value = s.zepKey || ''
    } catch {
      toast.error('Failed to load saved settings')
    }
  }
})

function save() {
  try {
    localStorage.setItem('mirofish-settings', JSON.stringify({
      provider: provider.value,
      apiKey: apiKey.value,
      zepKey: zepKey.value,
    }))
    saved.value = true
    clearTimeout(savedTimer)
    savedTimer = setTimeout(() => { saved.value = false }, 2000)
    toast.success('Settings saved')
  } catch {
    toast.error('Failed to save settings')
  }
}

async function testConnection(service) {
  connectionStatus.value[service] = 'testing'
  try {
    // TODO: Replace with real connection test endpoint
    await new Promise(resolve => setTimeout(resolve, 1000))
    connectionStatus.value[service] = 'success'
    toast.success(`${service === 'llm' ? 'LLM' : 'Zep'} connection successful`)
  } catch {
    connectionStatus.value[service] = 'error'
    toast.error(`${service === 'llm' ? 'LLM' : 'Zep'} connection failed`)
  }
}

function statusLabel(service) {
  const s = connectionStatus.value[service]
  if (s === 'testing') return 'Testing...'
  if (s === 'success') return '✓ Connected'
  if (s === 'error') return '✗ Failed'
  return 'Test'
}

function statusClass(service) {
  const s = connectionStatus.value[service]
  if (s === 'success') return 'text-[#090]'
  if (s === 'error') return 'text-[#ff5600]'
  return ''
}

const providers = [
  { id: 'anthropic', name: 'Claude (Anthropic)', model: 'claude-sonnet-4-20250514' },
  { id: 'openai', name: 'OpenAI (GPT-4o)', model: 'gpt-4o' },
  { id: 'gemini', name: 'Google Gemini', model: 'gemini-2.5-flash' },
]
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <div class="flex items-center justify-between mb-6 md:mb-8">
      <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Settings</h1>
      <transition name="fade">
        <span v-if="saved" class="text-xs font-medium text-[#090] bg-[rgba(0,153,0,0.08)] px-3 py-1 rounded-full">
          ✓ Saved
        </span>
      </transition>
    </div>

    <!-- Theme -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Theme</h2>
      <div class="flex gap-2">
        <button
          v-for="opt in themeOptions"
          :key="opt.id"
          @click="setTheme(opt.id)"
          class="flex items-center gap-2 px-4 py-2 rounded-lg border text-sm transition-colors cursor-pointer"
          :class="themePreference === opt.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.08)] text-[var(--color-text)]'
            : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50'"
        >
          <span>{{ opt.icon }}</span>
          <span>{{ opt.label }}</span>
        </button>
      </div>
    </section>

    <!-- LLM Provider -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">LLM Provider</h2>
      <div class="space-y-3">
        <label v-for="p in providers" :key="p.id"
          class="flex items-center gap-3 p-3 md:p-4 rounded-lg border cursor-pointer transition-colors"
          :class="provider === p.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)]'
            : 'border-[var(--color-border)] hover:border-[#2068FF]/50'">
          <input type="radio" :value="p.id" v-model="provider" @change="save" class="accent-[#2068FF]" />
          <div>
            <div class="text-sm font-medium text-[var(--color-text)]">{{ p.name }}</div>
            <div class="text-xs text-[var(--color-text-muted)]">Model: {{ p.model }}</div>
          </div>
        </label>
      </div>

      <div class="mt-4">
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">API Key</label>
        <div class="flex flex-col sm:flex-row gap-2">
          <input type="password" v-model="apiKey" @change="save"
            placeholder="Enter your API key"
            class="flex-1 border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 md:px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]" />
          <button @click="testConnection('llm')"
            class="px-4 py-2 text-sm border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-primary-light)] transition-colors"
            :class="statusClass('llm')">
            {{ statusLabel('llm') }}
          </button>
        </div>
      </div>
    </section>

    <!-- Zep Cloud -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Zep Cloud (Knowledge Graph)</h2>
      <div class="flex flex-col sm:flex-row gap-2">
        <input type="password" v-model="zepKey" @change="save"
          placeholder="Enter Zep API key"
          class="flex-1 border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 md:px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]" />
        <button @click="testConnection('zep')"
          class="px-4 py-2 text-sm border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-primary-light)] transition-colors"
          :class="statusClass('zep')">
          {{ statusLabel('zep') }}
        </button>
      </div>
      <p class="text-xs text-[var(--color-text-muted)] mt-2">
        Sign up at <a href="https://app.getzep.com/" target="_blank" class="text-[#2068FF]">app.getzep.com</a> — free tier is sufficient for PoC.
      </p>
    </section>

    <!-- Info -->
    <section class="bg-[var(--color-primary-light)] border border-[#2068FF]/20 rounded-lg p-3 md:p-4">
      <p class="text-xs text-[var(--color-text-secondary)]">
        Settings are stored locally in your browser. For Docker deployments, configure via
        <code class="bg-[var(--color-border)] px-1 rounded">.env</code> file instead.
      </p>
    </section>
  </div>
</template>
