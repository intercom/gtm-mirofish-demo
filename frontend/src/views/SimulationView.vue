<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import LoadingSpinner from '../components/ui/LoadingSpinner.vue'
import ErrorState from '../components/ui/ErrorState.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import { useToast } from '../composables/useToast'

const props = defineProps({ taskId: String })
const toast = useToast()

const runStatus = ref(null)
const allActions = ref([])
const activePlatform = ref('all')
const loading = ref(true)
const error = ref(null)

let pollTimer = null

// --- Status ---

const simulationStatus = computed(() => runStatus.value?.runner_status || 'idle')

const statusBadge = computed(() => {
  switch (simulationStatus.value) {
    case 'running': return { label: 'Running', classes: 'bg-green-100 text-green-700' }
    case 'completed': return { label: 'Completed', classes: 'bg-blue-100 text-[#2068FF]' }
    case 'failed': return { label: 'Failed', classes: 'bg-red-100 text-red-700' }
    case 'stopped': case 'stopping': return { label: 'Stopped', classes: 'bg-red-100 text-red-700' }
    default: return { label: 'Building', classes: 'bg-yellow-100 text-yellow-700' }
  }
})

const isTerminal = computed(() =>
  ['completed', 'failed', 'stopped'].includes(simulationStatus.value)
)

// --- Metrics ---

const progressPercent = computed(() => runStatus.value?.progress_percent ?? 0)
const currentRound = computed(() => runStatus.value?.current_round ?? 0)
const totalRounds = computed(() => runStatus.value?.total_rounds ?? 0)
const totalActions = computed(() => runStatus.value?.total_actions_count ?? 0)

const typeCounts = computed(() => {
  const counts = { replies: 0, likes: 0, reposts: 0 }
  for (const a of allActions.value) {
    if (a.action_type === 'REPLY_POST') counts.replies++
    else if (a.action_type === 'LIKE_POST') counts.likes++
    else if (a.action_type === 'REPOST') counts.reposts++
  }
  return counts
})

// --- Activity Feed ---

const filteredActivities = computed(() => {
  let list = allActions.value
  if (activePlatform.value !== 'all') {
    list = list.filter(a => a.platform === activePlatform.value)
  }
  return list.slice(0, 30)
})

// --- Chart ---

const timelineData = computed(() => {
  const byRound = {}
  for (const a of allActions.value) {
    const r = a.round_num ?? a.round ?? 0
    if (!byRound[r]) byRound[r] = 0
    byRound[r]++
  }
  return Object.keys(byRound)
    .map(Number)
    .sort((a, b) => a - b)
    .map(r => ({ round: r, count: byRound[r] }))
})

const CHART_W = 600
const CHART_H = 160
const CHART_PAD = 10

const chartLinePath = computed(() => {
  const d = timelineData.value
  if (d.length < 2) return ''
  const max = Math.max(...d.map(p => p.count), 1)
  const usable = CHART_H - CHART_PAD * 2
  return d.map((p, i) => {
    const x = (i / (d.length - 1)) * CHART_W
    const y = CHART_PAD + usable - (p.count / max) * usable
    return `${i === 0 ? 'M' : 'L'}${x},${y}`
  }).join(' ')
})

const chartAreaPath = computed(() => {
  const d = timelineData.value
  if (d.length < 2) return ''
  const max = Math.max(...d.map(p => p.count), 1)
  const usable = CHART_H - CHART_PAD * 2
  const pts = d.map((p, i) => {
    const x = (i / (d.length - 1)) * CHART_W
    const y = CHART_PAD + usable - (p.count / max) * usable
    return `${x},${y}`
  }).join(' L')
  return `M0,${CHART_H} L${pts} L${CHART_W},${CHART_H} Z`
})

// --- Polling ---

