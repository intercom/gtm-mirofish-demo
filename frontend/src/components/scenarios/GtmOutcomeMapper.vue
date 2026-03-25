<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'
import { scenariosApi } from '../../api/scenarios'

const props = defineProps({
  scenarioId: { type: String, required: true },
})

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  text: '#050505',
  muted: '#888',
  gridLine: 'rgba(0,0,0,0.06)',
  barBg: 'rgba(0,0,0,0.03)',
}

const CATEGORY_COLORS = {
  hiring: COLORS.primary,
  campaign: COLORS.orange,
  optimization: COLORS.green,
  targeting: COLORS.purple,
  retention: '#0077B6',
  pricing: COLORS.orange,
  process: '#888',
  enablement: COLORS.primary,
  automation: COLORS.green,
  content: COLORS.purple,
}

const loading = ref(true)
const error = ref(null)
const outcomes = ref(null)
const selectedDecision = ref(null)

const impactChartRef = ref(null)
const timelineChartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const formatCurrency = (value) => {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`
  return `$${value}`
}

const totalPipeline = computed(() => outcomes.value?.totals?.pipeline_per_month ?? 0)
const totalCost = computed(() => outcomes.value?.totals?.cost_per_month ?? 0)
const netImpact = computed(() => outcomes.value?.totals?.net_impact ?? 0)
const avgRoi = computed(() => outcomes.value?.totals?.avg_roi ?? 0)

async function fetchOutcomes() {
  loading.value = true
  error.value = null
  try {
    const res = await scenariosApi.getOutcomes(props.scenarioId)
    outcomes.value = res.data
    selectedDecision.value = null
    await nextTick()
    renderCharts()
  } catch (e) {
    error.value = e.message || 'Failed to load outcome data'
  } finally {
    loading.value = false
  }
}

function selectDecision(decision) {
  selectedDecision.value =
    selectedDecision.value?.id === decision.id ? null : decision
  nextTick(() => renderTimelineChart())
}

function clearCharts() {
  if (impactChartRef.value) d3.select(impactChartRef.value).selectAll('*').remove()
  if (timelineChartRef.value) d3.select(timelineChartRef.value).selectAll('*').remove()
}

function renderCharts() {
  clearCharts()
  if (!outcomes.value?.decisions?.length) return
  renderImpactChart()
  renderTimelineChart()
}

// --- Stacked Bar Chart: Impact vs Cost per Decision ---

function renderImpactChart() {
  const container = impactChartRef.value
  if (!container) return

  const decisions = outcomes.value.decisions
  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 80, bottom: 60, left: 180 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 32
  const barGap = 16
  const height = decisions.length * (barHeight + barGap) * 2 + barGap
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Projected Impact vs Cost')

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Monthly pipeline generation and associated cost per decision')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(decisions, d =>
    Math.max(d.impact.pipeline_per_month, d.impact.cost_per_month)
  )
  const x = d3.scaleLinear()
    .domain([0, maxVal * 1.15])
    .range([0, width])

  const gridTicks = x.ticks(5)
  g.selectAll('.grid-line')
    .data(gridTicks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', COLORS.gridLine)
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.x-label')
    .data(gridTicks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', height + 16)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => formatCurrency(d))

  const rowHeight = (barHeight + barGap) * 2
  decisions.forEach((decision, i) => {
    const yOffset = i * rowHeight

    // Decision label
    g.append('text')
      .attr('x', -8)
      .attr('y', yOffset + barHeight / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-size', '11px')
      .attr('fill', '#555')
      .text(decision.title.length > 28 ? decision.title.slice(0, 26) + '…' : decision.title)
      .style('cursor', 'pointer')
      .on('click', () => selectDecision(decision))

    // Pipeline bar background
    g.append('rect')
      .attr('x', 0)
      .attr('y', yOffset)
      .attr('width', width)
      .attr('height', barHeight)
      .attr('rx', 4)
      .attr('fill', COLORS.barBg)

    // Pipeline bar
    const catColor = CATEGORY_COLORS[decision.category] || COLORS.primary
    g.append('rect')
      .attr('x', 0)
      .attr('y', yOffset)
      .attr('width', 0)
      .attr('height', barHeight)
      .attr('rx', 4)
      .attr('fill', catColor)
      .attr('opacity', 0.85)
      .style('cursor', 'pointer')
      .on('click', () => selectDecision(decision))
      .transition()
      .duration(600)
      .delay(i * 100)
      .ease(d3.easeCubicOut)
      .attr('width', x(decision.impact.pipeline_per_month))

    // Pipeline value
    g.append('text')
      .attr('x', x(decision.impact.pipeline_per_month) + 8)
      .attr('y', yOffset + barHeight / 2)
      .attr('dy', '0.35em')
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', catColor)
      .style('opacity', 0)
      .text(formatCurrency(decision.impact.pipeline_per_month))
      .transition()
      .duration(300)
      .delay(600 + i * 100)
      .style('opacity', 1)

    // Cost bar background
    const costY = yOffset + barHeight + 4
    g.append('rect')
      .attr('x', 0)
      .attr('y', costY)
      .attr('width', width)
      .attr('height', barHeight * 0.6)
      .attr('rx', 3)
      .attr('fill', COLORS.barBg)

    // Cost bar
    g.append('rect')
      .attr('x', 0)
      .attr('y', costY)
      .attr('width', 0)
      .attr('height', barHeight * 0.6)
      .attr('rx', 3)
      .attr('fill', COLORS.orange)
      .attr('opacity', 0.5)
      .transition()
      .duration(600)
      .delay(i * 100 + 50)
      .ease(d3.easeCubicOut)
      .attr('width', x(decision.impact.cost_per_month))

    // Cost value
    g.append('text')
      .attr('x', x(decision.impact.cost_per_month) + 8)
      .attr('y', costY + (barHeight * 0.6) / 2)
      .attr('dy', '0.35em')
      .attr('font-size', '10px')
      .attr('fill', COLORS.orange)
      .style('opacity', 0)
      .text(formatCurrency(decision.impact.cost_per_month) + ' cost')
      .transition()
      .duration(300)
      .delay(650 + i * 100)
      .style('opacity', 1)
  })

  // Legend
  const legend = svg.append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 200}, 14)`)

  legend.append('rect')
    .attr('x', 0).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.85)

  legend.append('text')
    .attr('x', 16).attr('y', 9)
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text('Pipeline/mo')

  legend.append('rect')
    .attr('x', 100).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0.5)

  legend.append('text')
    .attr('x', 116).attr('y', 9)
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text('Cost/mo')
}

