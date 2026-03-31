<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import client from '../../api/client'

const props = defineProps({
  simulationId: { type: String, required: true },
})

const chartRef = ref(null)
const metricMode = ref('sentiment') // 'sentiment' | 'engagement'
const loading = ref(false)
const error = ref(null)
const comparisonData = ref(null)
const selectedBranchIds = ref([])

let resizeObserver = null
let resizeTimer = null

// Demo fallback data
const DEMO_DATA = {
  branchPoint: 4,
  totalRounds: 12,
  sharedTimeline: Array.from({ length: 4 }, (_, i) => ({
    round: i + 1,
    sentiment: 0.1 + 0.02 * (i + 1) + (Math.random() - 0.5) * 0.04,
    engagement: 0.4 + 0.01 * (i + 1) + (Math.random() - 0.5) * 0.02,
    actions: Math.round(12 + (i + 1) * 1.5),
  })),
  branches: [
    {
      id: 'branch-original', label: 'Original Run', color: '#2068FF',
      modification: null, modificationLabel: 'Baseline (no changes)', branchPoint: 0,
    },
    {
      id: 'branch-add-agent', label: 'Added Industry Analyst', color: '#009900',
      modification: 'add_agent', modificationLabel: 'Add agent: Industry Analyst', branchPoint: 4,
    },
    {
      id: 'branch-inject-event', label: 'Market Disruption Event', color: '#ff5600',
      modification: 'inject_event', modificationLabel: 'Inject event: Market disruption', branchPoint: 4,
    },
    {
      id: 'branch-personality', label: 'Skeptical CTO', color: '#AA00FF',
      modification: 'change_personality', modificationLabel: 'Change personality: CTO → Skeptical', branchPoint: 4,
    },
  ],
  winners: {},
  availableBranches: [
    { id: 'branch-original', label: 'Original Run', color: '#2068FF' },
    { id: 'branch-add-agent', label: 'Added Industry Analyst', color: '#009900' },
    { id: 'branch-inject-event', label: 'Market Disruption Event', color: '#ff5600' },
    { id: 'branch-personality', label: 'Skeptical CTO', color: '#AA00FF' },
  ],
}

function generateDemoTimeline(branchDef) {
  const rounds = 12
  const bp = 4
  const timeline = []
  const mod = branchDef.modification
  let seed = 0
  for (const c of branchDef.id) seed += c.charCodeAt(0)

  const rng = () => {
    seed = (seed * 9301 + 49297) % 233280
    return seed / 233280
  }

  for (let r = 1; r <= rounds; r++) {
    const noise = (rng() - 0.5) * 0.08
    let sentiment, engagement, actions

    if (r <= bp) {
      sentiment = 0.1 + 0.02 * r + noise
      engagement = 0.4 + 0.01 * r + noise * 0.5
      actions = Math.round(12 + r * 1.5)
    } else {
      const offset = r - bp
      if (mod === 'add_agent') {
        sentiment = 0.1 + 0.03 * r + 0.02 * offset + noise
        engagement = 0.4 + 0.02 * r + 0.03 * offset + noise * 0.5
        actions = Math.round(15 + r * 2.0 + offset * 1.5)
      } else if (mod === 'inject_event') {
        const spike = 0.15 * Math.exp(-0.3 * offset)
        sentiment = 0.1 + 0.02 * r + spike + noise
        engagement = 0.4 + 0.015 * r + spike * 0.8 + noise * 0.5
        actions = Math.round(14 + r * 1.8)
      } else if (mod === 'change_personality') {
        sentiment = 0.1 + 0.01 * r - 0.01 * offset + noise
        engagement = 0.4 + 0.012 * r + 0.005 * offset + noise * 0.5
        actions = Math.round(13 + r * 1.6)
      } else {
        sentiment = 0.1 + 0.02 * r + noise
        engagement = 0.4 + 0.01 * r + noise * 0.5
        actions = Math.round(12 + r * 1.5)
      }
    }

    timeline.push({
      round: r,
      sentiment: Math.max(-1, Math.min(1, sentiment)),
      engagement: Math.max(0, Math.min(1, engagement)),
      actions: Math.max(1, actions),
    })
  }
  return timeline
}

function computeMetrics(timeline, bp) {
  if (!timeline.length) return {}
  const post = timeline.filter(t => t.round > bp)
  const src = post.length ? post : timeline
  return {
    finalSentiment: +(timeline[timeline.length - 1].sentiment.toFixed(3)),
    avgSentiment: +(src.reduce((s, t) => s + t.sentiment, 0) / src.length).toFixed(3),
    finalEngagement: +(timeline[timeline.length - 1].engagement.toFixed(3)),
    avgEngagement: +(src.reduce((s, t) => s + t.engagement, 0) / src.length).toFixed(3),
    totalActions: timeline.reduce((s, t) => s + t.actions, 0),
    peakSentiment: +(Math.max(...timeline.map(t => t.sentiment)).toFixed(3)),
  }
}

