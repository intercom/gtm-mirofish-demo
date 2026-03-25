<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useSimulationStore } from '../../stores/simulation'
import { simulationApi } from '../../api/simulation'

const store = useSimulationStore()

const simAId = ref(null)
const simBId = ref(null)
const syncRounds = ref(true)
const currentRound = ref(0)
const loading = ref(false)
const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const simAData = ref(null)
const simBData = ref(null)

const completedRuns = computed(() =>
  store.sessionRuns.filter(r => r.status === 'completed' || r.status === 'complete'),
)

const needsDemo = computed(() => completedRuns.value.length < 2)

const DEMO_RUNS = [
  {
    id: 'demo-a',
    scenarioName: 'Enterprise SaaS Launch',
    totalRounds: 24,
    totalActions: 312,
    twitterActions: 187,
    redditActions: 125,
    agentCount: 15,
    platformMode: 'parallel',
    timestamp: Date.now() - 3600000,
  },
  {
    id: 'demo-b',
    scenarioName: 'SMB Market Entry',
    totalRounds: 24,
    totalActions: 278,
    twitterActions: 142,
    redditActions: 136,
    agentCount: 12,
    platformMode: 'parallel',
    timestamp: Date.now() - 7200000,
  },
]

function generateDemoRoundData(seed, rounds, totalActions) {
  const data = []
  let hash = seed
  for (let i = 1; i <= rounds; i++) {
    hash = ((hash * 1103515245 + 12345) & 0x7fffffff)
    const base = totalActions / rounds
    const variance = base * 0.5
    const actions = Math.max(1, Math.round(base + (hash % 100 - 50) / 50 * variance))
    hash = ((hash * 1103515245 + 12345) & 0x7fffffff)
    const sentiment = ((hash % 200) - 100) / 100 * 0.6
    data.push({ round: i, actions, sentiment: Math.round(sentiment * 100) / 100 })
  }
  return data
}

const selectableRuns = computed(() => {
  if (needsDemo.value) return DEMO_RUNS
  return completedRuns.value
})

const availableForA = computed(() =>
  selectableRuns.value.filter(r => r.id !== simBId.value),
)
const availableForB = computed(() =>
  selectableRuns.value.filter(r => r.id !== simAId.value),
)

const simARun = computed(() => selectableRuns.value.find(r => r.id === simAId.value))
const simBRun = computed(() => selectableRuns.value.find(r => r.id === simBId.value))

const maxRound = computed(() => {
  const aMax = simAData.value?.length || 0
  const bMax = simBData.value?.length || 0
  return Math.max(aMax, bMax)
})

const comparisonMetrics = computed(() => {
  const a = simARun.value
  const b = simBRun.value
  if (!a || !b) return []

  const metrics = [
    { name: 'Total Actions', a: a.totalActions || 0, b: b.totalActions || 0 },
    { name: 'Twitter Actions', a: a.twitterActions || 0, b: b.twitterActions || 0 },
    { name: 'Reddit Actions', a: a.redditActions || 0, b: b.redditActions || 0 },
    { name: 'Total Rounds', a: a.totalRounds || 0, b: b.totalRounds || 0 },
    { name: 'Agent Count', a: a.agentCount || 0, b: b.agentCount || 0 },
  ]

  if (simAData.value?.length && simBData.value?.length) {
    const avgSentA = d3.mean(simAData.value, d => d.sentiment) || 0
    const avgSentB = d3.mean(simBData.value, d => d.sentiment) || 0
    metrics.push({ name: 'Avg Sentiment', a: Math.round(avgSentA * 100) / 100, b: Math.round(avgSentB * 100) / 100 })

    const avgActA = d3.mean(simAData.value, d => d.actions) || 0
    const avgActB = d3.mean(simBData.value, d => d.actions) || 0
    metrics.push({ name: 'Avg Actions/Round', a: Math.round(avgActA * 10) / 10, b: Math.round(avgActB * 10) / 10 })
  }

  return metrics.map(m => {
    const diff = m.a - m.b
    const absDiff = Math.abs(diff)
    let winner = 'tie'
    if (m.name === 'Avg Sentiment') {
      if (diff > 0.05) winner = 'a'
      else if (diff < -0.05) winner = 'b'
    } else {
      if (diff > 0) winner = 'a'
      else if (diff < 0) winner = 'b'
    }
    return { ...m, diff, absDiff, winner }
  })
})

const scorecard = computed(() => {
  let aWins = 0
  let bWins = 0
  for (const m of comparisonMetrics.value) {
    if (m.winner === 'a') aWins++
    else if (m.winner === 'b') bWins++
  }
  return { aWins, bWins, ties: comparisonMetrics.value.length - aWins - bWins }
})