// --- Timeline Chart: 30/60/90 Day Projections ---

function renderTimelineChart() {
  const container = timelineChartRef.value
  if (!container) return
  d3.select(container).selectAll('*').remove()

  const decisions = selectedDecision.value
    ? [selectedDecision.value]
    : (outcomes.value?.decisions ?? [])

  if (!decisions.length) return

  const periods = ['day_30', 'day_60', 'day_90']
  const periodLabels = ['30 Days', '60 Days', '90 Days']

  // Aggregate timeline data across selected decisions
  const timelineData = periods.map((period, idx) => {
    const pipeline = decisions.reduce(
      (sum, d) => sum + (d.timeline[period]?.pipeline ?? 0), 0
    )
    const cost = decisions.reduce(
      (sum, d) => sum + (d.timeline[period]?.cost ?? 0), 0
    )
    return { period: periodLabels[idx], pipeline, cost, net: pipeline - cost }
  })

  const containerWidth = container.clientWidth
  const margin = { top: 56, right: 24, bottom: 40, left: 60 }
  const width = containerWidth - margin.left - margin.right
  const height = 220
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  const titleText = selectedDecision.value
    ? `Timeline: ${selectedDecision.value.title}`
    : 'Aggregate 30/60/90 Day Projections'

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text(titleText.length > 50 ? titleText.slice(0, 48) + '…' : titleText)

  svg.append('text')
    .attr('x', margin.left)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', COLORS.muted)
    .text('Cumulative pipeline and cost projections')

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x0 = d3.scaleBand()
    .domain(periodLabels)
    .range([0, width])
    .paddingInner(0.3)
    .paddingOuter(0.15)

  const x1 = d3.scaleBand()
    .domain(['pipeline', 'cost'])
    .range([0, x0.bandwidth()])
    .padding(0.1)

  const maxVal = d3.max(timelineData, d => Math.max(d.pipeline, d.cost))
  const y = d3.scaleLinear()
    .domain([0, maxVal * 1.15])
    .range([height, 0])

  const yTicks = y.ticks(5)
  g.selectAll('.grid-line')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', COLORS.gridLine)
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#aaa')
    .text(d => formatCurrency(d))

  const groups = g.selectAll('.group')
    .data(timelineData)
    .join('g')
    .attr('transform', d => `translate(${x0(d.period)},0)`)

  // Pipeline bars
  groups.append('rect')
    .attr('x', x1('pipeline'))
    .attr('y', height)
    .attr('width', x1.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((d, i) => i * 120)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.pipeline))
    .attr('height', d => height - y(d.pipeline))

  // Cost bars
  groups.append('rect')
    .attr('x', x1('cost'))
    .attr('y', height)
    .attr('width', x1.bandwidth())
    .attr('height', 0)
    .attr('rx', 3)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0.65)
    .transition()
    .duration(600)
    .delay((d, i) => i * 120 + 60)
    .ease(d3.easeCubicOut)
    .attr('y', d => y(d.cost))
    .attr('height', d => height - y(d.cost))

  // Pipeline value labels
  groups.append('text')
    .attr('x', x1('pipeline') + x1.bandwidth() / 2)
    .attr('y', d => y(d.pipeline) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.primary)
    .style('opacity', 0)
    .text(d => formatCurrency(d.pipeline))
    .transition()
    .duration(300)
    .delay((d, i) => 600 + i * 120)
    .style('opacity', 1)

  // Cost value labels
  groups.append('text')
    .attr('x', x1('cost') + x1.bandwidth() / 2)
    .attr('y', d => y(d.cost) - 6)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.orange)
    .style('opacity', 0)
    .text(d => formatCurrency(d.cost))
    .transition()
    .duration(300)
    .delay((d, i) => 660 + i * 120)
    .style('opacity', 1)

  // X-axis labels
  g.selectAll('.x-label')
    .data(timelineData)
    .join('text')
    .attr('x', d => x0(d.period) + x0.bandwidth() / 2)
    .attr('y', height + 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '12px')
    .attr('font-weight', '500')
    .attr('fill', '#555')
    .text(d => d.period)

  // Legend
  const legend = svg.append('g')
    .attr('transform', `translate(${containerWidth - margin.right - 200}, 14)`)

  legend.append('rect')
    .attr('x', 0).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.primary)
    .attr('opacity', 0.85)

  legend.append('text')
    .attr('x', 16).attr('y', 9)
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text('Pipeline')

  legend.append('rect')
    .attr('x', 85).attr('y', 0)
    .attr('width', 10).attr('height', 10)
    .attr('rx', 2)
    .attr('fill', COLORS.orange)
    .attr('opacity', 0.65)

  legend.append('text')
    .attr('x', 101).attr('y', 9)
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text('Cost')
}