async function fetchComparison() {
  loading.value = true
  error.value = null
  try {
    const ids = selectedBranchIds.value.join(',')
    const { data } = await client.get(`/branches/comparison/${props.simulationId}`, {
      params: ids ? { branch_ids: ids } : {},
    })
    comparisonData.value = data
  } catch {
    // Fallback to demo data
    const demo = JSON.parse(JSON.stringify(DEMO_DATA))
    demo.simulationId = props.simulationId
    for (const branch of demo.branches) {
      branch.timeline = generateDemoTimeline(branch)
      branch.metrics = computeMetrics(branch.timeline, demo.branchPoint)
    }
    const keys = ['finalSentiment', 'avgSentiment', 'finalEngagement', 'avgEngagement', 'totalActions', 'peakSentiment']
    for (const key of keys) {
      const best = demo.branches.reduce((a, b) => (a.metrics[key] || 0) >= (b.metrics[key] || 0) ? a : b)
      demo.winners[key] = best.id
    }
    comparisonData.value = demo
  } finally {
    loading.value = false
  }
}

const availableBranches = computed(() => comparisonData.value?.availableBranches || [])

const selectedBranches = computed(() => {
  if (!comparisonData.value) return []
  return comparisonData.value.branches.filter(b => selectedBranchIds.value.includes(b.id))
})

const winners = computed(() => comparisonData.value?.winners || {})

const branchPoint = computed(() => comparisonData.value?.branchPoint || 0)

const METRIC_LABELS = {
  finalSentiment: 'Final Sentiment',
  avgSentiment: 'Avg Sentiment (post-branch)',
  finalEngagement: 'Final Engagement',
  avgEngagement: 'Avg Engagement (post-branch)',
  totalActions: 'Total Actions',
  peakSentiment: 'Peak Sentiment',
}

function toggleBranch(id) {
  const idx = selectedBranchIds.value.indexOf(id)
  if (idx >= 0) {
    if (selectedBranchIds.value.length <= 2) return
    selectedBranchIds.value.splice(idx, 1)
  } else {
    if (selectedBranchIds.value.length >= 4) return
    selectedBranchIds.value.push(id)
  }
}

function formatMetric(key, value) {
  if (value == null) return '—'
  if (key === 'totalActions') return value.toLocaleString()
  if (value >= 0) return `+${value.toFixed(3)}`
  return value.toFixed(3)
}

