<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import draggable from 'vuedraggable'
import { useSimulationStore } from '../stores/simulation'
import { useKeyboardShortcuts } from '../composables/useKeyboardShortcuts'
import { usePullToRefresh } from '../composables/usePullToRefresh'
import { useStaggerAnimation } from '../composables/useStaggerAnimation'
import { getAllCachedTaskIds } from '../composables/useReportCache'
import DashboardMiniChart from '../components/dashboard/DashboardMiniChart.vue'
import { useLocale } from '../composables/useLocale'
import { useDashboardLayout } from '../composables/useDashboardLayout'
import { usePagination } from '../composables/usePagination'
import Pagination from '../components/common/Pagination.vue'
import { usePermissions } from '../composables/usePermissions'
import ConfirmDialog from '../components/ui/ConfirmDialog.vue'
import KeyboardShortcutsHelp from '../components/ui/KeyboardShortcutsHelp.vue'
import ScenarioCalendar from '../components/simulation/ScenarioCalendar.vue'

const router = useRouter()
const store = useSimulationStore()
const { formatRelativeTime, formatShortDateTime, formatNumber } = useLocale()
const { customOrder, saveOrder, clearOrder, applyOrder } = useDashboardLayout()
const { can } = usePermissions()

const viewMode = ref('list')

const cachedReportIds = ref(new Set())

onMounted(async () => {
  const ids = await getAllCachedTaskIds().catch(() => [])
  cachedReportIds.value = new Set(ids)
})

const showDeleteDialog = ref(false)
const showClearDialog = ref(false)
const pendingDeleteRun = ref(null)

const searchQuery = ref('')
const searchInput = ref(null)
const sortBy = ref('newest')

const statusOptions = ['all', 'completed', 'in_progress', 'failed']
const filterStatus = ref('all')

const { onBeforeEnter, onEnter, onLeave, reset: resetStagger } = useStaggerAnimation({
  delay: 60,
  duration: 350,
})
watch([searchQuery, filterStatus, sortBy], () => resetStagger())

const sortOptions = computed(() => {
  const options = [
    { value: 'newest', label: 'Newest first' },
    { value: 'oldest', label: 'Oldest first' },
    { value: 'most_actions', label: 'Most actions' },
    { value: 'most_rounds', label: 'Most rounds' },
  ]
  if (customOrder.value.length > 0) {
    options.push({ value: 'custom', label: 'Custom order' })
  }
  return options
})

// --- KPI computations (prioritized: most important first) ---

const simulationsShortcuts = [
  { key: '/', label: 'Focus search', action: () => searchInput.value?.focus() },
  { key: 'n', label: 'New simulation', action: () => router.push('/') },
  { key: 'Escape', label: 'Clear search', global: true, display: 'Esc', action: () => {
    const tag = document.activeElement?.tagName?.toLowerCase()
    if (tag === 'input' || tag === 'select') {
      document.activeElement.blur()
      searchQuery.value = ''
      filterStatus.value = 'all'
    }
  }},
]
const { showHelp, modLabel } = useKeyboardShortcuts(simulationsShortcuts)

const totalActions = computed(() =>
  store.sessionRuns.reduce((sum, r) => sum + (r.totalActions || 0), 0),
)

const avgActionsPerRun = computed(() => {
  if (!store.hasRuns) return 0
  return Math.round(totalActions.value / store.sessionRuns.length)
})

const successRate = computed(() => {
  if (!store.hasRuns) return 0
  const completed = store.sessionRuns.filter(r => normalizeStatus(r.status) === 'completed').length
  return Math.round((completed / store.sessionRuns.length) * 100)
})

const mostUsedScenario = computed(() => {
  if (!store.hasRuns) return null
  const counts = {}
  for (const run of store.sessionRuns) {
    const name = run.scenarioName || 'Untitled'
    counts[name] = (counts[name] || 0) + 1
  }
  let maxName = null
  let maxCount = 0
  for (const [name, count] of Object.entries(counts)) {
    if (count > maxCount) {
      maxCount = count
      maxName = name
    }
  }
  return maxName
})

// --- Chart data derived from session runs ---

const activityChartData = computed(() => {
  if (!store.hasRuns) return []
  const sorted = [...store.sessionRuns].sort((a, b) => a.timestamp - b.timestamp)
  const recent = sorted.slice(-10)
  return recent.map(r => ({ label: '', value: r.totalActions || 0 }))
})

