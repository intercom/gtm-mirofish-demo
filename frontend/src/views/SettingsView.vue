<script setup>
import { ref, onMounted } from 'vue'
import { useTheme } from '../composables/useTheme.js'

const { preference, setTheme } = useTheme()

const provider = ref('anthropic')
const apiKey = ref('')
const zepKey = ref('')
const connectionStatus = ref({ llm: null, zep: null })

onMounted(() => {
  const saved = localStorage.getItem('mirofish-settings')
  if (saved) {
    const s = JSON.parse(saved)
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
}

async function testConnection(service) {
  connectionStatus.value[service] = 'testing'
  // TODO: Implement connection test endpoints
  setTimeout(() => {
    connectionStatus.value[service] = 'success'
  }, 1000)
}

const providers = [
  { id: 'anthropic', name: 'Claude (Anthropic)', model: 'claude-sonnet-4-20250514' },
  { id: 'openai', name: 'OpenAI (GPT-4o)', model: 'gpt-4o' },
  { id: 'gemini', name: 'Google Gemini', model: 'gemini-2.5-flash' },
]

const themeOptions = [
  { id: 'auto', name: 'Auto', description: 'Dark on landing, light in app' },
  { id: 'light', name: 'Light', description: 'Always light mode' },
  { id: 'dark', name: 'Dark', description: 'Always dark mode' },
  { id: 'system', name: 'System', description: 'Follow OS preference' },
]
</script>

<template>
  <div class="max-w-2xl mx-auto px-6 py-10">
    <h1 class="text-2xl font-semibold text-[#050505] dark:text-[#e0e0e0] mb-8">Settings</h1>

    <!-- Theme -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] dark:text-[#e0e0e0] mb-4">Appearance</h2>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button
          v-for="opt in themeOptions"
          :key="opt.id"
          @click="setTheme(opt.id)"
          class="p-3 rounded-lg border text-center transition-colors cursor-pointer"
          :class="preference === opt.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.08)] dark:bg-[rgba(32,104,255,0.15)]'
            : 'border-black/10 dark:border-white/10 hover:border-[#2068FF]/50'"
        >
          <div class="text-sm font-medium text-[#050505] dark:text-[#e0e0e0]">{{ opt.name }}</div>
          <div class="text-[10px] text-[#888] dark:text-[#666] mt-0.5">{{ opt.description }}</div>
        </button>
      </div>
    </section>

    <!-- LLM Provider -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] dark:text-[#e0e0e0] mb-4">LLM Provider</h2>
      <div class="space-y-3">
        <label v-for="p in providers" :key="p.id"
          class="flex items-center gap-3 p-4 rounded-lg border cursor-pointer transition-colors"
          :class="provider === p.id
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)] dark:bg-[rgba(32,104,255,0.12)]'
            : 'border-black/10 dark:border-white/10 hover:border-[#2068FF]/50'">
          <input type="radio" :value="p.id" v-model="provider" @change="save" class="accent-[#2068FF]" />
          <div>
            <div class="text-sm font-medium text-[#050505] dark:text-[#e0e0e0]">{{ p.name }}</div>
            <div class="text-xs text-[#888] dark:text-[#666]">Model: {{ p.model }}</div>
          </div>
        </label>
      </div>

      <div class="mt-4">
        <label class="block text-xs uppercase tracking-wider text-[#888] dark:text-[#666] mb-2">API Key</label>
        <div class="flex gap-2">
          <input type="password" v-model="apiKey" @change="save"
            placeholder="Enter your API key"
            class="flex-1 border border-black/10 dark:border-white/10 rounded-lg px-4 py-2 text-sm bg-white dark:bg-white/5 text-[#050505] dark:text-[#e0e0e0] focus:ring-2 focus:ring-[#2068FF]" />
          <button @click="testConnection('llm')"
            class="px-4 py-2 text-sm border border-black/10 dark:border-white/10 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 text-[#050505] dark:text-[#e0e0e0] transition-colors">
            {{ connectionStatus.llm === 'testing' ? 'Testing...' : connectionStatus.llm === 'success' ? '&#10003; Connected' : 'Test' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Zep Cloud -->
    <section class="mb-10">
      <h2 class="text-sm font-semibold text-[#050505] dark:text-[#e0e0e0] mb-4">Zep Cloud (Knowledge Graph)</h2>
      <div class="flex gap-2">
        <input type="password" v-model="zepKey" @change="save"
          placeholder="Enter Zep API key"
          class="flex-1 border border-black/10 dark:border-white/10 rounded-lg px-4 py-2 text-sm bg-white dark:bg-white/5 text-[#050505] dark:text-[#e0e0e0] focus:ring-2 focus:ring-[#2068FF]" />
        <button @click="testConnection('zep')"
          class="px-4 py-2 text-sm border border-black/10 dark:border-white/10 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 text-[#050505] dark:text-[#e0e0e0] transition-colors">
          {{ connectionStatus.zep === 'testing' ? 'Testing...' : connectionStatus.zep === 'success' ? '&#10003; Connected' : 'Test' }}
        </button>
      </div>
      <p class="text-xs text-[#888] dark:text-[#666] mt-2">
        Sign up at <a href="https://app.getzep.com/" target="_blank" class="text-[#2068FF]">app.getzep.com</a> — free tier is sufficient for PoC.
      </p>
    </section>

    <!-- Info -->
    <section class="bg-[rgba(32,104,255,0.04)] dark:bg-[rgba(32,104,255,0.1)] border border-[#2068FF]/20 rounded-lg p-4">
      <p class="text-xs text-[#555] dark:text-[#aaa]">
        Settings are stored locally in your browser. For Docker deployments, configure via
        <code class="bg-black/5 dark:bg-white/10 px-1 rounded">{{ '.env' }}</code> file instead.
      </p>
    </section>
  </div>
</template>