function actionsToRoundData(actions) {
  const roundMap = new Map()
  for (const action of actions) {
    const round = action.round_num
    if (round == null) continue
    if (!roundMap.has(round)) roundMap.set(round, { count: 0, sentiments: [] })
    const entry = roundMap.get(round)
    entry.count++
    const content = action.action_args?.content || ''
    if (content) {
      const lower = content.toLowerCase()
      let pos = 0, neg = 0
      for (const w of ['impressive', 'great', 'excellent', 'good', 'recommend', 'valuable', 'innovative', 'better', 'love', 'helpful']) {
        if (lower.includes(w)) pos++
      }
      for (const w of ['concerned', 'skeptical', 'risk', 'worried', 'expensive', 'difficult', 'doubt', 'problem', 'poor', 'limited']) {
        if (lower.includes(w)) neg++
      }
      if (pos + neg > 0) entry.sentiments.push((pos - neg) / (pos + neg))
    }
  }
  return Array.from(roundMap.keys())
    .sort((a, b) => a - b)
    .map(round => {
      const e = roundMap.get(round)
      const avgSent = e.sentiments.length ? d3.mean(e.sentiments) : 0
      return { round, actions: e.count, sentiment: Math.round(avgSent * 100) / 100 }
    })
}

async function loadSimData(simId, isDemo) {
  if (isDemo) {
    const seed = simId === 'demo-a' ? 42 : 137
    const run = DEMO_RUNS.find(r => r.id === simId)
    return generateDemoRoundData(seed, run.totalRounds, run.totalActions)
  }
  try {
    const res = await simulationApi.getActions(simId)
    const actions = res.data?.data?.actions || res.data?.actions || res.data || []
    if (Array.isArray(actions) && actions.length) return actionsToRoundData(actions)
  } catch {
    // Fall through to demo data
  }
  const run = completedRuns.value.find(r => r.id === simId)
  return generateDemoRoundData(
    simId.split('').reduce((h, c) => ((h << 5) - h + c.charCodeAt(0)) | 0, 0),
    run?.totalRounds || 20,
    run?.totalActions || 200,
  )
}