const platformChartData = computed(() => {
  const twitter = store.sessionRuns.reduce((s, r) => s + (r.twitterActions || 0), 0)
  const reddit = store.sessionRuns.reduce((s, r) => s + (r.redditActions || 0), 0)
  if (!twitter && !reddit) return []
  return [
    { label: 'Twitter', value: twitter },
    { label: 'Reddit', value: reddit },
  ]
})

const roundsChartData = computed(() => {
  if (!store.hasRuns) return []
  const sorted = [...store.sessionRuns].sort((a, b) => a.timestamp - b.timestamp)
  const recent = sorted.slice(-8)
  return recent.map((r, i) => ({ label: `#${i + 1}`, value: r.totalRounds || 0 }))
})

// --- Pull to refresh ---

const scrollContainerRef = ref(null)

function handleRefresh() {
  return new Promise(resolve => setTimeout(resolve, 600))
}

const { pulling, pullDistance, refreshing, PULL_THRESHOLD } = usePullToRefresh(scrollContainerRef, handleRefresh)

// --- Filtering & sorting ---

function normalizeStatus(status) {
  if (!status) return 'completed'
  const s = status.toLowerCase()
  if (s === 'completed' || s === 'complete') return 'completed'
  if (s === 'failed' || s === 'error') return 'failed'
  if (['building_graph', 'preparing', 'running', 'in_progress'].includes(s)) return 'in_progress'
  return 'completed'
}

const filteredRuns = computed(() => {
  let result = [...store.sessionRuns]

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    result = result.filter(r =>
      (r.scenarioName || '').toLowerCase().includes(q),
    )
  }

  if (filterStatus.value !== 'all') {
    result = result.filter(r => normalizeStatus(r.status) === filterStatus.value)
  }

  if (sortBy.value === 'custom') {
    result = applyOrder(result)
  } else {
    switch (sortBy.value) {
      case 'oldest':
        result.sort((a, b) => a.timestamp - b.timestamp)
        break
      case 'most_actions':
        result.sort((a, b) => (b.totalActions || 0) - (a.totalActions || 0))
        break
      case 'most_rounds':
        result.sort((a, b) => (b.totalRounds || 0) - (a.totalRounds || 0))
        break
      default:
        result.sort((a, b) => b.timestamp - a.timestamp)
    }
  }

  return result
})

const {
  currentPage,
  totalPages,
  paginatedItems: paginatedRuns,
} = usePagination(filteredRuns, { perPage: 10 })

const displayRuns = ref([])

watch(paginatedRuns, (runs) => {
  displayRuns.value = [...runs]
}, { immediate: true })

function onDragEnd() {
  saveOrder(displayRuns.value.map(r => r.id))
  sortBy.value = 'custom'
}

function clearCustomOrder() {
  clearOrder()
  sortBy.value = 'newest'
}

function statusLabel(status) {
  const s = normalizeStatus(status)
  if (s === 'completed') return 'Completed'
  if (s === 'in_progress') return 'In Progress'
  if (s === 'failed') return 'Failed'
  return 'Completed'
}

function statusClasses(status) {
  const s = normalizeStatus(status)
  if (s === 'completed') return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
  if (s === 'in_progress') return 'bg-blue-500/10 text-blue-500 border-blue-500/20 animate-pulse'
  if (s === 'failed') return 'bg-red-500/10 text-red-500 border-red-500/20'
  return 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
}

function canRerun(run) {
  return run.scenarioId && run.seedText
}

function rerunUrl(run) {
  const params = new URLSearchParams()
  params.set('rerun', 'true')
  if (run.seedText) params.set('seedText', run.seedText)
  if (run.agentCount) params.set('agentCount', String(run.agentCount))
  if (run.personas?.length) params.set('personas', JSON.stringify(run.personas))
  if (run.industries?.length) params.set('industries', JSON.stringify(run.industries))
  if (run.duration) params.set('duration', String(run.duration))
  if (run.platformMode) params.set('platformMode', run.platformMode)
  return `/scenarios/${run.scenarioId}?${params.toString()}`
}

function deleteRun(run) {
  pendingDeleteRun.value = run
  showDeleteDialog.value = true
}

function confirmDelete() {
  if (pendingDeleteRun.value) {
    store.removeSessionRun(pendingDeleteRun.value.id)
    pendingDeleteRun.value = null
  }
  showDeleteDialog.value = false
}

function clearAll() {
  showClearDialog.value = true
}

function confirmClearAll() {
  store.clearAllRuns()
  showClearDialog.value = false
}

