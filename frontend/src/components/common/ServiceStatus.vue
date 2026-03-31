<script setup>
import { computed } from 'vue'
import { useServiceStatus } from '../../composables/useServiceStatus'
import { useToast } from '../../composables/useToast'
import client from '../../api/client'

const props = defineProps({
  mode: {
    type: String,
    default: 'compact',
    validator: (v) => ['compact', 'expanded'].includes(v),
  },
})

const { services: rawServices, loading, lastChecked, isAllOk, isDemoMode, isBackendReachable, check: refresh } = useServiceStatus()

// Build a status shape the template expects
const status = computed(() => {
  const svc = rawServices.value || {}
  const allOk = isAllOk.value
  const demo = isDemoMode.value
  const reachable = isBackendReachable.value
  let overall = 'unreachable'
  if (reachable && allOk) overall = 'healthy'
  else if (reachable && demo) overall = 'demo'
  else if (reachable) overall = 'degraded'
  return { overall, services: svc }
})
const toast = useToast()

const overall = computed(() => status.value?.overall ?? 'unreachable')

const dotColor = computed(() => {
  const map = {
    healthy: 'bg-[var(--color-success)]',
    degraded: 'bg-[var(--color-warning)]',
    demo: 'bg-[var(--color-fin-orange)]',
    unreachable: 'bg-[var(--color-error)]',
  }
  return map[overall.value] || map.unreachable
})

const tooltipText = computed(() => {
  const map = {
    healthy: 'All services connected',
    degraded: 'Some services in demo mode',
    demo: 'Demo mode — no API keys',
    unreachable: 'Backend unreachable',
  }
  return map[overall.value] || 'Unknown'
})

function normalizeStatus(raw) {
  if (raw === 'ok' || raw === 'connected') return 'connected'
  if (raw === 'unconfigured') return 'demo'
  if (raw === 'error') return 'error'
  return 'unknown'
}

const services = computed(() => {
  const s = status.value?.services ?? {}
  return [
    {
      key: 'llm',
      label: 'LLM Provider',
      status: normalizeStatus(s.llm?.status),
      detail: s.llm?.status === 'ok' || s.llm?.status === 'connected'
        ? 'Anthropic Claude — Connected'
        : s.llm?.message || 'Not configured',
    },
    {
      key: 'zep',
      label: 'Zep Cloud',
      status: normalizeStatus(s.zep?.status),
      detail: s.zep?.status === 'ok' || s.zep?.status === 'connected'
        ? 'Knowledge graph ready'
        : s.zep?.message || 'Using local fallback',
    },
    {
      key: 'oasis',
      label: 'OASIS Engine',
      status: normalizeStatus(s.backend?.status),
      detail: 'Simulation runtime',
    },
  ]
})

const lastCheckedLabel = computed(() => {
  if (!lastChecked.value) return 'Never'
  return new Date(lastChecked.value).toLocaleTimeString()
})

function statusDotClass(svcStatus) {
  const map = {
    connected: 'bg-[var(--color-success)]',
    demo: 'bg-[var(--color-fin-orange)]',
    error: 'bg-[var(--color-error)]',
  }
  return map[svcStatus] || 'bg-gray-400'
}

function statusLabel(svcStatus) {
  const map = { connected: 'Connected', demo: 'Demo', error: 'Error' }
  return map[svcStatus] || 'Unknown'
}

async function testConnection(serviceKey) {
  const path = serviceKey === 'llm' ? '/settings/test-llm' : '/settings/test-zep'

  try {
    const { data } = await client.post(path, {})
    if (data.ok) {
      toast.success(`${serviceKey.toUpperCase()} connection verified`)
    } else {
      toast.error(data.error || 'Connection test failed')
    }
  } catch {
    toast.error('Network error — is the backend running?')
  }
  refresh()
}
</script>

<template>
  <!-- Compact mode: dot + tooltip for navbar -->
  <div v-if="mode === 'compact'" class="relative group">
    <button
      class="flex items-center gap-2 text-xs text-white/40 hover:text-white/70 transition-colors"
      @click="refresh"
      :disabled="loading"
    >
      <span
        class="w-2 h-2 rounded-full shrink-0 transition-colors duration-500"
        :class="[dotColor, { 'animate-pulse': loading }]"
      />
      <span class="hidden sm:inline">{{ overall === 'healthy' ? 'Connected' : overall === 'demo' ? 'Demo' : overall === 'degraded' ? 'Partial' : 'Offline' }}</span>
    </button>

    <!-- Tooltip -->
    <div class="absolute top-full right-0 mt-2 w-52 bg-[#1a1a2e] border border-white/10 rounded-lg shadow-lg p-3 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 pointer-events-none">
      <p class="text-xs font-medium text-white mb-2">{{ tooltipText }}</p>
      <div class="space-y-1.5">
        <div v-for="svc in services" :key="svc.key" class="flex items-center gap-2">
          <span class="w-1.5 h-1.5 rounded-full shrink-0" :class="statusDotClass(svc.status)" />
          <span class="text-xs text-white/60">{{ svc.label }}</span>
        </div>
      </div>
      <p class="text-[10px] text-white/30 mt-2">Last checked: {{ lastCheckedLabel }}</p>
    </div>
  </div>

  <!-- Expanded mode: service cards for settings page -->
  <section v-else class="space-y-3">
    <div class="flex items-center justify-between mb-1">
      <h2 class="text-sm font-semibold text-[var(--color-text)]">Service Status</h2>
      <button
        @click="refresh"
        :disabled="loading"
        class="text-xs text-[var(--color-primary)] hover:underline disabled:opacity-40"
      >
        {{ loading ? 'Checking…' : 'Refresh' }}
      </button>
    </div>

    <TransitionGroup
      name="status-card"
      tag="div"
      class="space-y-2"
    >
      <div
        v-for="svc in services"
        :key="svc.key"
        class="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] transition-colors duration-300"
      >
        <span
          class="w-2.5 h-2.5 rounded-full shrink-0 transition-colors duration-500"
          :class="statusDotClass(svc.status)"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="text-sm font-medium text-[var(--color-text)]">{{ svc.label }}</span>
            <span
              class="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded-full"
              :class="{
                'bg-[rgba(0,153,0,0.08)] text-[var(--color-success)]': svc.status === 'connected',
                'bg-[rgba(255,86,0,0.08)] text-[var(--color-fin-orange)]': svc.status === 'demo',
              }"
            >
              {{ statusLabel(svc.status) }}
            </span>
          </div>
          <p class="text-xs text-[var(--color-text-muted)] truncate mt-0.5">{{ svc.detail }}</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="text-[10px] text-[var(--color-text-muted)] hidden sm:inline">{{ lastCheckedLabel }}</span>
          <button
            v-if="svc.key !== 'oasis' && svc.status === 'connected'"
            @click="testConnection(svc.key)"
            class="text-xs px-2.5 py-1 rounded border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors"
          >
            Test
          </button>
        </div>
      </div>
    </TransitionGroup>

    <p v-if="overall === 'demo'" class="text-xs text-[var(--color-text-muted)]">
      Running in demo mode — set API keys below for full functionality.
    </p>
  </section>
</template>

<style scoped>
.status-card-enter-active,
.status-card-leave-active {
  transition: all var(--transition-base) ease;
}
.status-card-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.status-card-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
