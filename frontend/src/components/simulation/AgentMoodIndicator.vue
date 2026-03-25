<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  score: { type: Number, default: null },
  actions: { type: Array, default: () => [] },
  agentName: { type: String, default: '' },
  size: { type: String, default: 'compact', validator: v => ['compact', 'large'].includes(v) },
})

// --- Sentiment scoring (same word lists as SentimentTimeline) ---

const POSITIVE_WORDS = [
  'impressive', 'compelling', 'great', 'interested', 'good', 'recommend',
  'valuable', 'effective', 'worth', 'excellent', 'innovative', 'benefit',
  'advantage', 'better', 'love', 'amazing', 'helpful', 'promising',
  'exciting', 'confident', 'strong', 'pleased', 'significant', 'positive',
]

const NEGATIVE_WORDS = [
  'concerned', 'skeptical', 'aggressive', 'missing', 'risk', 'worried',
  'expensive', 'complex', 'difficult', 'dismiss', 'doubt', 'issue',
  'problem', 'unclear', 'confusing', 'frustrated', 'poor', 'slow',
  'lacks', 'overpriced', 'clunky', 'limited', 'negative', 'afraid',
]

function scoreSentiment(content) {
  if (!content) return 0
  const lower = content.toLowerCase()
  let pos = 0, neg = 0
  for (const w of POSITIVE_WORDS) { if (lower.includes(w)) pos++ }
  for (const w of NEGATIVE_WORDS) { if (lower.includes(w)) neg++ }
  if (pos + neg === 0) return 0
  return (pos - neg) / (pos + neg)
}

// --- Mood computation (1–10 scale) ---

const moodScore = computed(() => {
  if (props.score != null) return Math.max(1, Math.min(10, Math.round(props.score)))
  if (!props.actions.length) return 5

  const filtered = props.agentName
    ? props.actions.filter(a => a.agent_name === props.agentName)
    : props.actions
  if (!filtered.length) return 5

  const scores = filtered.map(a => scoreSentiment(a.action_args?.content))
  const avg = scores.reduce((s, v) => s + v, 0) / scores.length
  return Math.max(1, Math.min(10, Math.round((avg + 1) * 4.5 + 1)))
})

const mood = computed(() => {
  const s = moodScore.value
  if (s <= 2) return { key: 'angry', label: 'Frustrated', color: '#dc2626', bg: 'rgba(220,38,38,0.12)' }
  if (s <= 4) return { key: 'worried', label: 'Skeptical', color: '#ff5600', bg: 'rgba(255,86,0,0.12)' }
  if (s <= 6) return { key: 'neutral', label: 'Neutral', color: '#6b7280', bg: 'rgba(107,114,128,0.12)' }
  if (s <= 8) return { key: 'pleased', label: 'Engaged', color: '#22c55e', bg: 'rgba(34,197,94,0.12)' }
  return { key: 'excited', label: 'Enthusiastic', color: '#009900', bg: 'rgba(0,153,0,0.12)' }
})

// --- SVG face expressions ---

const face = computed(() => {
  const s = moodScore.value
  if (s <= 2) return {
    brows: [{ x1: 28, y1: 32, x2: 40, y2: 38 }, { x1: 72, y1: 32, x2: 60, y2: 38 }],
    eyes: [{ cx: 36, cy: 44, r: 3.5 }, { cx: 64, cy: 44, r: 3.5 }],
    mouth: 'M 32 72 Q 50 60, 68 72',
  }
  if (s <= 4) return {
    brows: [{ x1: 30, y1: 36, x2: 40, y2: 33 }, { x1: 70, y1: 36, x2: 60, y2: 33 }],
    eyes: [{ cx: 37, cy: 44, r: 3.5 }, { cx: 63, cy: 44, r: 3.5 }],
    mouth: 'M 34 70 Q 50 63, 66 70',
  }
  if (s <= 6) return {
    eyes: [{ cx: 37, cy: 42, r: 4 }, { cx: 63, cy: 42, r: 4 }],
    mouth: 'M 36 66 L 64 66',
  }
  if (s <= 8) return {
    eyes: [{ cx: 37, cy: 42, r: 4 }, { cx: 63, cy: 42, r: 4 }],
    mouth: 'M 34 62 Q 50 76, 66 62',
  }
  return {
    eyes: [{ cx: 37, cy: 40, r: 5 }, { cx: 63, cy: 40, r: 5 }],
    mouth: 'M 30 60 Q 50 80, 70 60',
  }
})

// --- Pulse animation on mood change ---

const isPulsing = ref(false)
let pulseTimer = null

watch(moodScore, (newVal, oldVal) => {
  if (oldVal != null && newVal !== oldVal) {
    isPulsing.value = true
    clearTimeout(pulseTimer)
    pulseTimer = setTimeout(() => { isPulsing.value = false }, 600)
  }
})

// --- History popover (Teleported to body to avoid overflow clipping) ---

const showHistory = ref(false)
const faceRef = ref(null)
const popoverRef = ref(null)
const sparklineRef = ref(null)
const popoverPos = ref({ left: '0px', top: '0px' })

const sentimentHistory = computed(() => {
  if (!props.actions.length || !props.agentName) return []
  const byRound = new Map()
  for (const a of props.actions) {
    if (a.agent_name !== props.agentName || a.round_num == null) continue
    if (!byRound.has(a.round_num)) byRound.set(a.round_num, [])
    byRound.get(a.round_num).push(scoreSentiment(a.action_args?.content))
  }
  return Array.from(byRound.entries())
    .sort(([a], [b]) => a - b)
    .map(([round, scores]) => ({
      round,
      score: scores.reduce((s, v) => s + v, 0) / scores.length,
    }))
})

