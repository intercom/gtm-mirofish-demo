<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { API_BASE } from '../api/client'
import { useSimulationStore } from '../stores/simulation'
import PhaseNav from '../components/simulation/PhaseNav.vue'

const props = defineProps({ taskId: String })
const router = useRouter()
const simStore = useSimulationStore()

// --- State ---
const runStatus = ref(null)
const recentActions = ref([])
const timeline = ref([])
const activePlatform = ref('all') // 'all' | 'twitter' | 'reddit'
const pollTimer = ref(null)
const detailTimer = ref(null)
const chartCanvas = ref(null)
const error = ref(null)

// --- Computed ---
const status = computed(() => {
  const rs = runStatus.value?.runner_status
  if (!rs || rs === 'idle' || rs === 'starting') return 'building'
  if (rs === 'running' || rs === 'paused') return 'running'
  if (rs === 'completed' || rs === 'stopped') return 'completed'
  if (rs === 'failed') return 'failed'
  return 'building'
})

const statusLabel = computed(() => {
  const map = { building: 'Building', running: 'Running', completed: 'Completed', failed: 'Failed' }
  return map[status.value] || 'Unknown'
})

const statusStyle = computed(() => {
  const map = {
    building: 'bg-[#2068FF]/10 text-[#2068FF]',
    running: 'bg-emerald-100 text-emerald-700',
    completed: 'bg-[#090]/10 text-[#090]',
    failed: 'bg-red-100 text-red-700',
  }
  return map[status.value] || 'bg-gray-100 text-gray-700'
})

const statusIcon = computed(() => {
  const map = { building: '◔', running: '●', completed: '✓', failed: '✕' }
  return map[status.value] || '?'
})

const progressPercent = computed(() => runStatus.value?.progress_percent ?? 0)
const currentRound = computed(() => runStatus.value?.current_round ?? 0)
const totalRounds = computed(() => runStatus.value?.total_rounds ?? 0)
const totalActions = computed(() => runStatus.value?.total_actions_count ?? 0)
const twitterActions = computed(() => runStatus.value?.twitter_actions_count ?? 0)
const redditActions = computed(() => runStatus.value?.reddit_actions_count ?? 0)

