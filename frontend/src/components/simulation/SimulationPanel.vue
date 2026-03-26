<script setup>
import { ref, computed, inject, watch, nextTick, onMounted, onUnmounted } from 'vue'
import ShimmerCard from '../ui/ShimmerCard.vue'
import SentimentTimeline from './SentimentTimeline.vue'
import { useCountUp } from '../../composables/useCountUp'
import { useStaggerAnimation } from '../../composables/useStaggerAnimation'
import TimelineEventMarkers from './TimelineEventMarkers.vue'
import AgentMoodIndicator from './AgentMoodIndicator.vue'
import BehaviorPatterns from './BehaviorPatterns.vue'
import CollaborationIndicator from './CollaborationIndicator.vue'
import LiveMetrics from './LiveMetrics.vue'
import PredictionDashboard from './PredictionDashboard.vue'
import SyncedChart from '../timeline/SyncedChart.vue'
import MultiMetricView from './MultiMetricView.vue'
import BeliefEvolution from './BeliefEvolution.vue'
import LiveFeed from './LiveFeed.vue'
import RichTextEditor from '../common/RichTextEditor.vue'
import { useSimulationStream } from '../../composables/useSimulationStream'
import { useTransparency } from '../../composables/useTransparency'
import InfluenceFlow from './InfluenceFlow.vue'
import SentimentArc from './SentimentArc.vue'
import RelationshipNetwork from './RelationshipNetwork.vue'
import { useRelationshipsStore } from '../../stores/relationships'
import AnomalyHighlights from './AnomalyHighlights.vue'
import AgentSentimentTimeline from './AgentSentimentTimeline.vue'
import KnowledgeTimeline from './KnowledgeTimeline.vue'
import AgentJourneySankey from './AgentJourneySankey.vue'

const props = defineProps({
  taskId: { type: String, required: true },
})

const polling = inject('polling')
const simShortcuts = inject('simShortcuts', null)
const { showThinking, hasAgentFilter, toggleThinking, toggleAgent, isAgentTransparent, clearAgentFilter } = useTransparency()
const relationshipsStore = useRelationshipsStore()

const activePlatform = ref('all')
const chartViewMode = ref('detail') // 'detail' | 'overview'
const chartCanvas = ref(null)
const heartbeatCanvas = ref(null)
const selectedAgent = ref(null)
const agentBackstories = ref({})
const editingBackstory = ref(false)

const {
  onBeforeEnter: agentBeforeEnter,
  onEnter: agentEnter,
  onLeave: agentLeave,
  reset: resetAgentStagger,
} = useStaggerAnimation({ delay: 40, duration: 250, distance: 8 })
watch(selectedAgent, () => resetAgentStagger())

// SSE live feed stream — merges with polling data for the LiveFeed component
const stream = useSimulationStream(() => props.taskId)

const feedActions = computed(() => {
  // Prefer SSE events when connected; fall back to polling data
  if (stream.events.value.length > 0) return stream.events.value
  return polling.recentActions.value
})

const feedConnectionStatus = computed(() => {
  if (stream.status.value === 'connected') return 'connected'
  if (stream.status.value === 'connecting') return 'connecting'
  if (stream.status.value === 'done') return 'done'
  if (stream.status.value === 'error') return 'error'
  if (polling.recentActions.value.length > 0) return 'polling'
  return 'disconnected'
})

let resizeObserver = null
let heartbeatAnimId = null

const status = computed(() => {
  const rs = polling.runStatus.value?.runner_status
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
    building: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]',
    running: 'bg-[var(--color-success-light)] text-[var(--color-success)]',
    completed: 'bg-[var(--color-success-light)] text-[var(--color-success)]',
    failed: 'bg-[var(--color-error-light)] text-[var(--color-error)]',
  }
  return map[status.value] || 'bg-[var(--color-tint)] text-[var(--color-text-secondary)]'
})

const statusIcon = computed(() => {
  const map = { building: '\u25D4', running: '\u25CF', completed: '\u2713', failed: '\u2715' }
  return map[status.value] || '?'
})

const progressPercent = computed(() => polling.runStatus.value?.progress_percent ?? 0)
const currentRound = computed(() => polling.runStatus.value?.current_round ?? 0)
const totalRounds = computed(() => polling.runStatus.value?.total_rounds ?? 0)
const totalActions = computed(() => polling.runStatus.value?.total_actions_count ?? 0)
const twitterActions = computed(() => polling.runStatus.value?.twitter_actions_count ?? 0)
const redditActions = computed(() => polling.runStatus.value?.reddit_actions_count ?? 0)