function toggleHistory(e) {
  e.stopPropagation()
  if (!sentimentHistory.value.length) return
  showHistory.value = !showHistory.value
  if (showHistory.value) {
    const rect = e.currentTarget.getBoundingClientRect()
    const popW = 190
    const popH = 110
    const showAbove = rect.bottom + popH + 8 > window.innerHeight
    popoverPos.value = {
      left: `${Math.max(8, Math.min(window.innerWidth - popW - 8, rect.left + rect.width / 2 - popW / 2))}px`,
      top: showAbove ? `${rect.top - popH - 8}px` : `${rect.bottom + 8}px`,
    }
    nextTick(renderSparkline)
  }
}

function renderSparkline() {
  const el = sparklineRef.value
  if (!el) return
  const data = sentimentHistory.value
  if (!data.length) return

  d3.select(el).selectAll('*').remove()
  const w = 166, h = 48
  const m = { top: 4, right: 4, bottom: 4, left: 4 }
  const svg = d3.select(el).append('svg').attr('width', w).attr('height', h)
  const xScale = d3.scaleLinear().domain(d3.extent(data, d => d.round)).range([m.left, w - m.right])
  const yScale = d3.scaleLinear().domain([-1, 1]).range([h - m.bottom, m.top])

  svg.append('line')
    .attr('x1', m.left).attr('x2', w - m.right)
    .attr('y1', yScale(0)).attr('y2', yScale(0))
    .attr('stroke', 'rgba(0,0,0,0.08)').attr('stroke-dasharray', '2,2')

  if (data.length > 1) {
    svg.append('path')
      .datum(data)
      .attr('d', d3.line().x(d => xScale(d.round)).y(d => yScale(d.score)).curve(d3.curveMonotoneX))
      .attr('fill', 'none').attr('stroke', mood.value.color).attr('stroke-width', 1.5)
  }

  const last = data[data.length - 1]
  svg.append('circle')
    .attr('cx', xScale(last.round)).attr('cy', yScale(last.score))
    .attr('r', 3).attr('fill', mood.value.color)
}

function onClickOutside(e) {
  if (!showHistory.value) return
  if (faceRef.value?.contains(e.target)) return
  if (popoverRef.value?.contains(e.target)) return
  showHistory.value = false
}

onMounted(() => document.addEventListener('click', onClickOutside, true))
onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
  clearTimeout(pulseTimer)
})

const dims = computed(() => props.size === 'large' ? 48 : 20)
</script>

<template>
  <div class="inline-flex items-center" :title="`${mood.label} (${moodScore}/10)`">
    <button
      ref="faceRef"
      class="mood-face rounded-full cursor-pointer border-0 p-0 bg-transparent"
      :class="{ 'mood-pulse': isPulsing }"
      :style="{ width: `${dims}px`, height: `${dims}px` }"
      @click="toggleHistory"
    >
      <svg :width="dims" :height="dims" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="46" :fill="mood.bg" :stroke="mood.color" stroke-width="2.5" />
        <template v-if="face.brows">
          <line
            v-for="(b, i) in face.brows"
            :key="'b' + i"
            :x1="b.x1" :y1="b.y1" :x2="b.x2" :y2="b.y2"
            :stroke="mood.color" stroke-width="3" stroke-linecap="round"
          />
        </template>
        <circle
          v-for="(eye, i) in face.eyes"
          :key="'e' + i"
          :cx="eye.cx" :cy="eye.cy" :r="eye.r"
          :fill="mood.color"
        />
        <path :d="face.mouth" fill="none" :stroke="mood.color" stroke-width="3" stroke-linecap="round" />
      </svg>
    </button>

    <span v-if="size === 'large'" class="ml-2 text-xs font-medium" :style="{ color: mood.color }">
      {{ mood.label }}
    </span>
  </div>

  <Teleport to="body">
    <Transition name="pop">
      <div
        v-if="showHistory && sentimentHistory.length"
        ref="popoverRef"
        class="fixed z-[9999] bg-[var(--color-surface,#fff)] border border-[var(--color-border,rgba(0,0,0,0.1))] rounded-lg shadow-lg p-3"
        :style="popoverPos"
      >
        <div class="text-[10px] font-medium text-[var(--color-text-muted,#888)] mb-1.5 whitespace-nowrap">
          Sentiment &middot; {{ sentimentHistory.length }} rounds
        </div>
        <div ref="sparklineRef" style="width: 166px; height: 48px" />
        <div class="flex items-center justify-between mt-1.5 text-[10px]">
          <span :style="{ color: mood.color }" class="font-medium">{{ mood.label }}</span>
          <span class="text-[var(--color-text-muted,#888)]">{{ moodScore }}/10</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.mood-face {
  transition: transform 0.2s ease;
}
.mood-face:hover {
  transform: scale(1.15);
}
.mood-pulse {
  animation: pulse-mood 0.6s ease-out;
}
@keyframes pulse-mood {
  0% { transform: scale(1); }
  30% { transform: scale(1.3); }
  100% { transform: scale(1); }
}
.pop-enter-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.pop-leave-active { transition: opacity 0.1s ease, transform 0.1s ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: scale(0.95) translateY(4px); }
</style>
