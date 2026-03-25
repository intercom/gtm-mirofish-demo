<script setup>
import { ref, computed } from 'vue'
import { useSimulationStore } from '../stores/simulation'
import { useLocale } from '../composables/useLocale'
import ConfirmDialog from '../components/ui/ConfirmDialog.vue'

const store = useSimulationStore()
const { formatRelativeTime, formatShortDateTime, formatNumber } = useLocale()

const showDeleteDialog = ref(false)
const showClearDialog = ref(false)
const pendingDeleteRun = ref(null)

const searchQuery = ref('')
const sortBy = ref('newest')

const statusOptions = ['all', 'completed', 'in_progress', 'failed']
const filterStatus = ref('all')

const sortOptions = [
  { value: 'newest', label: 'Newest first' },
  { value: 'oldest', label: 'Oldest first' },
  { value: 'most_actions', label: 'Most actions' },
  { value: 'most_rounds', label: 'Most rounds' },
]

const totalActions = computed(() =>
  store.sessionRuns.reduce((sum, r) => sum + (r.totalActions || 0), 0),
)

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

  return result
})


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
  <div class="max-w-5xl mx-auto px-4 md:px-6 py-6 md:py-10">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 md:mb-8">
      <div class="flex items-center gap-3">
        <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Simulations</h1>
        <span
          v-if="store.hasRuns"
          class="text-xs font-medium text-[#2068FF] bg-[rgba(32,104,255,0.08)] px-2.5 py-0.5 rounded-full"
        >
          {{ store.sessionRuns.length }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <button
          v-if="store.hasRuns"
          @click="clearAll"
          class="text-xs font-medium px-3 py-2 rounded-lg border border-red-500/30 text-red-500 hover:bg-red-500/10 transition-colors"
        >
          Clear All
        </button>
        <router-link
          to="/"
          class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors no-underline"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Simulation
        </router-link>
      </div>
    </div>

    <!-- Summary Stats -->
    <div v-if="store.hasRuns" class="grid grid-cols-3 gap-3 mb-6">
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)]">Total Runs</div>
        <div class="text-lg font-semibold text-[var(--color-text)]">{{ store.sessionRuns.length }}</div>
      </div>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)]">Total Actions</div>
        <div class="text-lg font-semibold text-[var(--color-text)]">{{ formatNumber(totalActions) }}</div>
      </div>
      <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-4 py-3">
        <div class="text-xs text-[var(--color-text-muted)]">Top Scenario</div>
        <div class="text-sm font-semibold text-[var(--color-text)] truncate">{{ mostUsedScenario || '-' }}</div>
      </div>
    </div>

    <!-- Search / Filter / Sort Bar -->
    <div v-if="store.hasRuns" class="flex flex-col sm:flex-row gap-3 mb-6">
      <div class="flex-1 relative">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by scenario name..."
          class="w-full pl-9 pr-3 py-2 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] placeholder-[var(--color-text-muted)] focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        />
      </div>
      <div class="flex gap-2">
        <select
          v-model="filterStatus"
          class="text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        >
          <option v-for="opt in statusOptions" :key="opt" :value="opt">
            {{ opt === 'all' ? 'All statuses' : opt === 'in_progress' ? 'In Progress' : opt.charAt(0).toUpperCase() + opt.slice(1) }}
          </option>
        </select>
        <select
          v-model="sortBy"
          class="text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
        >
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!store.hasRuns" class="text-center py-16 md:py-24">
      <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-5">
        <svg class="w-7 h-7 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
        </svg>
      </div>
      <h2 class="text-base font-semibold text-[var(--color-text)] mb-2">No simulation runs yet</h2>
      <p class="text-sm text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
        Run your first simulation from the home page to see your results here.
      </p>
      <router-link
        to="/"
        class="inline-flex items-center gap-2 bg-[#2068FF] hover:bg-[#1a5ae0] text-white text-sm font-medium px-5 py-2.5 rounded-lg transition-colors no-underline"
      >
        Run your first simulation
      </router-link>
    </div>

    <!-- No results from filter -->
    <div v-else-if="filteredRuns.length === 0" class="text-center py-12">
      <p class="text-sm text-[var(--color-text-muted)]">No simulations match your filters.</p>
      <button
        @click="searchQuery = ''; filterStatus = 'all'"
        class="text-sm text-[#2068FF] hover:underline mt-2"
      >
        Clear filters
      </button>
    </div>

    <!-- Run cards -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="run in filteredRuns"
        :key="run.id"
        class="border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg p-5 transition-shadow hover:shadow-[var(--shadow-md)]"
      >
        <!-- Card header -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-sm font-semibold text-[var(--color-text)] leading-snug truncate">{{ run.scenarioName }}</h3>
              <span
                class="inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full border shrink-0"
                :class="statusClasses(run.status)"
              >
                {{ statusLabel(run.status) }}
              </span>
            </div>
            <div class="text-xs text-[var(--color-text-muted)]">
              {{ formatShortDateTime(run.timestamp) }} <span class="mx-1">-</span> {{ formatRelativeTime(run.timestamp) }}
            </div>
          </div>
          <div class="flex items-center gap-1 ml-2 shrink-0">
            <button
              @click="exportRun(run)"
              class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-[#2068FF] hover:bg-[rgba(32,104,255,0.08)] transition-colors"
              title="Export as JSON"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
            </button>
            <button
              @click="deleteRun(run)"
              class="p-1.5 rounded-md text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10 transition-colors"
              title="Delete run"
            >
              <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Stats grid -->
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div class="bg-[var(--color-tint)] rounded-md px-3 py-2">
            <div class="text-xs text-[var(--color-text-muted)]">Rounds</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.totalRounds }}</div>
          </div>
          <div class="bg-[var(--color-tint)] rounded-md px-3 py-2">
            <div class="text-xs text-[var(--color-text-muted)]">Actions</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.totalActions }}</div>
          </div>
          <div class="bg-[rgba(32,104,255,0.06)] rounded-md px-3 py-2">
            <div class="text-xs text-[#2068FF]">Twitter</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.twitterActions }}</div>
          </div>
          <div class="bg-[rgba(255,86,0,0.06)] rounded-md px-3 py-2">
            <div class="text-xs text-[#ff5600]">Reddit</div>
            <div class="text-sm font-semibold text-[var(--color-text)]">{{ run.redditActions }}</div>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="flex items-center gap-2">
          <router-link
            :to="`/workspace/${run.id}?tab=graph`"
            class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors no-underline"
          >
            Graph
          </router-link>
          <router-link
            :to="`/workspace/${run.id}?tab=simulation`"
            class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50 hover:text-[#2068FF] transition-colors no-underline"
          >
            Simulation
          </router-link>
          <router-link
            :to="`/report/${run.id}`"
            class="flex-1 text-center text-xs font-medium px-3 py-2 rounded-md bg-[#2068FF] text-white hover:bg-[#1a5ae0] transition-colors no-underline"
          >
            Report
          </router-link>
        </div>

        <!-- Re-run link -->
        <router-link
          v-if="canRerun(run)"
          :to="rerunUrl(run)"
          class="mt-3 flex items-center justify-center gap-1.5 text-xs text-[var(--color-text-muted)] hover:text-[#2068FF] transition-colors no-underline"
        >
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182" />
          </svg>
          Re-run
        </router-link>
      </div>
    </div>

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
  </div>
</template>
