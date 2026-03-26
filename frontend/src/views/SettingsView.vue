<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLanguage } from '../composables/useLanguage'
import { useToast } from '../composables/useToast'
import { useDemoMode } from '../composables/useDemoMode'
import { useSettingsStore } from '../stores/settings'
import { usePermissions } from '../composables/usePermissions'
import { API_BASE } from '../api/client'
import ThemeEditor from '../components/settings/ThemeEditor.vue'
import ServiceStatus from '../components/common/ServiceStatus.vue'
import ThemeSwitcher from '../components/common/ThemeSwitcher.vue'
import AuditLogViewer from '../components/settings/AuditLogViewer.vue'
import ApiKeyManagement from '../components/settings/ApiKeyManagement.vue'
import UserManagement from '../components/settings/UserManagement.vue'

const settingsStore = useSettingsStore()

const { t } = useI18n()
const { locale, languages, setLanguage } = useLanguage()
const toast = useToast()
const { isDemoMode } = useDemoMode()
const { isReadOnly, can } = usePermissions()

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
  { value: 24, key: 'settings.duration24' },
  { value: 48, key: 'settings.duration48' },
  { value: 72, key: 'settings.duration72' },
]

const platforms = [
  { id: 'twitter', key: 'settings.platformTwitter' },
  { id: 'reddit', key: 'settings.platformReddit' },
  { id: 'parallel', key: 'settings.platformBoth' },
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
    toast.error(t('settings.loadError'))
  }
}

function save() {
  if (isReadOnly.value) return
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
    toast.error(t('settings.saveError'))
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
      toast.success(t('settings.connectionSuccess', { service: service === 'llm' ? 'LLM' : 'Zep' }))
    } else {
      connectionStatus.value[service] = 'error'
      connectionError.value[service] = data.error || t('settings.connectionFailedGeneric')
      toast.error(t('settings.connectionFailed', { service: service === 'llm' ? 'LLM' : 'Zep' }))
    }
  } catch {
    connectionStatus.value[service] = 'error'
    connectionError.value[service] = t('settings.networkError')
    toast.error(t('settings.connectionFailed', { service: service === 'llm' ? 'LLM' : 'Zep' }))
  }
}


