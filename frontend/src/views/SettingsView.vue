<script setup>
import { ref, watch, onMounted } from 'vue'
import { useToast } from '../composables/useToast'
import { useDemoMode } from '../composables/useDemoMode'
import { useSettingsStore } from '../stores/settings'
import { API_BASE } from '../api/client'
import ThemeEditor from '../components/settings/ThemeEditor.vue'
import ServiceStatus from '../components/common/ServiceStatus.vue'
import ThemeSwitcher from '../components/common/ThemeSwitcher.vue'

const settingsStore = useSettingsStore()


const toast = useToast()
const { isDemoMode } = useDemoMode()

const STORAGE_KEY = 'mirofish-settings'

const provider = ref('anthropic')
const apiKey = ref('')
const zepKey = ref('')
const agentCount = ref(200)
const duration = ref(72)
const platformMode = ref('parallel')
const showPresence = ref(true)
const connectionStatus = ref({ llm: null, zep: null })
const connectionError = ref({ llm: '', zep: '' })

const saved = ref(false)
let savedTimer = null

const providers = [
  { id: 'anthropic', name: 'Claude (Anthropic)', model: 'claude-sonnet-4-20250514' },
  { id: 'openai', name: 'OpenAI (GPT-4o)', model: 'gpt-4o' },
  { id: 'gemini', name: 'Google Gemini', model: 'gemini-2.5-flash' },
]

const durations = [
  { value: 24, label: '24 hours' },
  { value: 48, label: '48 hours' },
  { value: 72, label: '72 hours (recommended)' },
]

const platforms = [
  { id: 'twitter', label: 'Twitter' },
  { id: 'reddit', label: 'Reddit' },
  { id: 'parallel', label: 'Both' },
]

function load() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (!stored) return
  try {
    const s = JSON.parse(stored)
    provider.value = s.provider || 'anthropic'
    apiKey.value = s.apiKey || ''
    zepKey.value = s.zepKey || ''
    agentCount.value = s.agentCount ?? 200
    duration.value = s.duration ?? 72
    platformMode.value = s.platformMode || 'parallel'
    showPresence.value = s.showPresence !== false
  } catch {
    toast.error('Failed to load saved settings')
  }
}

function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      provider: provider.value,
      apiKey: apiKey.value,
      zepKey: zepKey.value,
      agentCount: agentCount.value,
      duration: duration.value,
      platformMode: platformMode.value,
      showPresence: showPresence.value,
    }))
    saved.value = true
    clearTimeout(savedTimer)
    savedTimer = setTimeout(() => { saved.value = false }, 2000)
  } catch {
    toast.error('Failed to save settings')
  }
}

watch([provider, apiKey, zepKey, agentCount, duration, platformMode, showPresence], save, { deep: true })

watch(showPresence, (val) => {
  settingsStore.showPresence = val
})

async function testConnection(service) {
  connectionStatus.value[service] = 'testing'
  connectionError.value[service] = ''

  const endpoint = service === 'llm' ? `${API_BASE}/settings/test-llm` : `${API_BASE}/settings/test-zep`
  const body = service === 'llm'
    ? { provider: provider.value, apiKey: apiKey.value }
    : { apiKey: zepKey.value }

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()
    if (data.ok) {
      connectionStatus.value[service] = 'success'
      toast.success(`${service === 'llm' ? 'LLM' : 'Zep'} connection successful`)
    } else {
      connectionStatus.value[service] = 'error'
      connectionError.value[service] = data.error || 'Connection failed'
      toast.error(`${service === 'llm' ? 'LLM' : 'Zep'} connection failed`)
    }
  } catch {
    connectionStatus.value[service] = 'error'
    connectionError.value[service] = 'Network error — is the backend running?'
    toast.error(`${service === 'llm' ? 'LLM' : 'Zep'} connection failed`)
  }
}


