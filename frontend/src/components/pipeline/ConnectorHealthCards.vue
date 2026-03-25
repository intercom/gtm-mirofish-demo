<script setup>
import { ref, computed, onMounted } from 'vue'
import { dataPipelineApi } from '../../api/dataPipeline'
import { AppBadge } from '../common'

const connectors = ref([])
const loading = ref(true)
const error = ref(null)

async function fetchConnectors() {
  loading.value = true
  error.value = null
  try {
    const { data } = await dataPipelineApi.getConnectors()
    connectors.value = data.connectors
  } catch (err) {
    error.value = err.message || 'Failed to load connectors'
  } finally {
    loading.value = false
  }
}

function relativeTime(isoString) {
  const diff = Date.now() - new Date(isoString).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function formatNumber(n) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

function formatDuration(seconds) {
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return s > 0 ? `${m}m ${s}s` : `${m}m`
}

function badgeVariant(status) {
  if (status === 'healthy') return 'success'
  if (status === 'warning') return 'warning'
  return 'error'
}

function syncBadgeVariant(status) {
  return status === 'success' ? 'success' : 'error'
}

const sourceInitial = (name) => name.charAt(0).toUpperCase()

function sparklinePath(points) {
  if (!points || points.length === 0) return ''
  const w = 84
  const h = 24
  const pad = 2
  const step = (w - pad * 2) / (points.length - 1)
  return points
    .map((v, i) => {
      const x = pad + i * step
      const y = v === 1 ? pad : h - pad
      return `${i === 0 ? 'M' : 'L'}${x},${y}`
    })
    .join(' ')
}

function sparklineDots(points) {
  if (!points || points.length === 0) return []
  const w = 84
  const h = 24
  const pad = 2
  const step = (w - pad * 2) / (points.length - 1)
  return points.map((v, i) => ({
    cx: pad + i * step,
    cy: v === 1 ? pad : h - pad,
    success: v === 1,
  }))
}

const sortedConnectors = computed(() => {
  const order = { error: 0, warning: 1, healthy: 2 }
  return [...connectors.value].sort(
    (a, b) => (order[a.status] ?? 3) - (order[b.status] ?? 3),
  )
})

onMounted(fetchConnectors)
</script>

<template>
  <div>
    <!-- Loading skeleton -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div
        v-for="i in 6"
        :key="i"
        class="h-48 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] animate-pulse"
      />
    </div>

    <!-- Error state -->
    <div
      v-else-if="error"
      class="text-center py-12 text-[var(--color-text-secondary)]"
    >
      <p class="text-sm mb-3">{{ error }}</p>
      <button
        @click="fetchConnectors"
        class="text-sm text-[var(--color-primary)] hover:underline cursor-pointer"
      >
        Retry
      </button>
    </div>

    <!-- Card grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div
        v-for="c in sortedConnectors"
        :key="c.id"
        class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5 transition-shadow duration-[var(--transition-base)] hover:shadow-[var(--shadow-md)] group"
      >
        <!-- Header: icon + name + status badge -->
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center gap-3">
            <!-- Connector icon with brand color -->
            <div
              class="w-9 h-9 rounded-lg flex items-center justify-center text-white text-sm font-semibold shrink-0"
              :style="{ backgroundColor: c.icon_color }"
            >
              {{ sourceInitial(c.source) }}
            </div>
            <div class="min-w-0">
              <div class="text-sm font-semibold text-[var(--color-text)] truncate">
                {{ c.name }}
              </div>
              <div class="text-xs text-[var(--color-text-muted)] flex items-center gap-1">
                <span>{{ c.source }}</span>
                <svg class="w-3 h-3 shrink-0" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6h8M7.5 3.5 10 6 7.5 8.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>{{ c.destination }}</span>
              </div>
            </div>
          </div>
          <AppBadge :variant="badgeVariant(c.status)">
            {{ c.status }}
          </AppBadge>
        </div>

        <!-- Last sync row -->
        <div class="flex items-center justify-between mb-3 text-xs">
          <div class="flex items-center gap-2 text-[var(--color-text-secondary)]">
            <span
              class="w-1.5 h-1.5 rounded-full shrink-0"
              :class="c.last_sync.status === 'success' ? 'bg-[var(--color-success)]' : 'bg-[var(--color-error)]'"
            />
            <span>Last sync {{ relativeTime(c.last_sync.timestamp) }}</span>
          </div>
          <AppBadge :variant="syncBadgeVariant(c.last_sync.status)">
            {{ c.last_sync.status }}
          </AppBadge>
        </div>

        <!-- Stats row -->
        <div class="grid grid-cols-3 gap-2 mb-4">
          <div class="text-center">
            <div class="text-xs text-[var(--color-text-muted)]">Success</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">
              {{ (c.stats.success_rate_30d * 100).toFixed(0) }}%
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--color-text-muted)]">Avg rows</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">
              {{ formatNumber(c.stats.avg_rows_per_sync) }}
            </div>
          </div>
          <div class="text-center">
            <div class="text-xs text-[var(--color-text-muted)]">Duration</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">
              {{ formatDuration(c.stats.avg_duration_seconds) }}
            </div>
          </div>
        </div>

        <!-- Sparkline: 7-day sync history -->
        <div class="border-t border-[var(--color-border)] pt-3">
          <div class="text-[10px] text-[var(--color-text-muted)] mb-1">7-day sync history</div>
          <svg viewBox="0 0 84 24" class="w-full h-6" preserveAspectRatio="none">
            <path
              :d="sparklinePath(c.sparkline)"
              fill="none"
              :stroke="c.status === 'error' ? 'var(--color-error)' : c.status === 'warning' ? 'var(--color-warning)' : 'var(--color-success)'"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <circle
              v-for="(dot, idx) in sparklineDots(c.sparkline)"
              :key="idx"
              :cx="dot.cx"
              :cy="dot.cy"
              r="2.5"
              :fill="dot.success ? 'var(--color-success)' : 'var(--color-error)'"
            />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>
