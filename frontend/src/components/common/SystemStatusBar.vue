<script setup>
import { ref, computed } from 'vue'
import { useSystemStatus } from '../../composables/useSystemStatus'

const {
  apiStatus,
  lastHealthCheck,
  avgResponseTime,
  activeSimulationCount,
  dataMode,
  overallHealth,
  apiEndpoint,
  healthDetails,
} = useSystemStatus()

const expanded = ref(false)

const healthBg = computed(() => {
  switch (overallHealth.value) {
    case 'healthy': return 'bg-[rgba(0,153,0,0.06)]'
    case 'degraded': return 'bg-[rgba(245,158,11,0.08)]'
    case 'unhealthy': return 'bg-[rgba(239,68,68,0.08)]'
    default: return 'bg-[var(--color-tint)]'
  }
})

const statusDotClass = computed(() => {
  switch (apiStatus.value) {
    case 'healthy': return 'bg-[var(--color-success)]'
    case 'degraded': return 'bg-[var(--color-warning)]'
    case 'unhealthy': return 'bg-[var(--color-error)]'
    default: return 'bg-[var(--color-text-muted)]'
  }
})

const lastRefreshLabel = computed(() => {
  if (!lastHealthCheck.value) return '—'
  const ago = Math.round((Date.now() - lastHealthCheck.value) / 1000)
  if (ago < 5) return 'just now'
  if (ago < 60) return `${ago}s ago`
  return `${Math.floor(ago / 60)}m ago`
})

const appVersion = computed(() => healthDetails.value?.version || '0.0.0')

const featureFlags = computed(() => {
  if (!healthDetails.value) return []
  const flags = []
  if (healthDetails.value.auth_enabled) flags.push('Auth')
  if (healthDetails.value.llm_provider) flags.push(`LLM: ${healthDetails.value.llm_provider}`)
  return flags
})
</script>

<template>
  <div
    class="fixed bottom-0 inset-x-0 z-30 select-none border-t border-[var(--color-border)]"
    :class="healthBg"
    style="font-family: var(--font-mono); font-size: 11px; transition: background-color 0.3s"
  >
    <!-- Collapsed bar -->
    <button
      class="w-full h-6 flex items-center gap-4 px-3 text-[var(--color-text-secondary)] hover:text-[var(--color-text)] cursor-pointer"
      @click="expanded = !expanded"
    >
      <!-- API status dot -->
      <span class="flex items-center gap-1.5">
        <span
          class="w-1.5 h-1.5 rounded-full shrink-0"
          :class="[statusDotClass, apiStatus === 'healthy' ? '' : 'animate-pulse']"
        />
        <span class="uppercase tracking-wide">API</span>
      </span>

      <span class="text-[var(--color-text-muted)]">|</span>

      <!-- Data mode -->
      <span>
        Mode: <span class="text-[var(--color-text)]">{{ dataMode }}</span>
      </span>

      <span class="text-[var(--color-text-muted)]">|</span>

      <!-- Active simulations -->
      <span>
        Sims: <span class="text-[var(--color-text)]">{{ activeSimulationCount }}</span>
      </span>

      <span class="text-[var(--color-text-muted)]">|</span>

      <!-- Last refresh -->
      <span>
        Refresh: <span class="text-[var(--color-text)]">{{ lastRefreshLabel }}</span>
      </span>

      <span class="text-[var(--color-text-muted)]">|</span>

      <!-- Avg response time -->
      <span>
        Latency: <span class="text-[var(--color-text)]">{{ avgResponseTime !== null ? `${avgResponseTime}ms` : '—' }}</span>
      </span>

      <!-- Expand indicator -->
      <span class="ml-auto text-[var(--color-text-muted)]">
        {{ expanded ? '▾' : '▸' }} Info
      </span>
    </button>

    <!-- Expanded details -->
    <div
      v-if="expanded"
      class="px-3 pb-2 pt-1 border-t border-[var(--color-border)] text-[var(--color-text-secondary)] grid grid-cols-[auto_1fr] gap-x-6 gap-y-0.5"
    >
      <span class="text-[var(--color-text-muted)]">Version</span>
      <span>{{ appVersion }}</span>

      <span class="text-[var(--color-text-muted)]">API Endpoint</span>
      <span>{{ apiEndpoint }}</span>

      <span class="text-[var(--color-text-muted)]">Backend</span>
      <span>{{ healthDetails?.service || '—' }}</span>

      <span class="text-[var(--color-text-muted)]">Features</span>
      <span>{{ featureFlags.length ? featureFlags.join(', ') : 'default' }}</span>
    </div>
  </div>
</template>