function testButtonLabel(service) {
  const status = connectionStatus.value[service]
  if (status === 'testing') return t('settings.testing')
  if (status === 'success') return t('settings.testConnected')
  if (status === 'error') return t('settings.testFailed')
  return t('settings.testConnection')
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
      <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">{{ t('settings.title') }}</h1>
      <transition name="fade">
        <span v-if="saved" class="text-xs font-medium text-[#090] bg-[rgba(0,153,0,0.08)] px-3 py-1 rounded-full">
          ✓ {{ t('common.saved') }}
        </span>
      </transition>
    </div>

    <!-- Demo Mode Banner -->
    <section v-if="isDemoMode" class="mb-8 md:mb-10 bg-[rgba(32,104,255,0.06)] border border-[#2068FF]/20 rounded-lg p-3 md:p-4 flex items-start gap-3">
      <svg class="w-5 h-5 text-[#2068FF] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-sm text-[var(--color-text-secondary)]">
        <span class="font-semibold text-[var(--color-text)]">{{ t('settings.demoModeBanner') }}</span> — {{ t('settings.demoModeBannerDesc') }}
      </p>
    </section>

    <!-- Service Status -->
    <section class="mb-8 md:mb-10">
      <ServiceStatus mode="expanded" />
    </section>

    <!-- Read-only Banner -->
    <section v-if="isReadOnly" class="mb-8 md:mb-10 bg-[rgba(255,86,0,0.06)] border border-[#ff5600]/20 rounded-lg p-3 md:p-4 flex items-start gap-3">
      <svg class="w-5 h-5 text-[#ff5600] shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
      </svg>
      <p class="text-sm text-[var(--color-text-secondary)]">
        <span class="font-semibold text-[var(--color-text)]">Read-only</span> — You can view settings but editing requires the Editor role.
      </p>
    </section>

    <!-- Theme -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">{{ t('settings.theme') }}</h2>
      <ThemeSwitcher />
    </section>

    <!-- Custom Theme Editor -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">Custom Themes</h2>
      <ThemeEditor />
    </section>

    <!-- Language -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">{{ t('settings.language') }}</h2>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="lang in languages"
          :key="lang.code"
          @click="setLanguage(lang.code)"
          class="flex items-center gap-2 px-4 py-2 rounded-lg border text-sm transition-colors cursor-pointer"
          :class="locale === lang.code
            ? 'border-[#2068FF] bg-[rgba(32,104,255,0.08)] text-[var(--color-text)]'
            : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50'"
        >
          <span>{{ lang.flag }}</span>
          <span>{{ lang.label }}</span>
        </button>
      </div>
    </section>

    <!-- LLM Provider -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">{{ t('settings.llmProvider') }}</h2>
      <div class="space-y-3">
        <label
          v-for="p in providers"
          :key="p.id"
          class="flex items-center gap-3 p-3 md:p-4 rounded-lg border transition-colors"
          :class="[
            provider === p.id
              ? 'border-[#2068FF] bg-[rgba(32,104,255,0.04)]'
              : 'border-[var(--color-border)] hover:border-[#2068FF]/50',
            isReadOnly ? 'cursor-default opacity-60' : 'cursor-pointer',
          ]"
        >
          <input type="radio" :value="p.id" v-model="provider" :disabled="isReadOnly" class="accent-[#2068FF]" />
          <div>
            <div class="text-sm font-medium text-[var(--color-text)]">{{ p.name }}</div>
            <div class="text-xs text-[var(--color-text-muted)]">{{ t('common.model', { model: p.model }) }}</div>
          </div>
        </label>
      </div>

      <div class="mt-4">
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">{{ t('settings.apiKey') }}</label>
        <div class="flex flex-col sm:flex-row gap-2">
          <input
            type="password"
            v-model="apiKey"
            :placeholder="isDemoMode ? t('settings.apiKeyDemoPlaceholder') : t('settings.apiKeyPlaceholder')"
            :disabled="isDemoMode || isReadOnly"
            class="flex-1 border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 md:px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]"
            :class="{ 'opacity-40 cursor-not-allowed': isDemoMode || isReadOnly }"
          />
          <span
            v-if="isDemoMode"
            class="px-4 py-2 text-sm font-medium text-[#090] bg-[rgba(0,153,0,0.08)] border border-[rgba(0,153,0,0.2)] rounded-lg whitespace-nowrap text-center"
          >{{ t('common.simulated') }}</span>
          <button
            v-else-if="!isReadOnly"
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
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">{{ t('settings.zepCloud') }}</h2>
      <div class="flex flex-col sm:flex-row gap-2">
        <input
          type="password"
          v-model="zepKey"
          :placeholder="isDemoMode ? t('settings.zepKeyDemoPlaceholder') : t('settings.zepKeyPlaceholder')"
          :disabled="isDemoMode || isReadOnly"
          class="flex-1 border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 md:px-4 py-2 text-sm focus:ring-2 focus:ring-[#2068FF]"
          :class="{ 'opacity-40 cursor-not-allowed': isDemoMode || isReadOnly }"
        />
        <span
          v-if="isDemoMode"
          class="px-4 py-2 text-sm font-medium text-[#090] bg-[rgba(0,153,0,0.08)] border border-[rgba(0,153,0,0.2)] rounded-lg whitespace-nowrap text-center"
        >{{ t('common.simulated') }}</span>
        <button
          v-else-if="!isReadOnly"
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
        <i18n-t keypath="settings.zepSignup" tag="span">
          <template #link><a href="https://app.getzep.com/" target="_blank" rel="noopener" class="text-[#2068FF] hover:underline">app.getzep.com</a></template>
        </i18n-t>
      </p>
    </section>

    <!-- API Keys -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">API Keys</h2>
      <p class="text-xs text-[var(--color-text-muted)] mb-4">
        Create keys for programmatic access to the MiroFish API. Keys use the <code class="bg-[var(--color-border)] px-1 rounded">mf_</code> prefix.
      </p>
      <ApiKeyManagement />
    </section>

    <!-- Simulation Defaults -->
    <section class="mb-8 md:mb-10">
      <h2 class="text-sm font-semibold text-[var(--color-text)] mb-4">{{ t('settings.simulationDefaults') }}</h2>
      <div class="space-y-6">
        <!-- Agent Count -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">{{ t('settings.agentCount') }}</label>
          <input
            type="range"
            v-model.number="agentCount"
            min="10"
            max="500"
            step="10"
            :disabled="isReadOnly"
            class="w-full accent-[var(--color-primary)]"
            :class="{ 'opacity-40 cursor-not-allowed': isReadOnly }"
          />
          <div class="text-center text-2xl font-semibold text-[var(--color-primary)]">{{ agentCount }}</div>
        </div>

        <!-- Duration -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">{{ t('settings.duration') }}</label>
          <div class="flex gap-2">
            <button
              v-for="d in durations"
              :key="d.value"
              @click="isReadOnly || (duration = d.value)"
              :disabled="isReadOnly"
              class="flex-1 px-3 py-2 text-sm rounded-lg border transition-colors"
              :class="[
                duration === d.value
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/50',
                isReadOnly ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
              ]"
            >
              {{ t(d.key) }}
            </button>
          </div>
        </div>

        <!-- Platform -->
        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">{{ t('settings.platform') }}</label>
          <div class="flex gap-2">
            <button
              v-for="p in platforms"
              :key="p.id"
              @click="isReadOnly || (platformMode = p.id)"
              :disabled="isReadOnly"
              class="flex-1 px-3 py-2 text-sm rounded-lg border transition-colors"
              :class="[
                platformMode === p.id
                  ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                  : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]/50',
                isReadOnly ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
              ]"
            >
              {{ t(p.key) }}
            </button>
          </div>
        </div>
      </div>

      <p class="text-xs text-[var(--color-text-muted)] mt-4">
        {{ t('settings.defaultsHint') }}
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

    <!-- User Management -->
    <section class="mb-8 md:mb-10">
      <UserManagement />
    </section>

    <!-- Security & Audit Log -->
    <section class="mb-8 md:mb-10">
      <AuditLogViewer />
    </section>

    <!-- Info -->
    <section class="bg-[var(--color-primary-light)] border border-[#2068FF]/20 rounded-lg p-3 md:p-4">
      <p v-if="isDemoMode" class="text-xs text-[var(--color-text-secondary)]">
        <i18n-t keypath="settings.demoProdHint" tag="span">
          <template #code><code class="bg-[var(--color-border)] px-1 rounded">DEMO_MODE=false</code></template>
        </i18n-t>
      </p>
      <p v-else class="text-xs text-[var(--color-text-secondary)]">
        <i18n-t keypath="settings.localStorageHint" tag="span">
          <template #code><code class="bg-[var(--color-border)] px-1 rounded">.env</code></template>
        </i18n-t>
      </p>
    </section>
  </div>
</template>