function navigateToRun(run) {
  router.push(`/workspace/${run.id}?tab=simulation`)
}

function exportRun(run) {
  const data = {
    id: run.id,
    scenarioId: run.scenarioId,
    scenarioName: run.scenarioName,
    config: {
      seedText: run.seedText,
      agentCount: run.agentCount,
      personas: run.personas,
      industries: run.industries,
      duration: run.duration,
      platformMode: run.platformMode,
    },
    results: {
      totalRounds: run.totalRounds,
      totalActions: run.totalActions,
      twitterActions: run.twitterActions,
      redditActions: run.redditActions,
      status: run.status,
    },
    timestamp: run.timestamp,
    exportedAt: new Date().toISOString(),
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `simulation-${run.id}.json`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div
    ref="scrollContainerRef"
    class="dashboard-scroll-container"
  >
    <!-- Pull-to-refresh indicator -->
    <Transition name="fade">
      <div
        v-if="pulling || refreshing"
        class="pull-indicator"
        :style="{ transform: `translateY(${pullDistance}px)` }"
      >
        <svg
          class="w-5 h-5 text-[#2068FF]"
          :class="{ 'animate-spin': refreshing }"
          :style="{ transform: refreshing ? '' : `rotate(${Math.min(pullDistance / PULL_THRESHOLD * 180, 180)}deg)` }"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
        </svg>
        <span class="text-xs text-[var(--color-text-muted)]">
          {{ refreshing ? 'Refreshing...' : pullDistance >= PULL_THRESHOLD ? 'Release to refresh' : 'Pull to refresh' }}
        </span>
      </div>
    </Transition>

    <div
      class="max-w-5xl mx-auto px-3 md:px-6 py-4 md:py-10"
      :style="{ transform: pulling || refreshing ? `translateY(${pullDistance}px)` : '' }"
    >
      <!-- Header -->
      <div class="flex items-center justify-between gap-3 mb-4 md:mb-8">
        <div class="flex items-center gap-2">
          <h1 class="text-lg md:text-2xl font-semibold text-[var(--color-text)]">Dashboard</h1>
          <span
            v-if="store.hasRuns"
            class="text-[10px] md:text-xs font-medium text-[#2068FF] bg-[rgba(32,104,255,0.08)] px-2 py-0.5 rounded-full"
          >
            {{ store.sessionRuns.length }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <!-- View mode toggle -->
          <div v-if="store.hasRuns" class="flex items-center border border-[var(--color-border)] rounded-lg overflow-hidden">
            <button
              @click="viewMode = 'list'"
              class="p-2 transition-colors"
              :class="viewMode === 'list' ? 'bg-[#2068FF] text-white' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-tint)]'"
              title="List view"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
              </svg>
            </button>
            <button
              @click="viewMode = 'calendar'"
              class="p-2 transition-colors"
              :class="viewMode === 'calendar' ? 'bg-[#2068FF] text-white' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-tint)]'"
              title="Calendar view"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
              </svg>
            </button>
          </div>
          <router-link
            v-if="store.hasRuns"
            to="/comparison"
            class="inline-flex items-center gap-1.5 text-[11px] md:text-xs font-medium min-h-[44px] md:min-h-0 px-3 py-2 rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors no-underline"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
            </svg>
            Compare
          </router-link>
          <button
            v-if="store.hasRuns && can('delete_simulations')"
            @click="clearAll"
            class="text-[11px] md:text-xs font-medium min-h-[44px] md:min-h-0 px-3 py-2 rounded-lg border border-red-500/30 text-red-500 hover:bg-red-500/10 active:bg-red-500/20 transition-colors"
          >
            Clear
          </button>
          <router-link
            :to="`/replay/${run.id}`"
            class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors no-underline"
          >
            Replay
          </router-link>
          <router-link
            v-if="can('create_simulations')"
            to="/"
            class="inline-flex items-center gap-1.5 bg-[#2068FF] hover:bg-[#1a5ae0] active:bg-[#1550cc] text-white text-[11px] md:text-sm font-medium min-h-[44px] md:min-h-0 px-3 md:px-4 py-2 rounded-lg transition-colors no-underline"
          >
            <svg class="w-3.5 h-3.5 md:w-4 md:h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            <span class="hidden sm:inline">New Simulation</span>
            <span class="sm:hidden">New</span>
          </router-link>
        </div>
      </div>

      <!-- KPI Cards — 2×2 on mobile, 4-across on desktop (most important first) -->
      <div v-if="store.hasRuns" class="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-3 mb-4 md:mb-6">
        <div class="kpi-card">
          <div class="kpi-label">Total Runs</div>
          <div class="kpi-value">{{ store.sessionRuns.length }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Total Actions</div>
          <div class="kpi-value">{{ formatNumber(totalActions) }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Avg / Run</div>
          <div class="kpi-value">{{ formatNumber(avgActionsPerRun) }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Success Rate</div>
          <div class="kpi-value text-emerald-500">{{ successRate }}%</div>
        </div>
      </div>

      <!-- Charts — horizontally scrollable on mobile, grid on desktop -->
      <div
        v-if="store.hasRuns && activityChartData.length"
        class="mb-4 md:mb-6 -mx-3 md:mx-0"
      >
        <div class="text-[11px] md:text-xs font-medium text-[var(--color-text-muted)] mb-2 px-3 md:px-0">Trends</div>
        <div class="flex md:grid md:grid-cols-3 gap-3 overflow-x-auto snap-x snap-mandatory px-3 md:px-0 pb-2 md:pb-0 scrollbar-hide">
          <DashboardMiniChart
            title="Actions over time"
            type="sparkline"
            :data="activityChartData"
            color="#2068FF"
          />
          <DashboardMiniChart
            v-if="platformChartData.length"
            title="Platform split"
            type="donut"
            :data="platformChartData"
          />
          <DashboardMiniChart
            v-if="roundsChartData.length"
            title="Rounds per run"
            type="bar"
            :data="roundsChartData"
            color="#ff5600"
          />
        </div>
      </div>

      <!-- Calendar view -->
      <ScenarioCalendar
        v-if="store.hasRuns && viewMode === 'calendar'"
        :runs="store.sessionRuns"
        @select-run="navigateToRun"
      />

      <!-- Search / Filter / Sort (list mode only) -->
      <div v-if="store.hasRuns && viewMode === 'list'" class="flex flex-col sm:flex-row gap-2 md:gap-3 mb-4 md:mb-6">
        <div class="flex-1 relative">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search scenarios..."
            class="w-full pl-9 pr-3 py-2.5 md:py-2 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
          />
        </div>
        <div class="flex gap-2">
          <select
            v-model="filterStatus"
            class="flex-1 sm:flex-none text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2.5 md:py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
          >
            <option v-for="opt in statusOptions" :key="opt" :value="opt">
              {{ opt === 'all' ? 'All statuses' : opt === 'in_progress' ? 'In Progress' : opt.charAt(0).toUpperCase() + opt.slice(1) }}
            </option>
          </select>
          <select
            v-model="sortBy"
            class="flex-1 sm:flex-none text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2.5 md:py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
          >
            <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!store.hasRuns" class="text-center py-12 md:py-24">
        <div class="w-14 h-14 md:w-16 md:h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-4 md:mb-5">
          <svg class="w-6 h-6 md:w-7 md:h-7 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
          </svg>
        </div>
        <h2 class="text-sm md:text-base font-semibold text-[var(--color-text)] mb-2">No simulation runs yet</h2>
        <p class="text-xs md:text-sm text-[var(--color-text-secondary)] mb-5 md:mb-6 max-w-xs mx-auto">
          Run your first simulation from the home page to see your results here.
        </p>
        <router-link
          v-if="can('create_simulations')"
          to="/"
          class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] active:bg-[#1550cc] text-white text-sm font-medium min-h-[44px] px-5 py-2.5 rounded-lg transition-colors no-underline"
        >
          Run your first simulation
        </router-link>
      </div>

      <!-- No results from filter (list mode) -->
      <div v-else-if="viewMode === 'list' && filteredRuns.length === 0" class="text-center py-10 md:py-12">
        <p class="text-sm text-[var(--color-text-muted)]">No simulations match your filters.</p>
        <button
          @click="searchQuery = ''; filterStatus = 'all'"
          class="text-sm text-[#2068FF] hover:underline mt-2 min-h-[44px]"
        >
          Clear filters
        </button>
      </div>

      <!-- Activity feed — card-based run list (list mode) -->
      <div v-else-if="viewMode === 'list'">
        <div class="flex items-center justify-between mb-2">
          <div class="text-[11px] md:text-xs font-medium text-[var(--color-text-muted)]">
            Recent Activity
          </div>
          <div v-if="sortBy === 'custom'" class="flex items-center gap-2">
            <span class="text-[10px] md:text-xs text-[var(--color-text-muted)]">Drag to reorder</span>
            <button
              @click="clearCustomOrder"
              class="text-[10px] md:text-xs text-[#2068FF] hover:underline"
            >
              Reset order
            </button>
          </div>
        </div>
        <draggable
          v-model="displayRuns"
          item-key="id"
          handle=".drag-handle"
          ghost-class="drag-ghost"
          :animation="150"
          tag="div"
          class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4"
          @end="onDragEnd"
        >
          <template #item="{ element: run, index }">
          <div
            :data-index="index"
            class="run-card card-interactive group/card"
          >
            <!-- Card header -->
            <div class="flex items-start justify-between mb-2 md:mb-3">
              <div class="drag-handle shrink-0 mr-2 mt-0.5 cursor-grab active:cursor-grabbing text-[var(--color-text-muted)] opacity-0 group-hover/card:opacity-100 transition-opacity hover:text-[#2068FF]">
                <svg class="w-4 h-5" viewBox="0 0 16 20" fill="currentColor">
                  <circle cx="5" cy="4" r="1.5"/>
                  <circle cx="11" cy="4" r="1.5"/>
                  <circle cx="5" cy="10" r="1.5"/>
                  <circle cx="11" cy="10" r="1.5"/>
                  <circle cx="5" cy="16" r="1.5"/>
                  <circle cx="11" cy="16" r="1.5"/>
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5 md:gap-2 mb-0.5 md:mb-1">
                  <h3 class="text-[13px] md:text-sm font-semibold text-[var(--color-text)] leading-snug truncate">{{ run.scenarioName }}</h3>
                  <span
                    class="inline-flex items-center text-[9px] md:text-[10px] font-medium px-1.5 py-0.5 rounded-full border shrink-0"
                    :class="statusClasses(run.status)"
                  >
                    {{ statusLabel(run.status) }}
                  </span>
                </div>
                <div class="text-[11px] md:text-xs text-[var(--color-text-muted)]">
                  <span class="hidden md:inline">{{ formatShortDateTime(run.timestamp) }} &mdash; </span>{{ formatRelativeTime(run.timestamp) }}
                </div>
              </div>
              <div class="flex items-center gap-0.5 ml-2 shrink-0">
                <button
                  @click="exportRun(run)"
                  class="min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 flex items-center justify-center p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[#2068FF] hover:bg-[rgba(32,104,255,0.08)] active:bg-[rgba(32,104,255,0.15)] transition-colors"
                  title="Export as JSON"
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                </button>
                <button
                  v-if="can('delete_simulations')"
                  @click="deleteRun(run)"
                  class="min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 flex items-center justify-center p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10 active:bg-red-500/20 transition-colors"
                  title="Delete run"
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Compact stats row on mobile, 2×2 grid on desktop -->
            <div class="grid grid-cols-4 md:grid-cols-2 gap-1.5 md:gap-3 mb-3 md:mb-4">
              <div class="bg-[var(--color-tint)] rounded-md px-2 md:px-3 py-1.5 md:py-2">
                <div class="text-[10px] md:text-xs text-[var(--color-text-muted)]">Rounds</div>
                <div class="text-[13px] md:text-sm font-semibold text-[var(--color-text)]">{{ run.totalRounds }}</div>
              </div>
              <div class="bg-[var(--color-tint)] rounded-md px-2 md:px-3 py-1.5 md:py-2">
                <div class="text-[10px] md:text-xs text-[var(--color-text-muted)]">Actions</div>
                <div class="text-[13px] md:text-sm font-semibold text-[var(--color-text)]">{{ run.totalActions }}</div>
              </div>
              <div class="bg-[rgba(32,104,255,0.06)] rounded-md px-2 md:px-3 py-1.5 md:py-2">
                <div class="text-[10px] md:text-xs text-[#2068FF]">Twitter</div>
                <div class="text-[13px] md:text-sm font-semibold text-[var(--color-text)]">{{ run.twitterActions }}</div>
              </div>
              <div class="bg-[rgba(255,86,0,0.06)] rounded-md px-2 md:px-3 py-1.5 md:py-2">
                <div class="text-[10px] md:text-xs text-[#ff5600]">Reddit</div>
                <div class="text-[13px] md:text-sm font-semibold text-[var(--color-text)]">{{ run.redditActions }}</div>
              </div>
            </div>

            <!-- Touch-friendly action buttons (min 44px height) -->
            <div class="flex items-center gap-1.5 md:gap-2">
              <router-link
                :to="`/workspace/${run.id}?tab=graph`"
                class="flex-1 text-center text-[11px] md:text-xs font-medium px-2 md:px-3 min-h-[44px] md:min-h-0 py-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] active:bg-[rgba(32,104,255,0.06)] transition-colors no-underline flex items-center justify-center"
              >
                Graph
              </router-link>
              <router-link
                :to="`/workspace/${run.id}?tab=simulation`"
                class="flex-1 text-center text-[11px] md:text-xs font-medium px-2 md:px-3 min-h-[44px] md:min-h-0 py-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] active:bg-[rgba(32,104,255,0.06)] transition-colors no-underline flex items-center justify-center"
              >
                Sim
              </router-link>
              <router-link
                :to="`/report/${run.id}`"
                class="flex-1 text-center text-[11px] md:text-xs font-medium px-2 md:px-3 min-h-[44px] md:min-h-0 py-2 rounded-md bg-[#2068FF] text-white hover:bg-[#1a5ae0] active:bg-[#1550cc] transition-colors no-underline flex items-center justify-center relative"
              >
                Report
                <span
                  v-if="cachedReportIds.has(run.id)"
                  class="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center"
                  title="Available offline"
                >
                  <svg class="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </span>
              </router-link>
              <router-link
                v-if="canRerun(run) && can('create_simulations')"
                :to="rerunUrl(run)"
                class="min-w-[44px] min-h-[44px] md:min-w-0 md:min-h-0 flex items-center justify-center p-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[#2068FF] hover:border-[#2068FF]/50 active:bg-[rgba(32,104,255,0.06)] transition-colors no-underline"
                title="Re-run simulation"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
                </svg>
              </router-link>
            </div>
          </div>
          </template>
        </draggable>
      </div>
    </div>

    <!-- Pagination -->
    <Pagination
      v-if="filteredRuns.length > 0"
      :current-page="currentPage"
      :total-pages="totalPages"
      :total="filteredRuns.length"
      @update:current-page="currentPage = $event"
    />

    <!-- Confirmation Dialogs -->
    <ConfirmDialog
      v-model="showDeleteDialog"
      title="Delete Simulation"
      :message="`Are you sure you want to delete &quot;${pendingDeleteRun?.scenarioName || ''}&quot;? This cannot be undone.`"
      confirmLabel="Delete"
      :destructive="true"
      @confirm="confirmDelete"
    />
    <ConfirmDialog
      v-model="showClearDialog"
      title="Clear All Simulations"
      :message="`This will remove all ${store.sessionRuns.length} simulation runs from history. This cannot be undone.`"
      confirmLabel="Clear All"
      :destructive="true"
      @confirm="confirmClearAll"
    />

    <!-- Shortcuts hint -->
    <button
      @click="showHelp = true"
      class="fixed bottom-4 right-4 flex items-center gap-1.5 px-3 py-1.5 text-xs text-[var(--color-text-muted)] bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-sm hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition-colors"
    >
      <kbd class="inline-flex items-center justify-center w-5 h-5 text-[10px] font-medium bg-[var(--color-tint)] border border-[var(--color-border)] rounded">?</kbd>
      Shortcuts
    </button>

    <KeyboardShortcutsHelp
      :open="showHelp"
      :shortcuts="simulationsShortcuts"
      :modLabel="modLabel"
      @close="showHelp = false"
    />
  </div>
</template>

<style scoped>
.dashboard-scroll-container {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  position: relative;
}

.pull-indicator {
  position: absolute;
  top: -40px;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.5rem;
  z-index: 10;
  transition: transform 0.1s ease-out;
}

.kpi-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 0.625rem 0.75rem;
}
@media (min-width: 768px) {
  .kpi-card {
    padding: 0.75rem 1rem;
  }
}

.kpi-label {
  font-size: 10px;
  color: var(--color-text-muted);
  line-height: 1;
  margin-bottom: 2px;
}
@media (min-width: 768px) {
  .kpi-label {
    font-size: 12px;
    margin-bottom: 4px;
  }
}

.kpi-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.2;
}
@media (min-width: 768px) {
  .kpi-value {
    font-size: 18px;
  }
}

.run-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 0.75rem;
  transition: box-shadow 0.15s ease;
}
@media (min-width: 768px) {
  .run-card {
    padding: 1.25rem;
  }
}
.run-card:hover {
  box-shadow: var(--shadow-md);
}

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

.drag-ghost {
  opacity: 0.3;
  border-style: dashed;
}
</style>