const metrics = computed(() => {
  const actions = recentActions.value
  const filtered = activePlatform.value === 'all'
    ? actions
    : actions.filter(a => a.platform === activePlatform.value)

  let replies = 0, likes = 0, reposts = 0
  for (const a of filtered) {
    const t = a.action_type?.toUpperCase() || ''
    if (t.includes('REPLY') || t.includes('COMMENT')) replies++
    else if (t.includes('LIKE') || t.includes('UPVOTE')) likes++
    else if (t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')) reposts++
  }

  return { replies, likes, reposts }
})

const filteredActions = computed(() => {
  if (activePlatform.value === 'all') return recentActions.value
  return recentActions.value.filter(a => a.platform === activePlatform.value)
})

const platformTabs = [
  { key: 'all', label: 'Both Platforms' },
  { key: 'twitter', label: 'Twitter' },
  { key: 'reddit', label: 'Reddit' },
]

// --- API Helpers ---
async function fetchRunStatus() {
  try {
    const res = await fetch(`${API_BASE}/simulation/${props.taskId}/run-status`)
    if (!res.ok) throw new Error(`Status ${res.status}`)
    const json = await res.json()
    if (json.success) {
      runStatus.value = json.data
      simStore.updateProgress({
        progress_percent: json.data.progress_percent,
        current_round: json.data.current_round,
        total_rounds: json.data.total_rounds,
      })
      simStore.updateMetrics({
        total_actions_count: json.data.total_actions_count,
        twitter_actions_count: json.data.twitter_actions_count,
        reddit_actions_count: json.data.reddit_actions_count,
      })
    }
  } catch (e) {
    error.value = e.message
  }
}

async function fetchDetail() {
  try {
    const res = await fetch(`${API_BASE}/simulation/${props.taskId}/run-status/detail`)
    if (!res.ok) throw new Error(`Status ${res.status}`)
    const json = await res.json()
    if (json.success) {
      recentActions.value = json.data.recent_actions || json.data.all_actions || []
    }
  } catch (e) {
    // Non-critical — activity feed just won't update
  }
}

async function fetchTimeline() {
  try {
    const res = await fetch(`${API_BASE}/simulation/${props.taskId}/timeline`)
    if (!res.ok) return
    const json = await res.json()
    if (json.success) {
      timeline.value = json.data.timeline || []
      await nextTick()
      drawChart()
    }
  } catch (e) {
    // Non-critical
  }
}

// --- Chart Drawing ---
function drawChart() {
  const canvas = chartCanvas.value
  if (!canvas || !timeline.value.length) return

  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)

  const w = rect.width
  const h = rect.height
  const pad = { top: 16, right: 16, bottom: 28, left: 40 }
  const plotW = w - pad.left - pad.right
  const plotH = h - pad.top - pad.bottom

  ctx.clearRect(0, 0, w, h)

  const data = timeline.value
  const maxActions = Math.max(...data.map(d => (d.twitter_actions || 0) + (d.reddit_actions || 0)), 1)

  // Grid lines
  ctx.strokeStyle = 'rgba(0,0,0,0.06)'
  ctx.lineWidth = 1
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (plotH / 4) * i
    ctx.beginPath()
    ctx.moveTo(pad.left, y)
    ctx.lineTo(pad.left + plotW, y)
    ctx.stroke()
  }

  // Y-axis labels
  ctx.fillStyle = '#888'
  ctx.font = '10px system-ui'
  ctx.textAlign = 'right'
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (plotH / 4) * i
    const val = Math.round(maxActions * (1 - i / 4))
    ctx.fillText(val, pad.left - 6, y + 3)
  }

  // X-axis labels (show a few round numbers)
  ctx.textAlign = 'center'
  const step = Math.max(1, Math.floor(data.length / 6))
  for (let i = 0; i < data.length; i += step) {
    const x = pad.left + (i / Math.max(data.length - 1, 1)) * plotW
    ctx.fillText(`R${data[i].round_num}`, x, h - 6)
  }

  // Draw area + line for Twitter (blue)
  if (activePlatform.value !== 'reddit') {
    drawSeries(ctx, data, d => d.twitter_actions || 0, maxActions, pad, plotW, plotH, '#2068FF', 0.08)
  }
  // Draw area + line for Reddit (orange)
  if (activePlatform.value !== 'twitter') {
    drawSeries(ctx, data, d => d.reddit_actions || 0, maxActions, pad, plotW, plotH, '#ff5600', 0.08)
  }
}

function drawSeries(ctx, data, accessor, max, pad, plotW, plotH, color, fillAlpha) {
  if (data.length < 2) return

  const points = data.map((d, i) => ({
    x: pad.left + (i / (data.length - 1)) * plotW,
    y: pad.top + plotH - (accessor(d) / max) * plotH,
  }))

  // Fill area
  ctx.beginPath()
  ctx.moveTo(points[0].x, pad.top + plotH)
  points.forEach(p => ctx.lineTo(p.x, p.y))
  ctx.lineTo(points[points.length - 1].x, pad.top + plotH)
  ctx.closePath()
  const r = parseInt(color.slice(1, 3), 16)
  const g = parseInt(color.slice(3, 5), 16)
  const b = parseInt(color.slice(5, 7), 16)
  ctx.fillStyle = `rgba(${r},${g},${b},${fillAlpha})`
  ctx.fill()

  // Stroke line
  ctx.beginPath()
  points.forEach((p, i) => (i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)))
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.stroke()
}