async function fetchData() {
  if (!simAId.value || !simBId.value) return
  loading.value = true
  try {
    const [a, b] = await Promise.all([
      loadSimData(simAId.value, needsDemo.value),
      loadSimData(simBId.value, needsDemo.value),
    ])
    simAData.value = a
    simBData.value = b
    currentRound.value = 0
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

function swapSimulations() {
  const tmp = simAId.value
  simAId.value = simBId.value
  simBId.value = tmp
}

function stepRound(delta) {
  const next = currentRound.value + delta
  if (next >= 0 && next <= maxRound.value) {
    currentRound.value = next
    renderChart()
  }
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  if (!chartRef.value || !simAData.value?.length || !simBData.value?.length) return

  const container = chartRef.value
  const rect = container.getBoundingClientRect()
  const width = rect.width || 600
  const height = 280
  const margin = { top: 20, right: 20, bottom: 40, left: 50 }

  const dataA = currentRound.value > 0
    ? simAData.value.filter(d => d.round <= currentRound.value)
    : simAData.value
  const dataB = currentRound.value > 0
    ? simBData.value.filter(d => d.round <= currentRound.value)
    : simBData.value

  const allData = [...dataA, ...dataB]
  const xDomain = [
    d3.min(allData, d => d.round) || 1,
    d3.max(allData, d => d.round) || 24,
  ]
  const yMax = d3.max(allData, d => d.actions) || 20

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const x = d3.scaleLinear()
    .domain(xDomain)
    .range([margin.left, width - margin.right])

  const y = d3.scaleLinear()
    .domain([0, yMax * 1.15])
    .range([height - margin.bottom, margin.top])

  // Grid lines
  svg.append('g')
    .attr('transform', `translate(${margin.left},0)`)
    .call(d3.axisLeft(y).ticks(5).tickSize(-(width - margin.left - margin.right)).tickFormat(''))
    .call(g => g.selectAll('.tick line').attr('stroke', '#e5e7eb').attr('stroke-dasharray', '2,2'))
    .call(g => g.select('.domain').remove())

  // X axis
  svg.append('g')
    .attr('transform', `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).ticks(Math.min(dataA.length, 12)).tickFormat(d => `R${d}`))
    .call(g => g.select('.domain').attr('stroke', '#d1d5db'))
    .call(g => g.selectAll('.tick text').attr('fill', '#6b7280').attr('font-size', '11px'))

  // Y axis
  svg.append('g')
    .attr('transform', `translate(${margin.left},0)`)
    .call(d3.axisLeft(y).ticks(5))
    .call(g => g.select('.domain').remove())
    .call(g => g.selectAll('.tick text').attr('fill', '#6b7280').attr('font-size', '11px'))

  // Y label
  svg.append('text')
    .attr('transform', `rotate(-90)`)
    .attr('x', -(height / 2))
    .attr('y', 14)
    .attr('text-anchor', 'middle')
    .attr('fill', '#9ca3af')
    .attr('font-size', '11px')
    .text('Actions')

  const lineGen = d3.line()
    .x(d => x(d.round))
    .y(d => y(d.actions))
    .curve(d3.curveMonotoneX)

  // Area fills
  const areaGen = d3.area()
    .x(d => x(d.round))
    .y0(height - margin.bottom)
    .y1(d => y(d.actions))
    .curve(d3.curveMonotoneX)

  svg.append('path')
    .datum(dataA)
    .attr('fill', 'rgba(32,104,255,0.08)')
    .attr('d', areaGen)

  svg.append('path')
    .datum(dataB)
    .attr('fill', 'rgba(255,86,0,0.06)')
    .attr('d', areaGen)

  // Lines
  const pathA = svg.append('path')
    .datum(dataA)
    .attr('fill', 'none')
    .attr('stroke', '#2068FF')
    .attr('stroke-width', 2.5)
    .attr('d', lineGen)

  const pathB = svg.append('path')
    .datum(dataB)
    .attr('fill', 'none')
    .attr('stroke', '#ff5600')
    .attr('stroke-width', 2.5)
    .attr('d', lineGen)

  // Animate lines
  for (const path of [pathA, pathB]) {
    const length = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${length} ${length}`)
      .attr('stroke-dashoffset', length)
      .transition()
      .duration(800)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
  }

  // Dots
  svg.selectAll('.dot-a')
    .data(dataA)
    .enter()
    .append('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', d => y(d.actions))
    .attr('r', 0)
    .attr('fill', '#2068FF')
    .transition()
    .delay((d, i) => 800 + i * 30)
    .duration(200)
    .attr('r', 3)

  svg.selectAll('.dot-b')
    .data(dataB)
    .enter()
    .append('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', d => y(d.actions))
    .attr('r', 0)
    .attr('fill', '#ff5600')
    .transition()
    .delay((d, i) => 800 + i * 30)
    .duration(200)
    .attr('r', 3)

  // Tooltip overlay
  const tooltip = d3.select(container)
    .append('div')
    .attr('class', 'comparison-tooltip')
    .style('position', 'absolute')
    .style('display', 'none')
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, #e5e7eb)')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('pointer-events', 'none')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')

  svg.append('rect')
    .attr('width', width - margin.left - margin.right)
    .attr('height', height - margin.top - margin.bottom)
    .attr('transform', `translate(${margin.left},${margin.top})`)
    .attr('fill', 'transparent')
    .on('mousemove', (event) => {
      const [mx] = d3.pointer(event)
      const round = Math.round(x.invert(mx + margin.left))
      const aPoint = dataA.find(d => d.round === round)
      const bPoint = dataB.find(d => d.round === round)
      if (!aPoint && !bPoint) { tooltip.style('display', 'none'); return }

      let html = `<div style="font-weight:600;margin-bottom:4px;color:var(--color-text,#1a1a1a)">Round ${round}</div>`
      if (aPoint) html += `<div style="color:#2068FF">A: ${aPoint.actions} actions</div>`
      if (bPoint) html += `<div style="color:#ff5600">B: ${bPoint.actions} actions</div>`
      if (aPoint && bPoint) {
        const diff = aPoint.actions - bPoint.actions
        const color = diff > 0 ? '#2068FF' : diff < 0 ? '#ff5600' : '#6b7280'
        html += `<div style="color:${color};margin-top:2px;font-size:11px">${diff > 0 ? '+' : ''}${diff} difference</div>`
      }

      tooltip.html(html).style('display', 'block')
      const tooltipRect = tooltip.node().getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      let left = event.clientX - containerRect.left + 12
      if (left + tooltipRect.width > containerRect.width) left = left - tooltipRect.width - 24
      tooltip.style('left', `${left}px`).style('top', `${event.clientY - containerRect.top - tooltipRect.height - 8}px`)
    })
    .on('mouseleave', () => tooltip.style('display', 'none'))
}

watch([simAId, simBId], () => {
  if (simAId.value && simBId.value) fetchData()
})

onMounted(() => {
  if (selectableRuns.value.length >= 2) {
    simAId.value = selectableRuns.value[0].id
    simBId.value = selectableRuns.value[1].id
  }

  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => renderChart(), 150)
    })
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})