// Animated metric displays
const animatedTotalActions = useCountUp(totalActions, { duration: 600 })
const animatedCurrentRound = useCountUp(currentRound, { duration: 400 })
const animatedProgress = useCountUp(progressPercent, { duration: 400 })
const animatedTwitterActions = useCountUp(twitterActions, { duration: 600 })
const animatedRedditActions = useCountUp(redditActions, { duration: 600 })

const metrics = computed(() => {
  const actions = polling.recentActions.value
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

const animatedReplies = useCountUp(() => metrics.value.replies, { duration: 600 })
const animatedLikes = useCountUp(() => metrics.value.likes, { duration: 600 })
const animatedReposts = useCountUp(() => metrics.value.reposts, { duration: 600 })

// Agent panel animated stats
const animatedAgentTotal = useCountUp(() => selectedAgent.value?.totalActions ?? 0, { duration: 500 })
const animatedAgentTwitter = useCountUp(() => selectedAgent.value?.twitterActions ?? 0, { duration: 500 })
const animatedAgentReddit = useCountUp(() => selectedAgent.value?.redditActions ?? 0, { duration: 500 })

const filteredActions = computed(() => {
  if (activePlatform.value === 'all') return feedActions.value
  return feedActions.value.filter(a => a.platform === activePlatform.value)
})

const actionRounds = computed(() => {
  const rounds = new Set()
  for (const a of filteredActions.value) {
    if (a.round_num != null) rounds.add(a.round_num)
  }
  return Array.from(rounds).sort((a, b) => a - b)
})

const platformTabs = [
  { key: 'all', label: 'Both Platforms' },
  { key: 'twitter', label: 'Twitter' },
  { key: 'reddit', label: 'Reddit' },
]

// --- Heartbeat sparkline during build phase ---
function startHeartbeat() {
  const canvas = heartbeatCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  if (!rect.width || !rect.height) return

  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)

  const w = rect.width
  const h = rect.height
  let offset = 0

  function draw() {
    ctx.clearRect(0, 0, w, h)
    ctx.beginPath()

    const midY = h / 2
    const amp = h * 0.3
    const freq = 0.02
    const speed = 1.5

    for (let x = 0; x < w; x++) {
      const t = (x + offset) * freq
      const y = midY + Math.sin(t) * amp * (0.6 + 0.4 * Math.sin(t * 0.3))
      if (x === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }

    ctx.strokeStyle = 'rgba(32, 104, 255, 0.35)'
    ctx.lineWidth = 2
    ctx.stroke()

    // Glow effect
    ctx.beginPath()
    for (let x = 0; x < w; x++) {
      const t = (x + offset) * freq
      const y = midY + Math.sin(t) * amp * (0.6 + 0.4 * Math.sin(t * 0.3))
      if (x === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.strokeStyle = 'rgba(32, 104, 255, 0.1)'
    ctx.lineWidth = 6
    ctx.stroke()

    offset += speed
    heartbeatAnimId = requestAnimationFrame(draw)
  }

  heartbeatAnimId = requestAnimationFrame(draw)
}

function stopHeartbeat() {
  if (heartbeatAnimId) {
    cancelAnimationFrame(heartbeatAnimId)
    heartbeatAnimId = null
  }
}

// Start/stop heartbeat based on build status
watch(() => polling.graphStatus.value, (val) => {
  if (val === 'building') {
    nextTick(() => startHeartbeat())
  } else {
    stopHeartbeat()
  }
})

// --- Chart Drawing ---
let chartRetryTimer = null

function drawChart() {
  const canvas = chartCanvas.value
  if (!canvas || !polling.timeline.value.length) return

  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()

  // Canvas may have zero dimensions when tab is hidden (v-show) — retry
  if (rect.width === 0 || rect.height === 0) {
    if (chartRetryTimer) clearTimeout(chartRetryTimer)
    chartRetryTimer = setTimeout(drawChart, 300)
    return
  }

  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)

  const w = rect.width
  const h = rect.height
  const pad = { top: 16, right: 16, bottom: 28, left: 40 }
  const plotW = w - pad.left - pad.right
  const plotH = h - pad.top - pad.bottom

  ctx.clearRect(0, 0, w, h)

  const data = polling.timeline.value
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
  ctx.fillStyle = 'var(--color-text-muted, #888)'
  ctx.font = '10px system-ui'
  ctx.textAlign = 'right'
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (plotH / 4) * i
    const val = Math.round(maxActions * (1 - i / 4))
    ctx.fillText(val, pad.left - 6, y + 3)
  }

  // X-axis labels
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
  if (t.includes('POST') || t.includes('CREATE')) return '\uD83D\uDCDD'
  if (t.includes('REPLY') || t.includes('COMMENT')) return '\uD83D\uDCAC'
  if (t.includes('LIKE') || t.includes('UPVOTE')) return '\u2764\uFE0F'
  if (t.includes('REPOST') || t.includes('RETWEET') || t.includes('SHARE')) return '\uD83D\uDD01'
  return '\u26A1'
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
    ? { label: 'Twitter', class: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]' }
    : { label: 'Reddit', class: 'bg-[var(--color-fin-orange-tint)] text-[var(--color-fin-orange)]' }
}

function truncate(str, len = 120) {
  if (!str || str.length <= len) return str || ''
  return str.slice(0, len) + '\u2026'
}

function formatTimestamp(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ts
  }
}

function selectAgent(action) {
  const agentActions = feedActions.value.filter(
    a => a.agent_name === action.agent_name
  )
  const twitterCount = agentActions.filter(a => a.platform === 'twitter').length
  const redditCount = agentActions.filter(a => a.platform === 'reddit').length

  const parts = action.agent_name?.split(', ') || []
  const name = parts[0] || action.agent_name || `Agent #${action.agent_id}`
  const roleParts = (parts[1] || '').split(' @ ')
  const role = roleParts[0] || ''
  const company = roleParts[1] || ''

  editingBackstory.value = false
  selectedAgent.value = {
    id: action.agent_id,
    name,
    fullName: action.agent_name,
    role,
    company,
    totalActions: agentActions.length,
    twitterActions: twitterCount,
    redditActions: redditCount,
    actions: agentActions.slice(0, 20),
    sentiment: twitterCount + redditCount > 5 ? 'Engaged' : 'Moderate',
    backstory: agentBackstories.value[action.agent_id] || '',
  }
}

function updateBackstory(html) {
  if (!selectedAgent.value) return
  selectedAgent.value.backstory = html
  agentBackstories.value[selectedAgent.value.id] = html
}

// Connect SSE stream when simulation starts running
watch(status, (val) => {
  if (val === 'running') {
    stream.connect()
  } else if (val === 'completed' || val === 'failed') {
    stream.disconnect()
  }
})

// --- Auto-scroll for activity feed ---
function onFeedScroll() {
  const el = feedContainer.value
  if (!el) return
  autoScroll.value = (el.scrollHeight - el.scrollTop - el.clientHeight) < 50
}

watch(() => polling.recentActions.value.length, () => {
  if (autoScroll.value && feedContainer.value) {
    nextTick(() => {
      feedContainer.value.scrollTop = feedContainer.value.scrollHeight
    })
  }
})

// Fetch relationship data when actions accumulate or simulation completes
let relFetchTimer = null
watch(() => polling.recentActions.value.length, (len) => {
  if (len > 0 && len % 20 === 0) {
    clearTimeout(relFetchTimer)
    relFetchTimer = setTimeout(() => {
      relationshipsStore.fetchRelationships(props.taskId)
    }, 500)
  }
})
watch(() => polling.simStatus.value, (val) => {
  if (val === 'completed') {
    relationshipsStore.fetchRelationships(props.taskId)
  }
})

// Redraw chart when timeline updates
watch(() => polling.timeline.value, () => {
  nextTick(() => drawChart())
}, { deep: true })

// Redraw chart when platform filter changes
watch(activePlatform, () => drawChart())

onMounted(() => {
  const canvasContainer = chartCanvas.value?.parentElement
  if (canvasContainer) {
    resizeObserver = new ResizeObserver(() => {
      drawChart()
    })
    resizeObserver.observe(canvasContainer)
  }
  if (polling.graphStatus.value === 'building') {
    nextTick(() => startHeartbeat())
  }
  // Connect SSE if simulation is already running
  if (status.value === 'running') {
    stream.connect()
  }
  // Fetch relationships for existing/completed simulations
  if (props.taskId) {
    relationshipsStore.fetchRelationships(props.taskId)
  }
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (chartRetryTimer) clearTimeout(chartRetryTimer)
  if (relFetchTimer) clearTimeout(relFetchTimer)
  stopHeartbeat()
  stream.disconnect()
})
</script>

<template>
  <div class="h-full overflow-y-auto">
    <div class="max-w-6xl mx-auto px-4 md:px-6 py-6">

      <!-- Empty state when graph is building -->
      <div
        v-if="polling.graphStatus.value === 'building' && status === 'building'"
        class="flex flex-col items-center justify-center py-20"
      >
        <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mb-5">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="6" cy="6" r="2" />
            <circle cx="18" cy="6" r="2" />
            <circle cx="6" cy="18" r="2" />
            <circle cx="18" cy="18" r="2" />
            <circle cx="12" cy="12" r="2" />
            <line x1="7.8" y1="7" x2="10.5" y2="10.5" />
            <line x1="13.5" y1="10.5" x2="16.2" y2="7" />
            <line x1="7.8" y1="17" x2="10.5" y2="13.5" />
            <line x1="13.5" y1="13.5" x2="16.2" y2="17" />
          </svg>
        </div>
        <h2 class="text-base font-semibold text-[var(--color-text)] mb-2">Preparing Simulation</h2>
        <p class="text-sm text-[var(--color-text-secondary)] text-center max-w-sm">
          Simulation will begin once the knowledge graph is ready. Switch to the Graph tab to watch the build progress.
        </p>

        <!-- Heartbeat sparkline during build -->
        <div class="mt-8 w-full max-w-md">
          <canvas ref="heartbeatCanvas" class="w-full" style="height: 60px" />
        </div>
      </div>

      <!-- Main content -->
      <template v-else>

        <!-- Header -->
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-8">
          <div>
            <h1 class="text-xl md:text-2xl font-semibold text-[var(--color-text)]">Live Simulation</h1>
            <p class="text-xs md:text-sm text-[var(--color-text-muted)] mt-1 break-all">Task: {{ taskId }}</p>
          </div>
          <span class="px-4 py-1.5 rounded-full text-xs font-semibold" :class="statusStyle">
            {{ statusIcon }} {{ statusLabel }}
          </span>
        </div>

        <!-- Progress Bar -->
        <div class="mb-6 md:mb-8">
          <div class="flex items-center justify-between text-xs text-[var(--color-text-muted)] mb-1.5">
            <span>Round {{ animatedCurrentRound }} / {{ totalRounds }}</span>
            <span>{{ animatedProgress }}%</span>
          </div>
          <div class="h-2 bg-[var(--color-tint)] rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500 ease-out"
              :class="status === 'completed' ? 'bg-[var(--color-success)]' : 'bg-[var(--color-primary)]'"
              :style="{ width: `${progressPercent}%` }"
            />
          </div>
        </div>

        <!-- Shimmer loading state for metrics -->
        <div v-if="!polling.runStatus.value && status === 'building' && (!simShortcuts || simShortcuts.showMetrics.value)" class="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4 mb-6 md:mb-8">
          <ShimmerCard v-for="i in 5" :key="i" :lines="2" height="80px" />
        </div>

        <!-- Metrics Cards -->
        <div v-else-if="!simShortcuts || simShortcuts.showMetrics.value" class="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4 mb-6 md:mb-8">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-center">
            <div class="text-2xl md:text-3xl font-semibold text-[var(--color-primary)]">{{ animatedTotalActions }}</div>
            <div class="text-xs text-[var(--color-text-muted)] mt-1">Total Actions</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-center">
            <div class="text-2xl md:text-3xl font-semibold text-[var(--color-fin-orange)]">{{ animatedReplies }}</div>
            <div class="text-xs text-[var(--color-text-muted)] mt-1">Replies</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-center">
            <div class="text-2xl md:text-3xl font-semibold text-[var(--color-accent)]">{{ animatedLikes }}</div>
            <div class="text-xs text-[var(--color-text-muted)] mt-1">Likes</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-center">
            <div class="text-2xl md:text-3xl font-semibold text-[var(--color-text)]">{{ animatedReposts }}</div>
            <div class="text-xs text-[var(--color-text-muted)] mt-1">Reposts</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-center">
            <div class="text-2xl md:text-3xl font-semibold text-[var(--color-success)]">{{ animatedCurrentRound }}</div>
            <div class="text-xs text-[var(--color-text-muted)] mt-1">Current Round</div>
          </div>
        </div>

        <!-- Platform Tabs -->
        <div class="flex gap-1 mb-6 bg-[var(--color-tint)] rounded-lg p-1 w-fit">
          <button
            v-for="tab in platformTabs"
            :key="tab.key"
            class="px-4 py-1.5 text-sm rounded-md font-medium transition-colors"
            :class="activePlatform === tab.key
              ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
              : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
            @click="activePlatform = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Collaboration Indicator -->
        <CollaborationIndicator class="mb-6" />

        <!-- View mode toggle -->
        <div class="flex items-center justify-between mb-6">
          <div class="flex gap-1 bg-[var(--color-tint)] rounded-lg p-1">
            <button
              class="px-3 py-1 text-xs rounded-md font-medium transition-colors"
              :class="chartViewMode === 'detail'
                ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
              @click="chartViewMode = 'detail'"
            >
              Detail
            </button>
            <button
              class="px-3 py-1 text-xs rounded-md font-medium transition-colors"
              :class="chartViewMode === 'overview'
                ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
                : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
              @click="chartViewMode = 'overview'"
            >
              Overview
            </button>
          </div>
        </div>

        <!-- Multi-Metric Overview (when in overview mode) -->
        <MultiMetricView
          v-if="chartViewMode === 'overview'"
          :timeline="polling.timeline.value"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Two-column layout: Chart + Activity Feed (detail mode) -->
        <div v-if="chartViewMode === 'detail'" class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <!-- Engagement Timeline Chart -->
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
            <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Engagement Timeline</h3>
            <SyncedChart :pad-left="40" :pad-right="16">
              <div v-if="polling.timeline.value.length" class="relative" style="height: 200px">
                <canvas ref="chartCanvas" class="w-full h-full" />
              </div>
              <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
                <span v-if="status === 'building'">Waiting for simulation to start...</span>
                <span v-else>No timeline data yet</span>
              </div>
            </SyncedChart>
            <div v-if="polling.timeline.value.length" class="flex items-center gap-4 mt-3 text-xs text-[var(--color-text-muted)]">
              <span v-if="activePlatform !== 'reddit'" class="flex items-center gap-1">
                <span class="inline-block w-3 h-0.5 bg-[var(--color-primary)] rounded" /> Twitter
              </span>
              <span v-if="activePlatform !== 'twitter'" class="flex items-center gap-1">
                <span class="inline-block w-3 h-0.5 bg-[var(--color-fin-orange)] rounded" /> Reddit
              </span>
            </div>
          </div>

          <!-- Live Agent Activity Feed -->
          <LiveFeed
            :actions="feedActions"
            :connection-status="feedConnectionStatus"
            :show-thinking="showThinking"
            :has-agent-filter="hasAgentFilter"
            :is-agent-transparent="isAgentTransparent"
            :llm-model="polling.runStatus.value?.llm_model"
            :llm-provider="polling.runStatus.value?.llm_provider"
            @select-agent="selectAgent"
            @toggle-thinking="toggleThinking"
            @toggle-agent="toggleAgent"
            @clear-agent-filter="clearAgentFilter"
          />
        </div>

        <!-- Sentiment Timeline (detail mode only) -->
        <SyncedChart
          v-if="chartViewMode === 'detail' && filteredActions.length > 0"
          :pad-left="56"
          :pad-right="36"
          class="mb-8"
        >
          <SentimentTimeline
            :actions="filteredActions"
            :timeline="polling.timeline.value"
          />
        </SyncedChart>

        <!-- Timeline Event Markers -->
        <TimelineEventMarkers
          v-if="polling.timeline.value.length > 0"
          :timeline="polling.timeline.value"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Behavior Patterns -->
        <BehaviorPatterns
          v-if="filteredActions.length > 0"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Agent Journey Sankey -->
        <AgentJourneySankey
          v-if="filteredActions.length > 0"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Per-agent sentiment breakdown -->
        <AgentSentimentTimeline
          v-if="filteredActions.length > 0"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Behavior Anomalies -->
        <AnomalyHighlights
          v-if="filteredActions.length > 0"
          :simulationId="taskId"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Sentiment Arc (per-agent narrative) -->
        <SentimentArc
          :simulation-id="props.taskId"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Influence Flow -->
        <InfluenceFlow
          v-if="filteredActions.length > 0"
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Agent Relationships -->
        <RelationshipNetwork
          v-if="relationshipsStore.hasData || filteredActions.length > 0"
          :agents="relationshipsStore.agents"
          :relationships="relationshipsStore.relationships"
          :alliances="relationshipsStore.alliances"
          :conflicts="relationshipsStore.conflicts"
          :isDemo="relationshipsStore.isDemo"
          :loading="relationshipsStore.loading"
          class="mb-8"
        />

        <!-- Belief Evolution -->
        <BeliefEvolution
          :actions="filteredActions"
          class="mb-8"
        />

        <!-- Knowledge Timeline -->
        <KnowledgeTimeline
          v-if="polling.knowledgeTimeline.value?.timeline?.length > 0"
          :data="polling.knowledgeTimeline.value"
          class="mb-8"
        />

        <!-- Live Metrics Dashboard -->
        <LiveMetrics class="mb-8" />

        <!-- Prediction Dashboard -->
        <PredictionDashboard
          v-if="filteredActions.length > 0"
          :actions="filteredActions"
          :currentRound="currentRound"
          :totalRounds="totalRounds"
          class="mb-8"
        />
        <!-- Platform breakdown -->
        <div v-if="polling.runStatus.value" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 flex items-center gap-4">
            <div class="w-10 h-10 rounded-lg bg-[rgba(32,104,255,0.1)] flex items-center justify-center">
              <svg class="w-5 h-5" viewBox="0 0 24 24" fill="var(--color-primary)"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            </div>
            <div class="flex-1">
              <div class="text-sm font-medium text-[var(--color-text)]">Twitter</div>
              <div class="text-xs text-[var(--color-text-muted)]">
                {{ animatedTwitterActions }} actions &middot; Round {{ polling.runStatus.value.twitter_current_round || 0 }}
                <span v-if="polling.runStatus.value.twitter_completed" class="text-[var(--color-success)]"> &middot; Done</span>
              </div>
            </div>
            <div class="text-2xl font-semibold text-[var(--color-primary)]">{{ animatedTwitterActions }}</div>
          </div>
          <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 flex items-center gap-4">
            <div class="w-10 h-10 rounded-lg bg-[var(--color-fin-orange-tint)] flex items-center justify-center text-lg">&#x1F4E2;</div>
            <div class="flex-1">
              <div class="text-sm font-medium text-[var(--color-text)]">Reddit</div>
              <div class="text-xs text-[var(--color-text-muted)]">
                {{ animatedRedditActions }} actions &middot; Round {{ polling.runStatus.value.reddit_current_round || 0 }}
                <span v-if="polling.runStatus.value.reddit_completed" class="text-[var(--color-success)]"> &middot; Done</span>
              </div>
            </div>
            <div class="text-2xl font-semibold text-[var(--color-fin-orange)]">{{ animatedRedditActions }}</div>
          </div>
        </div>

        <!-- Error display -->
        <div
          v-if="polling.simStatus.value?.error"
          class="bg-[var(--color-error-light)] border border-[var(--color-error)] rounded-lg p-4 mb-8 text-sm text-[var(--color-error)]"
        >
          {{ polling.simStatus.value.error }}
        </div>

        <!-- Generate Report Button -->
        <Transition name="fade">
          <div v-if="status === 'completed'" class="text-center mt-8">
            <router-link
              :to="`/report/${taskId}`"
              class="inline-block bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-[var(--color-text-inverse)] px-8 py-3 rounded-lg font-semibold transition-colors no-underline"
            >
              Generate Report &rarr;
            </router-link>
          </div>
        </Transition>

      </template>
    </div>

    <!-- Overlay when agent panel is open -->
    <Transition name="modal-overlay">
      <div
        v-if="selectedAgent"
        class="fixed inset-0 z-40 bg-black/20 backdrop-blur-[1px]"
        @click="selectedAgent = null"
      />
    </Transition>

    <!-- Agent Detail Panel -->
    <Transition name="panel-right">
      <div
        v-if="selectedAgent"
        class="fixed top-0 right-0 z-50 h-full w-96 max-w-[90vw] bg-[var(--color-surface)] border-l border-[var(--color-border)] shadow-xl overflow-y-auto"
      >
        <div class="p-5">
          <!-- Header -->
          <div class="flex items-start justify-between mb-5">
            <div>
              <h3 class="text-base font-semibold text-[var(--color-text)]">{{ selectedAgent.name }}</h3>
              <p v-if="selectedAgent.role" class="text-xs text-[var(--color-text-muted)] mt-0.5">
                {{ selectedAgent.role }}
                <span v-if="selectedAgent.company"> @ {{ selectedAgent.company }}</span>
              </p>
            </div>
            <button @click="selectedAgent = null" class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-lg leading-none">&times;</button>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-3 gap-3 mb-5">
            <div class="bg-[var(--color-tint)] rounded-lg p-3 text-center">
              <div class="text-lg font-semibold text-[var(--color-text)]">{{ animatedAgentTotal }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)]">Actions</div>
            </div>
            <div class="bg-[rgba(32,104,255,0.06)] rounded-lg p-3 text-center">
              <div class="text-lg font-semibold text-[var(--color-primary)]">{{ animatedAgentTwitter }}</div>
              <div class="text-[10px] text-[var(--color-primary)]">Twitter</div>
            </div>
            <div class="bg-[rgba(255,86,0,0.06)] rounded-lg p-3 text-center">
              <div class="text-lg font-semibold text-[#ff5600]">{{ animatedAgentReddit }}</div>
              <div class="text-[10px] text-[#ff5600]">Reddit</div>
            </div>
          </div>

          <!-- Agent Mood -->
          <div class="mb-5">
            <AgentMoodIndicator
              :actions="polling.recentActions.value"
              :agent-name="selectedAgent.fullName"
              size="large"
            />
          </div>

          <!-- Backstory -->
          <div class="mb-5">
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider">Backstory</h4>
              <button
                @click="editingBackstory = !editingBackstory"
                class="text-[11px] font-medium text-[var(--color-primary)] hover:underline"
              >
                {{ editingBackstory ? 'Done' : (selectedAgent.backstory ? 'Edit' : 'Add') }}
              </button>
            </div>
            <RichTextEditor
              v-if="editingBackstory"
              :model-value="selectedAgent.backstory"
              @update:model-value="updateBackstory"
              placeholder="Describe this agent's background, experience, and perspective..."
              :char-limit="500"
            />
            <div
              v-else-if="selectedAgent.backstory"
              class="text-xs text-[var(--color-text-secondary)] leading-relaxed"
              v-html="selectedAgent.backstory"
            />
            <p v-else class="text-xs text-[var(--color-text-muted)] italic">
              No backstory yet
            </p>
          </div>

          <!-- Action history -->
          <div>
            <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Recent Activity</h4>
            <TransitionGroup
              tag="div"
              class="space-y-2"
              :css="false"
              appear
              @before-enter="agentBeforeEnter"
              @enter="agentEnter"
              @leave="agentLeave"
            >
              <div
                v-for="(action, idx) in selectedAgent.actions"
                :key="`${selectedAgent.id}-${idx}`"
                :data-index="idx"
                class="flex items-start gap-2 py-2 border-b border-[var(--color-border)] last:border-0"
              >
                <span class="text-sm mt-0.5 shrink-0">{{ actionIcon(action.action_type) }}</span>
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2">
                    <span class="text-xs px-1.5 py-0.5 rounded-full" :class="platformBadge(action.platform).class">
                      {{ platformBadge(action.platform).label }}
                    </span>
                    <span class="text-[10px] text-[var(--color-text-muted)]">R{{ action.round_num }}</span>
                  </div>
                  <p class="text-xs text-[var(--color-text-secondary)] mt-1">
                    {{ actionLabel(action.action_type) }}
                    <span v-if="action.action_args?.content" class="text-[var(--color-text-muted)]">
                      &mdash; {{ truncate(action.action_args.content, 100) }}
                    </span>
                  </p>
                </div>
              </div>
            </TransitionGroup>
          </div>

          <!-- View Full Profile link -->
          <div class="mt-6 pt-4 border-t border-[var(--color-border)]">
            <router-link
              :to="`/workspace/${taskId}/agent/${selectedAgent.id}?name=${encodeURIComponent(selectedAgent.fullName)}`"
              class="flex items-center justify-center gap-2 w-full bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white text-sm font-medium py-2.5 rounded-lg transition-colors no-underline"
            >
              View Full Profile &rarr;
            </router-link>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-right-enter-active, .slide-right-leave-active {
  transition: transform 0.25s ease;
}
.slide-right-enter-from, .slide-right-leave-to {
  transform: translateX(100%);
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
