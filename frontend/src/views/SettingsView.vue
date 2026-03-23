<script setup>
import { ref, onMounted } from 'vue'

const provider = ref('anthropic')
const apiKey = ref('')
const zepKey = ref('')
const connectionStatus = ref({ llm: null, zep: null })
const saved = ref(false)
let savedTimer = null

onMounted(() => {
  const stored = localStorage.getItem('mirofish-settings')
  if (stored) {
    const s = JSON.parse(stored)
    provider.value = s.provider || 'anthropic'
    apiKey.value = s.apiKey || ''
    zepKey.value = s.zepKey || ''
  }
})

function save() {
  localStorage.setItem('mirofish-settings', JSON.stringify({
    provider: provider.value,
    apiKey: apiKey.value,
    zepKey: zepKey.value,
  }))
  saved.value = true
  clearTimeout(savedTimer)
  savedTimer = setTimeout(() => { saved.value = false }, 2000)
}

async function testConnection(service) {
  connectionStatus.value[service] = 'testing'
  try {
    // TODO: Replace with real connection test endpoint
    await new Promise(resolve => setTimeout(resolve, 1000))
    connectionStatus.value[service] = 'success'
  } catch {
    connectionStatus.value[service] = 'error'
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
  <div class="max-w-2xl mx-auto px-6 py-10">
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-semibold text-[#050505]">Settings</h1>
      <transition name="fade">
        <span v-if="saved" class="text-xs font-medium text-[#090] bg-[rgba(0,153,0,0.08)] px-3 py-1 rounded-full">
          ✓ Saved
        </span>
      </transition>
    </div>

    <!-- LLM Provider -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] mb-4">LLM Provider</h2>
      <div class="space-y-3">
        <label v-for="p in providers" :key="p.id"
          class="flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-colors"
          :class="provider === p.id ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)]' : 'border-black/10 hover:border-[#2068FF]/50'">
          <input type="radio" :value="p.id" v-model="provider" @change="save" class="accent-[#2068FF]" />
          <div>
            <div class="text-sm font-medium text-[#050505]">{{ p.name }}</div>
            <div class="text-xs text-[#888]">Model: {{ p.model }}</div>
          </div>
        </label>
      </div>

      <div class="mt-4">
        <label class="block text-xs uppercase tracking-wider text-[#888] mb-2">API Key</label>
        <div class="flex gap-2">
          <input type="password" v-model="apiKey" @change="save"
            placeholder="Enter your API key"
            class="flex-1 border border-black/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]" />
          <button @click="testConnection('llm')"
            class="px-4 py-2 text-sm border border-black/10 rounded-lg hover:bg-black/5 transition-colors"
            :class="statusClass('llm')">
            {{ statusLabel('llm') }}
          </button>
        </div>
      </div>
    </section>

    <!-- Zep Cloud -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] mb-4">Zep Cloud (Knowledge Graph)</h2>
      <div class="flex gap-2">
        <input type="password" v-model="zepKey" @change="save"
          placeholder="Enter Zep API key"
          class="flex-1 border border-black/10 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]" />
        <button @click="testConnection('zep')"
          class="px-4 py-2 text-sm border border-black/10 rounded-lg hover:bg-black/5 transition-colors"
          :class="statusClass('zep')">
          {{ statusLabel('zep') }}
        </button>
      </div>
      <p class="text-xs text-[#888] mt-2">
        Sign up at <a href="https://app.getzep.com/" target="_blank" class="text-[#2068FF]">app.getzep.com</a> — free tier is sufficient for PoC.
      </p>
    </section>

    <!-- Info -->
    <section class="bg-[rgba(32,104,255,0.04)] border border-[#2068FF]/20 rounded-lg p-4">
      <p class="text-xs text-[#555]">
        Settings are stored locally in your browser. For Docker deployments, configure via
        <code class="bg-black/5 px-1 rounded">.env</code> file instead.
      </p>
    </section>
  </div>
</template>