async function fetchStatus() {
  try {
    const res = await fetch(`/api/simulation/${props.taskId}/run-status`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    if (json.success) runStatus.value = json.data
  } catch (e) {
    error.value = e.message
    toast.error('Failed to fetch simulation status')
  } finally {
    loading.value = false
  }
}

async function fetchActions() {
  try {
    const res = await fetch(`/api/simulation/${props.taskId}/actions?limit=1000&offset=0`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success) allActions.value = json.data || []
  } catch {
    // non-critical
  }
}

function startPolling() {
  fetchStatus()
  fetchActions()
  pollTimer = setInterval(() => {
    if (isTerminal.value) return stopPolling()
    fetchStatus()
    fetchActions()
  }, 3000)
}

function stopPolling() {
  clearInterval(pollTimer)
  pollTimer = null
}

function retry() {
  loading.value = true
  error.value = null
  startPolling()
}

onMounted(startPolling)
onUnmounted(stopPolling)

// --- Helpers ---

const ACTION_DOT = {
  CREATE_POST: 'bg-[#2068FF]',
  REPLY_POST: 'bg-[#ff5600]',
  LIKE_POST: 'bg-[#A0F]',
  REPOST: 'bg-[#090]',
  DELETE_POST: 'bg-red-500',
  FOLLOW_USER: 'bg-[#888]',
  UNFOLLOW_USER: 'bg-[#888]',
}

const ACTION_LABEL = {
  CREATE_POST: 'posted',
  REPLY_POST: 'replied',
  LIKE_POST: 'liked',
  REPOST: 'reposted',
  DELETE_POST: 'deleted',
  FOLLOW_USER: 'followed',
  UNFOLLOW_USER: 'unfollowed',
}

const PLATFORM_TABS = [
  { key: 'all', label: 'Both Platforms' },
  { key: 'twitter', label: 'Twitter' },
  { key: 'reddit', label: 'Reddit' },
]

const METRIC_CARDS = computed(() => [
  { value: totalActions.value, label: 'Total Actions', color: 'text-[#2068FF]' },
  { value: typeCounts.value.replies, label: 'Replies', color: 'text-[#ff5600]' },
  { value: typeCounts.value.likes, label: 'Likes', color: 'text-[#A0F]' },
  { value: typeCounts.value.reposts, label: 'Reposts', color: 'text-[#090]' },
])
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-8">
    <!-- Loading State -->
    <LoadingSpinner v-if="loading" label="Connecting to simulation..." />

    <!-- Error State -->
    <ErrorState
      v-else-if="error"
      title="Simulation unavailable"
      :message="error"
      @retry="retry"
    />

    <!-- Simulation Content -->
    <template v-else>
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-semibold text-[#050505]" style="letter-spacing: -0.64px">
          Live Simulation
        </h1>
        <p class="text-sm text-[#888]">Task: {{ taskId }}</p>
      </div>
      <span
        class="px-4 py-1.5 rounded-full text-xs font-semibold inline-flex items-center gap-1.5"
        :class="statusBadge.classes"
      >
        <span
          v-if="simulationStatus === 'running'"
          class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"
        />
        {{ statusBadge.label }}
      </span>
    </div>

    <!-- Progress Bar -->
    <div class="mb-8">
      <div class="flex justify-between text-xs text-[#888] mb-1.5">
        <span>Round {{ currentRound }} of {{ totalRounds }}</span>
        <span>{{ Math.round(progressPercent) }}%</span>
      </div>
      <div class="w-full h-2 bg-black/5 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500 bg-[#2068FF]"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>

    <!-- Platform Tabs -->
    <div class="flex gap-2 mb-6">
      <button
        v-for="tab in PLATFORM_TABS"
        :key="tab.key"
        @click="activePlatform = tab.key"
        class="px-4 py-2 text-xs font-medium rounded-lg border transition-colors"
        :class="activePlatform === tab.key
          ? 'bg-[#2068FF] text-white border-[#2068FF]'
          : 'bg-white text-[#555] border-black/10 hover:border-[#2068FF]'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      <div
        v-for="card in METRIC_CARDS"
        :key="card.label"
        class="bg-white border border-black/10 rounded-lg p-4 text-center"
      >
        <div class="text-3xl font-semibold" :class="card.color">{{ card.value }}</div>
        <div class="text-xs text-[#888] mt-1">{{ card.label }}</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-4 text-center">
        <div class="text-3xl font-semibold text-[#050505]">
          {{ currentRound }}<span class="text-base text-[#888]">/{{ totalRounds }}</span>
        </div>
        <div class="text-xs text-[#888] mt-1">Current Round</div>
      </div>
    </div>

    <!-- Two Column: Feed + Chart -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
      <!-- Activity Feed -->
      <div class="lg:col-span-3 bg-white border border-black/10 rounded-lg p-6 max-h-[480px] overflow-y-auto">
        <h3 class="text-sm font-semibold text-[#050505] mb-4">Agent Activity Feed</h3>

        <div v-if="filteredActivities.length === 0" class="text-center text-[#888] py-8">
          <p class="text-sm">{{ loading ? 'Loading activity...' : 'Waiting for agent actions...' }}</p>
        </div>

        <div v-else class="space-y-2">
          <div
            v-for="(action, i) in filteredActivities"
            :key="`${action.agent_id}-${action.round_num ?? action.round}-${action.action_type}-${i}`"
            class="flex items-start gap-3 p-3 rounded-lg bg-[#fafafa] border border-black/5"
          >
            <span
              class="mt-1.5 w-2.5 h-2.5 rounded-full shrink-0"
              :class="ACTION_DOT[action.action_type] || 'bg-[#888]'"
            />
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 text-xs">
                <span class="font-semibold text-[#050505]">{{ action.agent_name }}</span>
                <span class="text-[#888]">{{ ACTION_LABEL[action.action_type] || 'acted' }}</span>
                <span class="ml-auto text-[#aaa] shrink-0 tabular-nums">
                  {{ action.platform === 'twitter' ? 'X' : 'R' }} · R{{ action.round_num ?? action.round }}
                </span>
              </div>
              <p
                v-if="action.action_args?.content"
                class="text-xs text-[#555] mt-1 line-clamp-2"
              >
                {{ action.action_args.content }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Engagement Timeline Chart -->
      <div class="lg:col-span-2 bg-white border border-black/10 rounded-lg p-6">
        <h3 class="text-sm font-semibold text-[#050505] mb-4">Engagement Timeline</h3>

        <div v-if="timelineData.length < 2" class="text-center text-[#888] py-8">
          <p class="text-sm">Chart appears after 2+ rounds</p>
        </div>

        <template v-else>
          <svg
            :viewBox="`0 0 ${CHART_W} ${CHART_H}`"
            class="w-full h-40"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="sim-area-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#2068FF" stop-opacity="0.15" />
                <stop offset="100%" stop-color="#2068FF" stop-opacity="0.02" />
              </linearGradient>
            </defs>
            <path :d="chartAreaPath" fill="url(#sim-area-fill)" />
            <path
              :d="chartLinePath"
              fill="none"
              stroke="#2068FF"
              stroke-width="2"
              vector-effect="non-scaling-stroke"
            />
          </svg>
          <div class="flex justify-between text-xs text-[#888] mt-2">
            <span>Round {{ timelineData[0]?.round }}</span>
            <span>Round {{ timelineData[timelineData.length - 1]?.round }}</span>
          </div>
        </template>
      </div>
    </div>

    <!-- Generate Report -->
    <div v-if="simulationStatus === 'completed'" class="text-center">
      <router-link
        :to="`/report/${taskId}`"
        class="inline-block bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-8 py-3 rounded-lg font-semibold transition-colors no-underline"
      >
        Generate Report
      </router-link>
    </div>
    </template>
  </div>
</template>