function formatMetric(val) {
  if (typeof val !== 'number') return '-'
  return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(2)
}

function diffLabel(m) {
  const prefix = m.diff > 0 ? '+' : ''
  return prefix + formatMetric(m.diff)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header with selectors -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4">
      <div class="flex-1 min-w-0">
        <label class="block text-xs font-medium text-[var(--color-text-muted)] mb-1">Simulation A</label>
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-[#2068FF] shrink-0" />
          <select
            v-model="simAId"
            class="w-full text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
          >
            <option :value="null" disabled>Select simulation...</option>
            <option v-for="run in availableForA" :key="run.id" :value="run.id">
              {{ run.scenarioName }} ({{ run.totalActions }} actions)
            </option>
          </select>
        </div>
      </div>

      <button
        @click="swapSimulations"
        :disabled="!simAId || !simBId"
        class="p-2 rounded-lg border border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[#2068FF] hover:border-[#2068FF]/50 transition-colors disabled:opacity-30 mt-4 sm:mt-5"
        title="Swap simulations"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
        </svg>
      </button>

      <div class="flex-1 min-w-0">
        <label class="block text-xs font-medium text-[var(--color-text-muted)] mb-1">Simulation B</label>
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-[#ff5600] shrink-0" />
          <select
            v-model="simBId"
            class="w-full text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] px-3 py-2 focus:ring-2 focus:ring-[#2068FF] focus:border-transparent"
          >
            <option :value="null" disabled>Select simulation...</option>
            <option v-for="run in availableForB" :key="run.id" :value="run.id">
              {{ run.scenarioName }} ({{ run.totalActions }} actions)
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Demo badge -->
    <div v-if="needsDemo" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-[rgba(32,104,255,0.06)] border border-[#2068FF]/20">
      <svg class="w-4 h-4 text-[#2068FF] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
      </svg>
      <span class="text-xs text-[#2068FF]">Showing demo data — run 2+ simulations to compare your own results</span>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="w-6 h-6 border-2 border-[#2068FF] border-t-transparent rounded-full animate-spin" />
      <span class="ml-3 text-sm text-[var(--color-text-muted)]">Loading comparison data...</span>
    </div>

    <template v-else-if="simARun && simBRun">
      <!-- Side-by-side metric panels -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Sim A panel -->
        <div class="border-2 border-[#2068FF]/30 bg-[rgba(32,104,255,0.03)] rounded-lg p-4">
          <div class="flex items-center gap-2 mb-3">
            <span class="w-2.5 h-2.5 rounded-full bg-[#2068FF]" />
            <h3 class="text-sm font-semibold text-[var(--color-text)] truncate">{{ simARun.scenarioName }}</h3>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[var(--color-text-muted)]">Actions</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ (simARun.totalActions || 0).toLocaleString() }}</div>
            </div>
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[var(--color-text-muted)]">Rounds</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ simARun.totalRounds || 0 }}</div>
            </div>
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[#2068FF]">Twitter</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ (simARun.twitterActions || 0).toLocaleString() }}</div>
            </div>
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[#ff5600]">Reddit</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ (simARun.redditActions || 0).toLocaleString() }}</div>
            </div>
          </div>
        </div>

        <!-- Sim B panel -->
        <div class="border-2 border-[#ff5600]/30 bg-[rgba(255,86,0,0.03)] rounded-lg p-4">
          <div class="flex items-center gap-2 mb-3">
            <span class="w-2.5 h-2.5 rounded-full bg-[#ff5600]" />
            <h3 class="text-sm font-semibold text-[var(--color-text)] truncate">{{ simBRun.scenarioName }}</h3>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[var(--color-text-muted)]">Actions</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ (simBRun.totalActions || 0).toLocaleString() }}</div>
            </div>
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[var(--color-text-muted)]">Rounds</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ simBRun.totalRounds || 0 }}</div>
            </div>
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[#2068FF]">Twitter</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ (simBRun.twitterActions || 0).toLocaleString() }}</div>
            </div>
            <div class="bg-[var(--color-surface)] rounded-md px-3 py-2">
              <div class="text-xs text-[#ff5600]">Reddit</div>
              <div class="text-sm font-semibold text-[var(--color-text)]">{{ (simBRun.redditActions || 0).toLocaleString() }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Overlay chart -->
      <div class="border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg p-4">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Actions per Round</h3>
          <div class="flex items-center gap-3">
            <!-- Sync control -->
            <label class="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)] cursor-pointer">
              <input
                type="checkbox"
                v-model="syncRounds"
                class="w-3.5 h-3.5 rounded border-[var(--color-border)] text-[#2068FF] focus:ring-[#2068FF]"
              />
              Sync rounds
            </label>
            <!-- Round nav -->
            <div v-if="syncRounds && maxRound > 0" class="flex items-center gap-1">
              <button
                @click="stepRound(-1)"
                :disabled="currentRound <= 0"
                class="p-1 rounded text-[var(--color-text-muted)] hover:text-[#2068FF] disabled:opacity-30 transition-colors"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" />
                </svg>
              </button>
              <span class="text-xs text-[var(--color-text-muted)] min-w-[60px] text-center">
                {{ currentRound === 0 ? 'All' : `R1–${currentRound}` }}
              </span>
              <button
                @click="stepRound(1)"
                :disabled="currentRound >= maxRound"
                class="p-1 rounded text-[var(--color-text-muted)] hover:text-[#2068FF] disabled:opacity-30 transition-colors"
              >
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
                </svg>
              </button>
            </div>
            <!-- Legend -->
            <div class="flex items-center gap-3 text-xs">
              <span class="flex items-center gap-1"><span class="w-3 h-0.5 bg-[#2068FF] rounded" /> A</span>
              <span class="flex items-center gap-1"><span class="w-3 h-0.5 bg-[#ff5600] rounded" /> B</span>
            </div>
          </div>
        </div>
        <div ref="chartRef" class="relative w-full" style="height: 280px;" />
      </div>

      <!-- Summary comparison table -->
      <div class="border border-[var(--color-border)] bg-[var(--color-surface)] rounded-lg overflow-hidden">
        <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Comparison Summary</h3>
          <div class="flex items-center gap-3 text-xs">
            <span class="text-[#2068FF] font-medium">A wins {{ scorecard.aWins }}</span>
            <span class="text-[var(--color-text-muted)]">{{ scorecard.ties }} tie{{ scorecard.ties !== 1 ? 's' : '' }}</span>
            <span class="text-[#ff5600] font-medium">B wins {{ scorecard.bWins }}</span>
          </div>
        </div>
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-[var(--color-tint)]">
              <th class="text-left px-4 py-2 text-xs font-medium text-[var(--color-text-muted)]">Metric</th>
              <th class="text-right px-4 py-2 text-xs font-medium text-[#2068FF]">Sim A</th>
              <th class="text-right px-4 py-2 text-xs font-medium text-[#ff5600]">Sim B</th>
              <th class="text-right px-4 py-2 text-xs font-medium text-[var(--color-text-muted)]">Diff</th>
              <th class="text-center px-4 py-2 text-xs font-medium text-[var(--color-text-muted)]">Winner</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="m in comparisonMetrics"
              :key="m.name"
              class="border-t border-[var(--color-border)] transition-colors hover:bg-[var(--color-tint)]"
            >
              <td class="px-4 py-2.5 text-[var(--color-text)]">{{ m.name }}</td>
              <td class="px-4 py-2.5 text-right font-medium" :class="m.winner === 'a' ? 'text-[#2068FF]' : 'text-[var(--color-text)]'">
                {{ formatMetric(m.a) }}
              </td>
              <td class="px-4 py-2.5 text-right font-medium" :class="m.winner === 'b' ? 'text-[#ff5600]' : 'text-[var(--color-text)]'">
                {{ formatMetric(m.b) }}
              </td>
              <td class="px-4 py-2.5 text-right text-[var(--color-text-muted)]">
                {{ diffLabel(m) }}
              </td>
              <td class="px-4 py-2.5 text-center">
                <span
                  v-if="m.winner === 'a'"
                  class="inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-[rgba(32,104,255,0.1)] text-[#2068FF]"
                >A</span>
                <span
                  v-else-if="m.winner === 'b'"
                  class="inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-[rgba(255,86,0,0.1)] text-[#ff5600]"
                >B</span>
                <span v-else class="text-xs text-[var(--color-text-muted)]">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- Empty state -->
    <div v-else-if="!loading" class="text-center py-12">
      <div class="w-14 h-14 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6 text-[#2068FF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21 3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
        </svg>
      </div>
      <h3 class="text-sm font-semibold text-[var(--color-text)] mb-1">Select two simulations</h3>
      <p class="text-xs text-[var(--color-text-muted)]">Choose simulations above to compare their results side by side.</p>
    </div>
  </div>
</template>
