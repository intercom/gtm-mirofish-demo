<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useSimulationStore } from '../../stores/simulation'
import { scenariosApi } from '../../api/scenarios'

const props = defineProps({
  runs: { type: Array, default: null },
})

const emit = defineEmits(['select'])

const store = useSimulationStore()
const loading = ref(false)
const entries = ref([])
const error = ref(null)

// Filters
const filterTemplate = ref('all')
const dateRange = ref('all')
const sortMetric = ref('composite')

// Interaction state
const expandedId = ref(null)
const compareIds = ref([])
const showCompare = ref(false)

// Fetch leaderboard data from backend
async function fetchLeaderboard() {
  loading.value = true
  error.value = null
  try {
    const sourceRuns = props.runs || store.sessionRuns
    const res = await scenariosApi.getLeaderboard(sourceRuns)
    entries.value = res.data?.data || res.data || []
  } catch (e) {
    error.value = e.message || 'Failed to load leaderboard'
    entries.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchLeaderboard)

// Re-fetch when source runs change
watch(() => props.runs, fetchLeaderboard)
watch(() => store.sessionRuns.length, fetchLeaderboard)

// Template names for filter dropdown
const templateNames = computed(() => {
  const names = new Set()
  for (const e of entries.value) {
    if (e.scenarioName) names.add(e.scenarioName)
  }
  return [...names].sort()
})

// Date range filter cutoffs
function getDateCutoff(range) {
  const now = Date.now()
  if (range === '7d') return now - 7 * 86400000
  if (range === '30d') return now - 30 * 86400000
  if (range === '90d') return now - 90 * 86400000
  return 0
}

// Filtered + sorted entries
const rankedEntries = computed(() => {
  let result = [...entries.value]

  if (filterTemplate.value !== 'all') {
    result = result.filter(e => e.scenarioName === filterTemplate.value)
  }
  if (dateRange.value !== 'all') {
    const cutoff = getDateCutoff(dateRange.value)
    result = result.filter(e => (e.timestamp || 0) >= cutoff)
  }

  const metric = sortMetric.value
  result.sort((a, b) => {
    if (metric === 'actions') return (b.totalActions || 0) - (a.totalActions || 0)
    if (metric === 'rounds') return (b.totalRounds || 0) - (a.totalRounds || 0)
    const scoreA = a.scores?.[metric] ?? a.scores?.composite ?? 0
    const scoreB = b.scores?.[metric] ?? b.scores?.composite ?? 0
    return scoreB - scoreA
  })

  // Re-assign display ranks after filtering
  return result.map((e, i) => ({ ...e, displayRank: i + 1 }))
})

const topThree = computed(() => rankedEntries.value.slice(0, 3))
const restEntries = computed(() => rankedEntries.value.slice(3))

// Medal display
const medals = ['#FFD700', '#C0C0C0', '#CD7F32']
const medalLabels = ['1st', '2nd', '3rd']

function toggleExpand(id) {
  expandedId.value = expandedId.value === id ? null : id
}

function toggleCompare(id) {
  const idx = compareIds.value.indexOf(id)
  if (idx >= 0) {
    compareIds.value.splice(idx, 1)
  } else if (compareIds.value.length < 2) {
    compareIds.value.push(id)
  }
  showCompare.value = compareIds.value.length === 2
}

function clearCompare() {
  compareIds.value = []
  showCompare.value = false
}

const compareEntries = computed(() =>
  compareIds.value.map(id => rankedEntries.value.find(e => e.id === id)).filter(Boolean),
)

function handleSelect(entry) {
  emit('select', entry)
}

function formatDate(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

function scoreBarWidth(value) {
  return `${Math.max(value, 4)}%`
}
</script>

<template>
  <div class="w-full">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-[var(--color-text)]">Performance Leaderboard</h2>
      <button
        v-if="compareIds.length > 0"
        @click="clearCompare"
        class="text-xs font-medium px-3 py-1.5 rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors"
      >
        Clear compare
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2 mb-5">
      <select
        v-model="filterTemplate"
        class="text-xs border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-2.5 py-1.5 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
      >
        <option value="all">All templates</option>
        <option v-for="name in templateNames" :key="name" :value="name">{{ name }}</option>
      </select>
      <select
        v-model="dateRange"
        class="text-xs border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-2.5 py-1.5 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
      >
        <option value="all">All time</option>
        <option value="7d">Last 7 days</option>
        <option value="30d">Last 30 days</option>
        <option value="90d">Last 90 days</option>
      </select>
      <select
        v-model="sortMetric"
        class="text-xs border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-2.5 py-1.5 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
      >
        <option value="composite">Composite Score</option>
        <option value="sentiment">Sentiment</option>
        <option value="consensus">Consensus</option>
        <option value="decisionQuality">Decision Quality</option>
        <option value="actions">Total Actions</option>
        <option value="rounds">Total Rounds</option>
      </select>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <svg class="animate-spin h-6 w-6 text-[#2068FF]" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="text-center py-8">
      <p class="text-sm text-red-500 mb-2">{{ error }}</p>
      <button @click="fetchLeaderboard" class="text-xs text-[#2068FF] hover:underline">Retry</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="rankedEntries.length === 0" class="text-center py-12">
      <div class="w-12 h-12 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-3">
        <svg class="w-5 h-5 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 0 1 3 3h-15a3 3 0 0 1 3-3m9 0v-4.5A3.375 3.375 0 0 0 13.125 10.875h-2.25A3.375 3.375 0 0 0 7.5 14.25v4.5m6-6V6.75A2.25 2.25 0 0 0 11.25 4.5h-.75a2.25 2.25 0 0 0-2.25 2.25V8.5" />
        </svg>
      </div>
      <p class="text-sm text-[var(--color-text-secondary)]">No simulation runs to rank yet.</p>
    </div>

    <template v-else>
      <!-- Top 3 Podium -->
      <div class="grid grid-cols-3 gap-3 mb-6">
        <div
          v-for="(entry, idx) in topThree"
          :key="entry.id"
          class="relative border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg p-4 text-center cursor-pointer transition-shadow hover:shadow-[var(--shadow-md)]"
          :class="{ 'ring-2 ring-[#2068FF]': compareIds.includes(entry.id) }"
          @click="handleSelect(entry)"
        >
          <!-- Medal -->
          <div
            class="w-8 h-8 rounded-full flex items-center justify-center mx-auto mb-2 text-xs font-bold text-white"
            :style="{ backgroundColor: medals[idx] }"
          >
            {{ medalLabels[idx] }}
          </div>
          <div class="text-xs font-semibold text-[var(--color-text)] truncate mb-1" :title="entry.scenarioName">
            {{ entry.scenarioName }}
          </div>
          <div class="text-2xl font-bold text-[#2068FF]">{{ entry.scores?.composite }}</div>
          <div class="text-[10px] text-[var(--color-text-muted)] mt-0.5">composite score</div>

          <!-- Compare checkbox -->
          <button
            class="absolute top-2 right-2 w-5 h-5 rounded border flex items-center justify-center text-[10px] transition-colors"
            :class="compareIds.includes(entry.id)
              ? 'bg-[#2068FF] border-[#2068FF] text-white'
              : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[#2068FF]'"
            @click.stop="toggleCompare(entry.id)"
            title="Compare"
          >
            <svg v-if="compareIds.includes(entry.id)" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Full Leaderboard List -->
      <div class="border border-[var(--color-border)] rounded-lg overflow-hidden bg-[var(--color-surface)]">
        <!-- Header row -->
        <div class="grid grid-cols-[2.5rem_1fr_4.5rem_4.5rem_4.5rem_5rem_2.5rem] gap-2 px-4 py-2.5 bg-[var(--color-tint)] text-[10px] font-semibold text-[var(--color-text-muted)] uppercase tracking-wide">
          <div>#</div>
          <div>Simulation</div>
          <div class="text-right">Sent.</div>
          <div class="text-right">Cons.</div>
          <div class="text-right">Qual.</div>
          <div class="text-right">Score</div>
          <div></div>
        </div>

        <!-- Rows -->
        <div
          v-for="entry in rankedEntries"
          :key="entry.id"
          class="border-t border-[var(--color-border)]"
        >
          <div
            class="grid grid-cols-[2.5rem_1fr_4.5rem_4.5rem_4.5rem_5rem_2.5rem] gap-2 px-4 py-3 items-center cursor-pointer transition-colors hover:bg-[rgba(32,104,255,0.03)]"
            :class="{ 'bg-[rgba(32,104,255,0.04)]': compareIds.includes(entry.id) }"
            @click="handleSelect(entry)"
          >
            <!-- Rank -->
            <div class="flex items-center">
              <span
                v-if="entry.displayRank <= 3"
                class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
                :style="{ backgroundColor: medals[entry.displayRank - 1] }"
              >{{ entry.displayRank }}</span>
              <span v-else class="text-sm font-medium text-[var(--color-text-muted)]">{{ entry.displayRank }}</span>
            </div>

            <!-- Name + date -->
            <div class="min-w-0">
              <div class="text-sm font-medium text-[var(--color-text)] truncate">{{ entry.scenarioName }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)]">{{ formatDate(entry.timestamp) }}</div>
            </div>

            <!-- Metric cells -->
            <div class="text-right text-xs font-medium text-[var(--color-text)]">{{ entry.scores?.sentiment }}</div>
            <div class="text-right text-xs font-medium text-[var(--color-text)]">{{ entry.scores?.consensus }}</div>
            <div class="text-right text-xs font-medium text-[var(--color-text)]">{{ entry.scores?.decisionQuality }}</div>

            <!-- Composite with bar -->
            <div class="text-right">
              <div class="text-sm font-bold text-[#2068FF]">{{ entry.scores?.composite }}</div>
              <div class="h-1 rounded-full bg-[var(--color-border)] mt-1">
                <div class="h-1 rounded-full bg-[#2068FF] transition-all" :style="{ width: scoreBarWidth(entry.scores?.composite) }" />
              </div>
            </div>

            <!-- Expand + compare -->
            <div class="flex items-center gap-1">
              <button
                class="w-5 h-5 rounded border flex items-center justify-center transition-colors"
                :class="compareIds.includes(entry.id)
                  ? 'bg-[#2068FF] border-[#2068FF] text-white'
                  : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[#2068FF]'"
                @click.stop="toggleCompare(entry.id)"
                title="Compare"
              >
                <svg v-if="compareIds.includes(entry.id)" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                </svg>
              </button>
            </div>
          </div>

          <!-- "Why this rank?" expandable -->
          <div
            class="px-4 py-0 overflow-hidden transition-all"
            :class="expandedId === entry.id ? 'max-h-60 py-3' : 'max-h-0'"
          >
            <button
              class="text-[11px] text-[#2068FF] hover:underline mb-2 font-medium"
              @click.stop="toggleExpand(entry.id)"
            >
              {{ expandedId === entry.id ? 'Hide breakdown' : 'Why this rank?' }}
            </button>
            <div v-if="expandedId === entry.id" class="space-y-2">
              <div v-for="metric in [
                { key: 'sentiment', label: 'Sentiment', weight: '35%', color: '#2068FF' },
                { key: 'consensus', label: 'Consensus', weight: '30%', color: '#ff5600' },
                { key: 'decisionQuality', label: 'Decision Quality', weight: '35%', color: '#AA00FF' },
              ]" :key="metric.key" class="flex items-center gap-3">
                <span class="text-[11px] text-[var(--color-text-secondary)] w-28">{{ metric.label }} ({{ metric.weight }})</span>
                <div class="flex-1 h-2 rounded-full bg-[var(--color-border)]">
                  <div class="h-2 rounded-full transition-all" :style="{ width: scoreBarWidth(entry.scores?.[metric.key]), backgroundColor: metric.color }" />
                </div>
                <span class="text-xs font-semibold text-[var(--color-text)] w-8 text-right">{{ entry.scores?.[metric.key] }}</span>
              </div>
              <div class="text-[10px] text-[var(--color-text-muted)] pt-1">
                {{ entry.totalActions || 0 }} actions across {{ entry.totalRounds || 0 }} rounds with {{ entry.agentCount || 0 }} agents
              </div>
            </div>
          </div>

          <!-- "Why this rank?" toggle when collapsed -->
          <div v-if="expandedId !== entry.id" class="px-4 pb-2">
            <button
              class="text-[11px] text-[#2068FF] hover:underline font-medium"
              @click.stop="toggleExpand(entry.id)"
            >
              Why this rank?
            </button>
          </div>
        </div>
      </div>

      <!-- Compare Panel -->
      <Transition name="compare">
        <div
          v-if="showCompare && compareEntries.length === 2"
          class="mt-6 border border-[#2068FF]/30 bg-[rgba(32,104,255,0.03)] rounded-lg p-5"
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-[var(--color-text)]">Head-to-Head Comparison</h3>
            <button
              @click="clearCompare"
              class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="grid grid-cols-[1fr_auto_1fr] gap-4">
            <!-- Entry A -->
            <div class="text-center">
              <div class="text-xs font-semibold text-[var(--color-text)] truncate mb-2">{{ compareEntries[0].scenarioName }}</div>
              <div class="text-2xl font-bold text-[#2068FF]">{{ compareEntries[0].scores?.composite }}</div>
            </div>
            <div class="flex items-center text-sm font-bold text-[var(--color-text-muted)]">vs</div>
            <!-- Entry B -->
            <div class="text-center">
              <div class="text-xs font-semibold text-[var(--color-text)] truncate mb-2">{{ compareEntries[1].scenarioName }}</div>
              <div class="text-2xl font-bold text-[#ff5600]">{{ compareEntries[1].scores?.composite }}</div>
            </div>
          </div>

          <!-- Metric comparison bars -->
          <div class="mt-4 space-y-3">
            <div v-for="metric in [
              { key: 'sentiment', label: 'Sentiment' },
              { key: 'consensus', label: 'Consensus' },
              { key: 'decisionQuality', label: 'Decision Quality' },
            ]" :key="metric.key">
              <div class="flex items-center justify-between text-[11px] text-[var(--color-text-secondary)] mb-1">
                <span class="font-semibold" :class="compareEntries[0].scores?.[metric.key] >= compareEntries[1].scores?.[metric.key] ? 'text-[#2068FF]' : ''">
                  {{ compareEntries[0].scores?.[metric.key] }}
                </span>
                <span>{{ metric.label }}</span>
                <span class="font-semibold" :class="compareEntries[1].scores?.[metric.key] >= compareEntries[0].scores?.[metric.key] ? 'text-[#ff5600]' : ''">
                  {{ compareEntries[1].scores?.[metric.key] }}
                </span>
              </div>
              <div class="flex gap-1 h-2">
                <div class="flex-1 flex justify-end">
                  <div class="h-2 rounded-l-full bg-[#2068FF] transition-all" :style="{ width: scoreBarWidth(compareEntries[0].scores?.[metric.key]) }" />
                </div>
                <div class="flex-1">
                  <div class="h-2 rounded-r-full bg-[#ff5600] transition-all" :style="{ width: scoreBarWidth(compareEntries[1].scores?.[metric.key]) }" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </template>
  </div>
</template>

<style scoped>
.compare-enter-active,
.compare-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.compare-enter-from,
.compare-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