// --- D3 Chart ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !selectedBranches.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const branches = selectedBranches.value
  const bp = branchPoint.value
  const field = metricMode.value

  const margin = { top: 16, right: 20, bottom: 32, left: 44 }
  const width = containerWidth - margin.left - margin.right
  const height = 220
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Collect all data points for scale domains
  const allValues = branches.flatMap(b => b.timeline.map(t => t[field]))
  const minVal = Math.min(0, d3.min(allValues) - 0.05)
  const maxVal = d3.max(allValues) + 0.05

  const allRounds = branches.flatMap(b => b.timeline.map(t => t.round))
  const roundExtent = [d3.min(allRounds), d3.max(allRounds)]

  const x = d3.scaleLinear().domain(roundExtent).range([0, width])
  const y = d3.scaleLinear().domain([minVal, maxVal]).range([height, 0]).clamp(true)

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => field === 'sentiment' ? (d >= 0 ? `+${d.toFixed(2)}` : d.toFixed(2)) : d.toFixed(2))

  // X-axis labels
  const xTicks = branches[0].timeline
    .filter((_, i) => i % Math.max(1, Math.floor(roundExtent[1] / 8)) === 0 || i === roundExtent[1] - 1)
  g.selectAll('.x-label')
    .data(xTicks)
    .join('text')
    .attr('x', d => x(d.round))
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round}`)

  // Shared region background (before branch point)
  if (bp > 0) {
    g.append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', x(bp))
      .attr('height', height)
      .attr('fill', 'rgba(32, 104, 255, 0.03)')
      .attr('rx', 4)

    // Branch point vertical marker
    g.append('line')
      .attr('x1', x(bp)).attr('x2', x(bp))
      .attr('y1', 0).attr('y2', height)
      .attr('stroke', 'var(--color-border, rgba(0,0,0,0.15))')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '6,4')

    // Branch point label
    g.append('text')
      .attr('x', x(bp)).attr('y', -4)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', 'var(--color-text-secondary, #555)')
      .text(`Branch Point (R${bp})`)
  }

  // Draw branch lines
  const lineGen = d3.line()
    .x(d => x(d.round))
    .y(d => y(d[field]))
    .curve(d3.curveMonotoneX)

  const allDots = []

  branches.forEach((branch, bi) => {
    const data = branch.timeline

    // Shared portion (thicker, dimmed)
    if (bp > 0) {
      const shared = data.filter(d => d.round <= bp)
      if (bi === 0 && shared.length > 1) {
        g.append('path')
          .datum(shared)
          .attr('d', lineGen)
          .attr('fill', 'none')
          .attr('stroke', '#888')
          .attr('stroke-width', 3)
          .attr('stroke-opacity', 0.4)
      }
    }

    // Diverging portion (colored)
    const diverging = bp > 0
      ? data.filter(d => d.round >= bp)
      : data

    if (diverging.length > 1) {
      const path = g.append('path')
        .datum(diverging)
        .attr('d', lineGen)
        .attr('fill', 'none')
        .attr('stroke', branch.color)
        .attr('stroke-width', 2.5)

      // Animate line drawing
      const totalLength = path.node().getTotalLength()
      path
        .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
        .attr('stroke-dashoffset', totalLength)
        .transition()
        .duration(600)
        .delay(bi * 100)
        .ease(d3.easeCubicOut)
        .attr('stroke-dashoffset', 0)
    }

    // Data points (diverging portion only)
    const dotData = bp > 0 ? data.filter(d => d.round > bp) : data
    dotData.forEach(d => allDots.push({ ...d, branch }))
  })

  // Render dots
  const dots = g.selectAll('.dot')
    .data(allDots)
    .join('circle')
    .attr('cx', d => x(d.round))
    .attr('cy', d => y(d[field]))
    .attr('r', 0)
    .attr('fill', d => d.branch.color)
    .attr('stroke', 'var(--color-surface, #fff)')
    .attr('stroke-width', 1.5)

  dots.transition()
    .duration(200)
    .delay((_, i) => 600 + i * 20)
    .attr('r', 3.5)

  // Tooltip
  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '8px 12px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('max-width', '220px')

  // Vertical hover line + tooltip
  const hoverLine = g.append('line')
    .attr('y1', 0).attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.1)')
    .attr('stroke-width', 1)
    .style('opacity', 0)

  // Hover overlay per round
  const rounds = branches[0].timeline.map(t => t.round)
  g.selectAll('.hover-target')
    .data(rounds)
    .join('rect')
    .attr('x', d => {
      const idx = rounds.indexOf(d)
      const prev = idx > 0 ? x(rounds[idx - 1]) : x(d)
      return (prev + x(d)) / 2
    })
    .attr('y', 0)
    .attr('width', (d) => {
      const idx = rounds.indexOf(d)
      const prev = idx > 0 ? x(rounds[idx - 1]) : x(d)
      const next = idx < rounds.length - 1 ? x(rounds[idx + 1]) : x(d)
      return ((x(d) - prev) + (next - x(d))) / 2
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, round) => {
      hoverLine
        .attr('x1', x(round)).attr('x2', x(round))
        .style('opacity', 1)

      const rows = branches.map(b => {
        const pt = b.timeline.find(t => t.round === round)
        if (!pt) return ''
        const val = field === 'sentiment'
          ? (pt.sentiment >= 0 ? `+${pt.sentiment.toFixed(3)}` : pt.sentiment.toFixed(3))
          : pt.engagement.toFixed(3)
        return `<div style="display:flex;align-items:center;gap:6px;margin-top:3px">
          <span style="width:8px;height:8px;border-radius:50%;background:${b.color};flex-shrink:0"></span>
          <span style="color:var(--color-text-secondary,#555)">${b.label}:</span>
          <span style="font-weight:600">${val}</span>
        </div>`
      }).join('')

      tooltip
        .html(`<div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:2px">Round ${round}${round <= bp ? ' (shared)' : ''}</div>${rows}`)
        .style('opacity', 1)

      // Highlight dots at this round
      dots.filter(d => d.round === round)
        .transition().duration(80).attr('r', 5.5)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 30}px`)
    })
    .on('mouseleave', (event, round) => {
      hoverLine.style('opacity', 0)
      tooltip.style('opacity', 0)
      dots.filter(d => d.round === round)
        .transition().duration(80).attr('r', 3.5)
    })
}

// Lifecycle
watch([selectedBranches, metricMode], () => {
  nextTick(() => renderChart())
})

watch(selectedBranchIds, () => {
  fetchComparison()
})

onMounted(async () => {
  await fetchComparison()

  // Default: select all branches (up to 4)
  if (comparisonData.value?.availableBranches) {
    selectedBranchIds.value = comparisonData.value.availableBranches
      .slice(0, 4)
      .map(b => b.id)
  }

  nextTick(() => {
    renderChart()
    if (chartRef.value) {
      resizeObserver = new ResizeObserver(() => {
        clearTimeout(resizeTimer)
        resizeTimer = setTimeout(renderChart, 200)
      })
      resizeObserver.observe(chartRef.value)
    }
  })
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg">
    <!-- Header -->
    <div class="flex items-center justify-between p-5 pb-0">
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Branch Comparison</h3>
        <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
          Select 2–4 branches to compare outcomes side by side
        </p>
      </div>
      <div v-if="selectedBranches.length" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="metricMode === 'sentiment'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="metricMode = 'sentiment'"
        >Sentiment</button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="metricMode === 'engagement'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="metricMode = 'engagement'"
        >Engagement</button>
      </div>
    </div>

    <!-- Branch Selector -->
    <div class="flex flex-wrap items-center gap-2 px-5 pt-4 pb-2">
      <button
        v-for="branch in availableBranches"
        :key="branch.id"
        class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium border transition-all"
        :class="selectedBranchIds.includes(branch.id)
          ? 'border-transparent text-white shadow-sm'
          : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-[var(--color-text-muted)]'"
        :style="selectedBranchIds.includes(branch.id) ? `background:${branch.color}` : ''"
        @click="toggleBranch(branch.id)"
      >
        <span
          v-if="!selectedBranchIds.includes(branch.id)"
          class="w-2 h-2 rounded-full"
          :style="`background:${branch.color}`"
        />
        <svg v-else class="w-3 h-3" viewBox="0 0 16 16" fill="currentColor">
          <path d="M13.78 4.22a.75.75 0 010 1.06l-7.25 7.25a.75.75 0 01-1.06 0L2.22 9.28a.75.75 0 011.06-1.06L6 10.94l6.72-6.72a.75.75 0 011.06 0z"/>
        </svg>
        {{ branch.label }}
      </button>
      <span class="text-[10px] text-[var(--color-text-muted)] ml-1">
        {{ selectedBranchIds.length }}/4 selected
      </span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center h-[260px]">
      <div class="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
        <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        Loading comparison data...
      </div>
    </div>

    <!-- Chart -->
    <div
      v-else-if="selectedBranches.length >= 2"
      ref="chartRef"
      class="relative mx-5 mt-2"
      style="height: 268px"
    />

    <!-- Not enough branches selected -->
    <div v-else class="flex items-center justify-center h-[220px] text-[var(--color-text-muted)] text-sm">
      Select at least 2 branches to compare
    </div>

    <!-- Legend -->
    <div v-if="selectedBranches.length >= 2" class="flex flex-wrap items-center gap-4 px-5 pt-1 pb-2 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-4 h-0.5 bg-[#888] opacity-40 rounded" /> Shared timeline
      </span>
      <span
        v-for="branch in selectedBranches"
        :key="branch.id"
        class="flex items-center gap-1.5"
      >
        <span class="inline-block w-2 h-2 rounded-full" :style="`background:${branch.color}`" />
        {{ branch.label }}
      </span>
    </div>

    <!-- Metrics Table -->
    <div v-if="selectedBranches.length >= 2" class="px-5 pb-5 pt-2">
      <div class="border border-[var(--color-border)] rounded-lg overflow-hidden">
        <table class="w-full text-xs">
          <thead>
            <tr class="bg-[var(--color-tint)]">
              <th class="text-left px-3 py-2 font-semibold text-[var(--color-text-secondary)]">Metric</th>
              <th
                v-for="branch in selectedBranches"
                :key="branch.id"
                class="text-right px-3 py-2 font-semibold"
                :style="`color:${branch.color}`"
              >{{ branch.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(label, key) in METRIC_LABELS"
              :key="key"
              class="border-t border-[var(--color-border)]"
            >
              <td class="px-3 py-2 text-[var(--color-text-secondary)]">{{ label }}</td>
              <td
                v-for="branch in selectedBranches"
                :key="branch.id"
                class="text-right px-3 py-2 font-mono"
                :class="winners[key] === branch.id
                  ? 'text-[#009900] font-semibold bg-[rgba(0,153,0,0.04)]'
                  : 'text-[var(--color-text)]'"
              >
                <span class="inline-flex items-center gap-1">
                  {{ formatMetric(key, branch.metrics?.[key]) }}
                  <svg
                    v-if="winners[key] === branch.id"
                    class="w-3 h-3 text-[#009900]"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                  >
                    <path d="M8 0l2.5 5.3L16 6.2l-4 3.9 1 5.9L8 13.4 2.9 16l1-5.9-4-3.9 5.6-.9L8 0z"/>
                  </svg>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