// --- Action type display helpers ---
function actionIcon(actionType) {
  const t = (actionType || '').toUpperCase()
  if (t.includes('POST') || t.includes('CREATE')) return '📝'
  if (t.includes('REPLY') || t.includes('COMMENT')) return '💬'
  if (t.includes('LIKE') || t.includes('UPVOTE')) return '❤️'
  if (t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')) return '🔁'
  return '⚡'
}

function actionLabel(actionType) {
  const t = (actionType || '').toUpperCase()
  if (t.includes('CREATE_POST') || t.includes('CREATE_THREAD')) return 'Posted'
  if (t.includes('REPLY') || t.includes('COMMENT')) return 'Replied'
  if (t.includes('LIKE') || t.includes('UPVOTE')) return 'Liked'
  if (t.includes('REPOST') || t.includes('RETWEET')) return 'Reposted'
  if (t.includes('SHARE')) return 'Shared'
  return actionType?.replace(/_/g, ' ').toLowerCase() || 'Action'
}

function platformBadge(platform) {
  return platform === 'twitter'
    ? { label: 'Twitter', class: 'bg-[#2068FF]/10 text-[#2068FF]' }
    : { label: 'Reddit', class: 'bg-[#ff5600]/10 text-[#ff5600]' }
}

function truncate(str, len = 120) {
  if (!str || str.length <= len) return str || ''
  return str.slice(0, len) + '…'
}

// --- Polling lifecycle ---
function startPolling() {
  fetchRunStatus()
  fetchDetail()
  fetchTimeline()

  pollTimer.value = setInterval(() => {
    fetchRunStatus()
    if (status.value === 'running') fetchTimeline()
  }, 3000)

  detailTimer.value = setInterval(() => {
    fetchDetail()
  }, 5000)
}

function stopPolling() {
  if (pollTimer.value) clearInterval(pollTimer.value)
  if (detailTimer.value) clearInterval(detailTimer.value)
}

onMounted(() => {
  simStore.startRun(props.taskId)
  startPolling()
})
onUnmounted(stopPolling)

// Stop polling when simulation completes
watch(status, (val) => {
  if (val === 'completed' || val === 'failed') {
    // One final fetch then stop
    fetchDetail()
    fetchTimeline()
    stopPolling()

    if (val === 'completed') {
      simStore.complete()
      simStore.addSessionRun({
        id: props.taskId,
        scenarioName: 'GTM Simulation',
        totalRounds: totalRounds.value,
        totalActions: totalActions.value,
        twitterActions: twitterActions.value,
        redditActions: redditActions.value,
      })
    }
  }
})

// Redraw chart when platform filter changes
watch(activePlatform, () => drawChart())
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 md:px-6 py-8">
    <PhaseNav :taskId="taskId" activePhase="simulation" />

    <!-- Header -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-8">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-[#050505]">Live Simulation</h1>
        <p class="text-xs md:text-sm text-[#888] mt-1 break-all">Task: {{ taskId }}</p>
      </div>
      <span class="px-4 py-1.5 rounded-full text-xs font-semibold" :class="statusStyle">
        {{ statusIcon }} {{ statusLabel }}
      </span>
    </div>

    <!-- Progress Bar -->
    <div class="mb-6 md:mb-8">
      <div class="flex items-center justify-between text-xs text-[#888] mb-1.5">
        <span>Round {{ currentRound }} / {{ totalRounds }}</span>
        <span>{{ progressPercent }}%</span>
      </div>
      <div class="h-2 bg-black/5 rounded-full overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500 ease-out"
          :class="status === 'completed' ? 'bg-[#090]' : 'bg-[#2068FF]'"
          :style="{ width: `${progressPercent}%` }"
        />
      </div>
    </div>

    <!-- Metrics Cards -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4 mb-6 md:mb-8">
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#2068FF]">{{ totalActions }}</div>
        <div class="text-xs text-[#888] mt-1">Total Actions</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#ff5600]">{{ metrics.replies }}</div>
        <div class="text-xs text-[#888] mt-1">Replies</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#A0F]">{{ metrics.likes }}</div>
        <div class="text-xs text-[#888] mt-1">Likes</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#050505]">{{ metrics.reposts }}</div>
        <div class="text-xs text-[#888] mt-1">Reposts</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-3 md:p-4 text-center">
        <div class="text-2xl md:text-3xl font-semibold text-[#090]">{{ currentRound }}</div>
        <div class="text-xs text-[#888] mt-1">Current Round</div>
      </div>
    </div>

    <!-- Platform Tabs -->
    <div class="flex gap-1 mb-6 bg-black/5 rounded-lg p-1 w-fit">
      <button
        v-for="tab in platformTabs"
        :key="tab.key"
        class="px-4 py-1.5 text-sm rounded-md font-medium transition-colors"
        :class="activePlatform === tab.key
          ? 'bg-white text-[#050505] shadow-sm'
          : 'text-[#888] hover:text-[#555]'"
        @click="activePlatform = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Two-column layout: Chart + Activity Feed -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- Engagement Timeline Chart -->
      <div class="bg-white border border-black/10 rounded-lg p-5">
        <h3 class="text-sm font-semibold text-[#050505] mb-4">Engagement Timeline</h3>
        <div v-if="timeline.length" class="relative" style="height: 200px">
          <canvas ref="chartCanvas" class="w-full h-full" />
        </div>
        <div v-else class="flex items-center justify-center h-[200px] text-[#888] text-sm">
          <span v-if="status === 'building'">Waiting for simulation to start…</span>
          <span v-else>No timeline data yet</span>
        </div>
        <div v-if="timeline.length" class="flex items-center gap-4 mt-3 text-xs text-[#888]">
          <span v-if="activePlatform !== 'reddit'" class="flex items-center gap-1">
            <span class="inline-block w-3 h-0.5 bg-[#2068FF] rounded" /> Twitter
          </span>
          <span v-if="activePlatform !== 'twitter'" class="flex items-center gap-1">
            <span class="inline-block w-3 h-0.5 bg-[#ff5600] rounded" /> Reddit
          </span>
        </div>
      </div>

      <!-- Agent Activity Feed -->
      <div class="bg-white border border-black/10 rounded-lg p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-[#050505]">Agent Activity Feed</h3>
          <span class="text-xs text-[#888]">{{ filteredActions.length }} actions</span>
        </div>
        <div
          v-if="filteredActions.length"
          class="space-y-2 max-h-[240px] overflow-y-auto pr-1"
        >
          <div
            v-for="(action, idx) in filteredActions.slice(0, 50)"
            :key="idx"
            class="flex items-start gap-2.5 py-2 border-b border-black/5 last:border-0"
          >
            <span class="text-base mt-0.5 shrink-0">{{ actionIcon(action.action_type) }}</span>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-sm font-medium text-[#050505]">{{ action.agent_name || `Agent #${action.agent_id}` }}</span>
                <span class="text-xs px-1.5 py-0.5 rounded-full" :class="platformBadge(action.platform).class">
                  {{ platformBadge(action.platform).label }}
                </span>
                <span class="text-xs text-[#aaa]">R{{ action.round_num }}</span>
              </div>
              <p class="text-xs text-[#555] mt-0.5">
                {{ actionLabel(action.action_type) }}
                <span v-if="action.action_args?.content" class="text-[#888]">
                  — {{ truncate(action.action_args.content) }}
                </span>
              </p>
            </div>
          </div>
        </div>
        <div v-else class="flex flex-col items-center justify-center h-[200px] text-[#888]">
          <p class="text-3xl mb-2">🐦</p>
          <p class="text-sm">Real-time agent actions will appear here</p>
          <p class="text-xs mt-1 text-[#aaa]">Posts, replies, likes, and reposts from simulated agents</p>
        </div>
      </div>
    </div>

    <!-- Platform breakdown -->
    <div v-if="runStatus" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      <div class="bg-white border border-black/10 rounded-lg p-4 flex items-center gap-4">
        <div class="w-10 h-10 rounded-lg bg-[#2068FF]/10 flex items-center justify-center text-lg">𝕏</div>
        <div class="flex-1">
          <div class="text-sm font-medium text-[#050505]">Twitter</div>
          <div class="text-xs text-[#888]">
            {{ twitterActions }} actions · Round {{ runStatus.twitter_current_round || 0 }}
            <span v-if="runStatus.twitter_completed" class="text-[#090]"> · Done</span>
          </div>
        </div>
        <div class="text-2xl font-semibold text-[#2068FF]">{{ twitterActions }}</div>
      </div>
      <div class="bg-white border border-black/10 rounded-lg p-4 flex items-center gap-4">
        <div class="w-10 h-10 rounded-lg bg-[#ff5600]/10 flex items-center justify-center text-lg">📢</div>
        <div class="flex-1">
          <div class="text-sm font-medium text-[#050505]">Reddit</div>
          <div class="text-xs text-[#888]">
            {{ redditActions }} actions · Round {{ runStatus.reddit_current_round || 0 }}
            <span v-if="runStatus.reddit_completed" class="text-[#090]"> · Done</span>
          </div>
        </div>
        <div class="text-2xl font-semibold text-[#ff5600]">{{ redditActions }}</div>
      </div>
    </div>

    <!-- Error display -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-8 text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Generate Report Button -->
    <Transition name="page">
      <div v-if="status === 'completed'" class="text-center mt-8">
        <router-link
          :to="`/report/${taskId}`"
          class="inline-block bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-8 py-3 rounded-lg font-semibold transition-colors no-underline"
        >
          Generate Report →
        </router-link>
      </div>
    </Transition>
  </div>
</template>