function testButtonLabel(service) {
  const status = connectionStatus.value[service]
  if (status === 'testing') return 'Testing…'
  if (status === 'success') return '✓ Connected'
  if (status === 'error') return '✗ Failed'
  return 'Test Connection'
}

function testButtonClass(service) {
  const status = connectionStatus.value[service]
  if (status === 'success') return 'border-[var(--color-success)] text-[var(--color-success)]'
  if (status === 'error') return 'border-[var(--color-fin-orange)] text-[var(--color-fin-orange)]'
  return 'border-[var(--color-border)] hover:bg-[var(--color-primary-light)]'
}

onMounted(() => {
  load()
})
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

    <!-- Demo Mode Banner -->
    <section v-if="isDemoMode" class="mb-8 md:mb-10 bg-[rgba(32,104,255,0.06)] border border-[#2068FF]/20 rounded-lg p-3 md:p-4 flex items-start gap-3">
      <svg class="w-5 h-5 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-sm text-[var(--color-text-secondary)]">
        <span class="font-semibold text-[var(--color-text)]">Demo Mode</span> — Using simulated data. API keys are not required.
      </p>
    </section>

    <!-- Service Status -->
    <section class="mb-8 md:mb-10">
      <ServiceStatus mode="expanded" />
    </section>

    <!-- Theme -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Theme</h2>
      <ThemeSwitcher />
    </section>

    <!-- Custom Theme Editor -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Custom Themes</h2>
      <ThemeEditor />
    </section>

    <!-- LLM Provider -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">LLM Provider</h2>
      <div class="space-y-3">
        <label
          v-for="p in providers"
          :key="p.id"
          class="flex items-center gap-3 p-3 md:p-4 rounded-lg border cursor-pointer transition-colors"
          :class="provider === p.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)]'
            : 'border-[var(--color-border)] hover:border-[#2068FF]/50'"
        >
          <input type="radio" :value="p.id" v-model="provider" class="accent-[#2068FF]" />
          <div>
            <div class="text-sm font-medium text-[var(--color-text)]">{{ p.name }}</div>
            <div class="text-xs text-[var(--color-text-muted)]">Model: {{ p.model }}</div>
          </div>
        </label>
      </div>

      <div class="mt-4">
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">API Key</label>
        <div class="flex flex-col sm:flex-row gap-2">
          <input
            type="password"
            v-model="apiKey"
            :placeholder="isDemoMode ? 'Not required in demo mode' : 'Enter your API key'"
            :disabled="isDemoMode"
            class="flex-1 border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 md:px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]"
            :class="{ 'opacity-40 cursor-not-allowed': isDemoMode }"
          />
          <span
            v-if="isDemoMode"
            class="px-4 py-2 text-sm font-medium text-[#090] bg-[rgba(0,153,0,0.08)] border border-[rgba(0,153,0,0.2)] rounded-lg whitespace-nowrap text-center"
          >Simulated</span>
          <button
            v-else
            @click="testConnection('llm')"
            :disabled="!apiKey || connectionStatus.llm === 'testing'"
            class="px-4 py-2 text-sm border rounded-lg transition-colors whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed"
            :class="testButtonClass('llm')"
          >
            {{ testButtonLabel('llm') }}
          </button>
        </div>
        <p v-if="connectionError.llm" class="text-xs text-red-500 mt-1">{{ connectionError.llm }}</p>
      </div>
    </section>

    <!-- Zep Cloud -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Zep Cloud (Knowledge Graph)</h2>
      <div class="flex flex-col sm:flex-row gap-2">
        <input
          type="password"
          v-model="zepKey"
          :placeholder="isDemoMode ? 'Not required in demo mode' : 'Enter Zep API key'"
          :disabled="isDemoMode"
          class="flex-1 border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 md:px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]"
          :class="{ 'opacity-40 cursor-not-allowed': isDemoMode }"
        />
        <span
          v-if="isDemoMode"
          class="px-4 py-2 text-sm font-medium text-[#090] bg-[rgba(0,153,0,0.08)] border border-[rgba(0,153,0,0.2)] rounded-lg whitespace-nowrap text-center"
        >Simulated</span>
        <button
          v-else
          @click="testConnection('zep')"
          :disabled="!zepKey || connectionStatus.zep === 'testing'"
          class="px-4 py-2 text-sm border rounded-lg transition-colors whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed"
          :class="testButtonClass('zep')"
        >
          {{ testButtonLabel('zep') }}
        </button>
      </div>
      <p v-if="connectionError.zep" class="text-xs text-red-500 mt-1">{{ connectionError.zep }}</p>
      <p v-else-if="!isDemoMode" class="text-xs text-[var(--color-text-muted)] mt-2">
        Sign up at
        <a href="https://app.getzep.com/" target="_blank" rel="noopener" class="text-[#2068FF] hover:underline">app.getzep.com</a>
        — free tier is sufficient for PoC.
      </p>
    </section>

    <!-- Simulation Defaults -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Simulation Defaults</h2>
      <div class="space-y-6">
        <!-- Agent Count -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Agent Count</label>
          <input
            type="range"
            v-model.number="agentCount"
            min="10"
            max="500"
            step="10"
            class="w-full accent-[var(--color-primary)]"
          />
          <div class="text-center text-2xl font-semibold text-[var(--color-primary)]">{{ agentCount }}</div>
        </div>

        <!-- Duration -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Duration</label>
          <div class="flex gap-2">
            <button
              v-for="d in durations"
              :key="d.value"
              @click="duration = d.value"
              class="flex-1 px-3 py-2 text-sm rounded-lg border transition-colors cursor-pointer"
              :class="duration === d.value
                ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/50'"
            >
              {{ d.label }}
            </button>
          </div>
        </div>

        <!-- Platform -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Platform</label>
          <div class="flex gap-2">
            <button
              v-for="p in platforms"
              :key="p.id"
              @click="platformMode = p.id"
              class="flex-1 px-3 py-2 text-sm rounded-lg border transition-colors cursor-pointer"
              :class="platformMode === p.id
                ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/50'"
            >
              {{ p.label }}
            </button>
          </div>
        </div>
      </div>

      <p class="text-xs text-[var(--color-text-muted)] mt-4">
        These defaults pre-fill the Scenario Builder. You can override them per-simulation.
      </p>
    </section>

    <!-- Demo Features -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Demo Features</h2>
      <label class="flex items-center justify-between p-3 md:p-4 rounded-lg border border-[var(--color-border)] cursor-pointer transition-colors hover:border-[#2068FF]/50">
        <div>
          <div class="text-sm font-medium text-[var(--color-text)]">Show Collaboration Presence</div>
          <div class="text-xs text-[var(--color-text-muted)] mt-0.5">Simulates other team members viewing the app</div>
        </div>
        <div
          class="relative w-10 h-6 rounded-full transition-colors shrink-0 ml-4"
          :class="showPresence ? 'bg-[#2068FF]' : 'bg-[var(--color-border-strong)]'"
        >
          <input type="checkbox" v-model="showPresence" class="sr-only" />
          <div
            class="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform"
            :class="{ 'translate-x-4': showPresence }"
          />
        </div>
      </label>
    </section>

    <!-- Info -->
    <section class="bg-[var(--color-primary-light)] border border-[#2068FF]/20 rounded-lg p-3 md:p-4">
      <p v-if="isDemoMode" class="text-xs text-[var(--color-text-secondary)]">
        Running in demo mode with pre-generated simulation data. Switch to production mode by setting
        <code class="bg-[var(--color-border)] px-1 rounded">DEMO_MODE=false</code> and configuring API keys.
      </p>
      <p v-else class="text-xs text-[var(--color-text-secondary)]">
        Settings are stored locally in your browser. For Docker deployments, configure via
        <code class="bg-[var(--color-border)] px-1 rounded">.env</code> file instead.
      </p>
    </section>
  </div>
</template>
