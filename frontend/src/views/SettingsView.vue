<script setup>
import { ref, watch, onMounted } from 'vue'

const STORAGE_KEY = 'mirofish-settings'

const provider = ref('anthropic')
const apiKey = ref('')
const zepKey = ref('')
const agentCount = ref(200)
const duration = ref(72)
const platformMode = ref('parallel')
const connectionStatus = ref({ llm: null, zep: null })
const connectionError = ref({ llm: '', zep: '' })
const authStatus = ref({ authEnabled: false, user: null, provider: null })

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
  const saved = localStorage.getItem(STORAGE_KEY)
  if (!saved) return
  const s = JSON.parse(saved)
  provider.value = s.provider || 'anthropic'
  apiKey.value = s.apiKey || ''
  zepKey.value = s.zepKey || ''
  agentCount.value = s.agentCount ?? 200
  duration.value = s.duration ?? 72
  platformMode.value = s.platformMode || 'parallel'
}

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    provider: provider.value,
    apiKey: apiKey.value,
    zepKey: zepKey.value,
    agentCount: agentCount.value,
    duration: duration.value,
    platformMode: platformMode.value,
  }))
}

watch([provider, apiKey, zepKey, agentCount, duration, platformMode], save, { deep: true })

async function testConnection(service) {
  connectionStatus.value[service] = 'testing'
  connectionError.value[service] = ''

  const endpoint = service === 'llm' ? '/api/settings/test-llm' : '/api/settings/test-zep'
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
    } else {
      connectionStatus.value[service] = 'error'
      connectionError.value[service] = data.error || 'Connection failed'
    }
  } catch {
    connectionStatus.value[service] = 'error'
    connectionError.value[service] = 'Network error — is the backend running?'
  }
}

async function fetchAuthStatus() {
  try {
    const res = await fetch('/api/settings/auth-status')
    if (res.ok) authStatus.value = await res.json()
  } catch {
    // Auth status is best-effort; silently ignore
  }
}

function logout() {
  window.location.href = '/api/auth/logout'
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
  if (status === 'success') return 'border-[#090] text-[#090]'
  if (status === 'error') return 'border-red-500 text-red-500'
  return 'border-black/10 hover:bg-black/5'
}

onMounted(() => {
  load()
  fetchAuthStatus()
})
</script>

<template>
  <div class="max-w-2xl mx-auto px-6 py-10">
    <h1 class="text-2xl font-semibold text-[#050505] mb-8">Settings</h1>

    <!-- ─── LLM Provider ─── -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] mb-4">LLM Provider</h2>
      <div class="space-y-3">
        <label
          v-for="p in providers"
          :key="p.id"
          class="flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-colors"
          :class="provider === p.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)]'
            : 'border-black/10 hover:border-[#2068FF]/50'"
        >
          <input type="radio" :value="p.id" v-model="provider" class="accent-[#2068FF]" />
          <div>
            <div class="text-sm font-medium text-[#050505]">{{ p.name }}</div>
            <div class="text-xs text-[#888]">Model: {{ p.model }}</div>
          </div>
        </label>
      </div>

      <div class="mt-4">
        <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">API Key</label>
        <div class="flex gap-2">
          <input
            type="password"
            v-model="apiKey"
            placeholder="Enter your API key"
            class="flex-1 border border-black/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2068FF]"
          />
          <button
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

    <!-- ─── Zep Cloud ─── -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] mb-4">Zep Cloud (Knowledge Graph)</h2>
      <div class="flex gap-2">
        <input
          type="password"
          v-model="zepKey"
          placeholder="Enter Zep API key"
          class="flex-1 border border-black/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2068FF]"
        />
        <button
          @click="testConnection('zep')"
          :disabled="!zepKey || connectionStatus.zep === 'testing'"
          class="px-4 py-2 text-sm border rounded-lg transition-colors whitespace-nowrap disabled:opacity-40 disabled:cursor-not-allowed"
          :class="testButtonClass('zep')"
        >
          {{ testButtonLabel('zep') }}
        </button>
      </div>
      <p v-if="connectionError.zep" class="text-xs text-red-500 mt-1">{{ connectionError.zep }}</p>
      <p v-else class="text-xs text-[#888] mt-2">
        Sign up at
        <a href="https://app.getzep.com/" target="_blank" rel="noopener" class="text-[#2068FF] hover:underline">app.getzep.com</a>
        — free tier is sufficient for PoC.
      </p>
    </section>

    <!-- ─── Simulation Defaults ─── -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] mb-4">Simulation Defaults</h2>

      <div class="space-y-6">
        <!-- Agent Count -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Agent Count</label>
          <input
            type="range"
            v-model.number="agentCount"
            min="10"
            max="500"
            step="10"
            class="w-full accent-[#2068FF]"
          />
          <div class="text-center text-2xl font-semibold text-[#2068FF]">{{ agentCount }}</div>
        </div>

        <!-- Duration -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Duration (hours)</label>
          <select
            v-model.number="duration"
            class="w-full border border-black/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2068FF]"
          >
            <option v-for="d in durations" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </div>

        <!-- Platform -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">Platform</label>
          <div class="flex gap-2">
            <button
              v-for="p in platforms"
              :key="p.id"
              @click="platformMode = p.id"
              class="flex-1 px-3 py-2 text-sm rounded-lg border transition-colors"
              :class="platformMode === p.id
                ? 'bg-[#2068FF] text-white border-[#2068FF]'
                : 'bg-white text-[#555] border-black/10 hover:border-[#2068FF]'"
            >
              {{ p.label }}
            </button>
          </div>
        </div>
      </div>

      <p class="text-xs text-[#888] mt-4">
        These defaults pre-fill the Scenario Builder. You can override them per-simulation.
      </p>
    </section>

    <!-- ─── Auth ─── -->
    <section v-if="authStatus.authEnabled" class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] mb-4">Authentication</h2>
      <div class="border border-black/10 rounded-lg p-4">
        <div v-if="authStatus.user" class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <img
              v-if="authStatus.user.picture"
              :src="authStatus.user.picture"
              :alt="authStatus.user.name"
              class="w-8 h-8 rounded-full"
            />
            <div v-else class="w-8 h-8 rounded-full bg-[#2068FF] flex items-center justify-center text-white text-sm font-medium">
              {{ (authStatus.user.name || authStatus.user.email || '?')[0].toUpperCase() }}
            </div>
            <div>
              <div class="text-sm font-medium text-[#050505]">{{ authStatus.user.name || 'User' }}</div>
              <div class="text-xs text-[#888]">{{ authStatus.user.email }}</div>
            </div>
          </div>
          <button
            @click="logout"
            class="px-4 py-2 text-sm border border-black/10 rounded-lg hover:bg-red-50 hover:border-red-300 hover:text-red-600 transition-colors"
          >
            Log out
          </button>
        </div>
        <div v-else class="text-sm text-[#888]">
          Not signed in.
          <router-link to="/login" class="text-[#2068FF] hover:underline ml-1">Sign in</router-link>
        </div>
      </div>
      <p class="text-xs text-[#888] mt-2">
        Auth provider: {{ authStatus.provider }} · Domain: @{{ authStatus.allowedDomain }}
      </p>
    </section>

    <!-- ─── Info ─── -->
    <section class="bg-[rgba(32,104,255,0.04)] border border-[#2068FF]/20 rounded-lg p-4">
      <p class="text-xs text-[#555]">
        Settings are stored locally in your browser. For Docker deployments, configure via
        <code class="bg-black/5 px-1 rounded">.env</code> file instead.
      </p>
    </section>
  </div>
</template>