// --- Lifecycle ---

watch(() => props.scenarioId, () => fetchOutcomes())

onMounted(() => {
  fetchOutcomes()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      if (outcomes.value) renderCharts()
    }, 200)
  })
  if (impactChartRef.value) resizeObserver.observe(impactChartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="space-y-6">
    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-[var(--color-primary)] border-t-transparent" />
      <span class="ml-3 text-[var(--color-text-secondary)]">Loading outcome projections…</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Content -->
    <template v-else-if="outcomes">
      <!-- ROI Summary Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
          <div class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">Pipeline/mo</div>
          <div class="text-2xl font-bold text-[var(--color-primary)] mt-1">{{ formatCurrency(totalPipeline) }}</div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
          <div class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">Cost/mo</div>
          <div class="text-2xl font-bold text-[#ff5600] mt-1">{{ formatCurrency(totalCost) }}</div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
          <div class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">Net Impact</div>
          <div class="text-2xl font-bold mt-1" :class="netImpact >= 0 ? 'text-[#009900]' : 'text-[#ff5600]'">
            {{ formatCurrency(netImpact) }}
          </div>
        </div>
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
          <div class="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wide">Avg ROI</div>
          <div class="text-2xl font-bold text-[var(--color-primary)] mt-1">{{ avgRoi }}x</div>
        </div>
      </div>

      <!-- Impact vs Cost Chart -->
      <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
        <div ref="impactChartRef" class="w-full" />
      </div>

      <!-- Decision Cards -->
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Decision → Impact Mapping</h3>
        <div class="grid gap-3 md:grid-cols-2">
          <button
            v-for="decision in outcomes.decisions"
            :key="decision.id"
            class="text-left bg-[var(--color-surface)] border rounded-lg p-4 transition-all duration-150 hover:shadow-md"
            :class="selectedDecision?.id === decision.id
              ? 'border-[var(--color-primary)] ring-1 ring-[var(--color-primary)]'
              : 'border-[var(--color-border)]'"
            @click="selectDecision(decision)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-1 min-w-0">
                <div class="font-medium text-sm text-[var(--color-text)]">{{ decision.title }}</div>
                <div class="mt-1 text-xs text-[var(--color-text-muted)]">
                  <span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide"
                    :style="{ background: (CATEGORY_COLORS[decision.category] || COLORS.primary) + '18', color: CATEGORY_COLORS[decision.category] || COLORS.primary }">
                    {{ decision.category }}
                  </span>
                </div>
              </div>
              <div class="text-right shrink-0">
                <div class="text-sm font-bold" :style="{ color: CATEGORY_COLORS[decision.category] || COLORS.primary }">
                  +{{ formatCurrency(decision.impact.pipeline_per_month) }}
                </div>
                <div class="text-xs text-[var(--color-text-muted)]">
                  {{ decision.roi }}x ROI
                  <span class="ml-1 opacity-60">{{ Math.round(decision.confidence * 100) }}% conf</span>
                </div>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- Timeline Chart -->
      <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
        <div ref="timelineChartRef" class="w-full" />
      </div>
    </template>
  </div>
</template>
