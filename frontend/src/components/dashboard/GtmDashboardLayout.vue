<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  title: {
    type: String,
    default: 'GTM Dashboard',
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['refresh', 'date-change'])

const dateRange = ref('last-30d')
const autoRefresh = ref(false)
const lastUpdated = ref(Date.now())
let refreshInterval = null

const dateRangeOptions = [
  { value: 'last-7d', label: 'Last 7 days' },
  { value: 'last-30d', label: 'Last 30 days' },
  { value: 'last-90d', label: 'Last 90 days' },
  { value: 'last-12m', label: 'Last 12 months' },
  { value: 'ytd', label: 'Year to date' },
]

const lastUpdatedLabel = computed(() => {
  const diff = Math.floor((Date.now() - lastUpdated.value) / 1000)
  if (diff < 5) return 'Just now'
  if (diff < 60) return `${diff}s ago`
  const m = Math.floor(diff / 60)
  return `${m}m ago`
})

function onDateChange() {
  emit('date-change', dateRange.value)
  refresh()
}

function refresh() {
  lastUpdated.value = Date.now()
  emit('refresh', dateRange.value)
}

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    refreshInterval = setInterval(refresh, 30000)
  } else {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// Keep lastUpdatedLabel reactive by ticking every 10s
let tickTimer = null
onMounted(() => {
  tickTimer = setInterval(() => {
    lastUpdated.value = lastUpdated.value // trigger reactivity via computed
  }, 10000)
})

onUnmounted(() => {
  clearInterval(refreshInterval)
  clearInterval(tickTimer)
})
</script>

<template>
  <div class="dashboard-layout">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="flex items-center gap-3 min-w-0">
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)] truncate">
          {{ title }}
        </h1>
        <span
          v-if="loading"
          class="shrink-0 w-2 h-2 rounded-full bg-[#2068FF] animate-pulse"
        />
      </div>

      <div class="flex items-center gap-2 shrink-0">
        <span class="hidden sm:inline text-xs text-[var(--color-text-muted)]">
          Updated {{ lastUpdatedLabel }}
        </span>

        <select
          v-model="dateRange"
          @change="onDateChange"
          class="text-xs border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-2.5 py-1.5 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        >
          <option v-for="opt in dateRangeOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>

        <button
          @click="toggleAutoRefresh"
          :title="autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh (30s)'"
          class="p-1.5 rounded-lg border transition-colors"
          :class="autoRefresh
            ? 'border-[#2068FF]/40 bg-[rgba(32,104,255,0.08)] text-[#2068FF]'
            : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[#2068FF] hover:border-[#2068FF]/30'"
        >
          <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
          </svg>
        </button>

        <button
          @click="refresh"
          class="text-xs font-medium px-3 py-1.5 rounded-lg bg-[#2068FF] hover:bg-[#1a5ae0] text-white transition-colors"
        >
          Refresh
        </button>
      </div>
    </header>

    <!-- Ticker slot (full width, above KPIs) -->
    <div v-if="$slots.ticker" class="dashboard-area-ticker">
      <slot name="ticker" />
    </div>

    <!-- KPI row -->
    <section v-if="$slots.kpis" class="dashboard-area-kpis">
      <slot name="kpis" />
    </section>

    <!-- Main content grid -->
    <div class="dashboard-grid">
      <div v-if="$slots['chart-left']" class="dashboard-area-chart-left">
        <slot name="chart-left" />
      </div>
      <div v-if="$slots['chart-right']" class="dashboard-area-chart-right">
        <slot name="chart-right" />
      </div>
    </div>

    <!-- Full-width chart -->
    <section v-if="$slots['full-chart']" class="dashboard-area-full-chart">
      <slot name="full-chart" />
    </section>

    <!-- Table section -->
    <section v-if="$slots.table" class="dashboard-area-table">
      <slot name="table" />
    </section>

    <!-- Catch-all default slot for extra content -->
    <div v-if="$slots.default">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.dashboard-layout {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

@media (min-width: 768px) {
  .dashboard-layout {
    padding: 2rem 1.5rem;
  }
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.dashboard-area-kpis {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

@media (min-width: 640px) {
  .dashboard-area-kpis {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (min-width: 1024px) {
  .dashboard-area-kpis {
    grid-template-columns: repeat(8, 1fr);
    gap: 1rem;
  }
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}

@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 2fr 1fr;
  }
}

.dashboard-area-chart-left,
.dashboard-area-chart-right,
.dashboard-area-full-chart,
.dashboard-area-table,
.dashboard-area-ticker {
  min-width: 0;
}
</style>
