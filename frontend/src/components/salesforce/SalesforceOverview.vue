<script setup>
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useSalesforceStore } from '../../stores/salesforce'
import { useCountUp } from '../../composables/useCountUp'
import ShimmerCard from '../ui/ShimmerCard.vue'

const store = useSalesforceStore()

const animatedAccounts = useCountUp(computed(() => store.totalAccounts))
const animatedHealthScore = useCountUp(computed(() => store.avgHealthScore))

function formatCurrency(value) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value}`
}

function healthScoreColor(score) {
  if (score >= 80) return 'var(--color-success)'
  if (score >= 60) return 'var(--color-warning)'
  return 'var(--color-error)'
}

const statCards = computed(() => [
  {
    label: 'Total Accounts',
    value: animatedAccounts.value.toLocaleString(),
    icon: 'accounts',
    color: 'var(--color-primary)',
  },
  {
    label: 'Total ARR',
    value: formatCurrency(store.totalArr),
    icon: 'arr',
    color: 'var(--color-success)',
  },
  {
    label: 'Avg Health Score',
    value: animatedHealthScore.value,
    icon: 'health',
    color: healthScoreColor(store.avgHealthScore),
  },
  {
    label: 'Pipeline Value',
    value: formatCurrency(store.pipelineValue),
    icon: 'pipeline',
    color: 'var(--color-fin-orange)',
  },
])

// --- D3 Charts ---

const donutRef = ref(null)
const barRef = ref(null)
let donutObserver = null
let barObserver = null
let donutTimer = null
let barTimer = null

const CHART_COLORS = ['#2068FF', '#ff5600', '#009900', '#f59e0b', '#AA00FF', '#888888']

function clearEl(el) {
  if (el) d3.select(el).selectAll('*').remove()
}

function renderDonut() {
  const container = donutRef.value
  if (!container || !store.industryBreakdown.length) return
  clearEl(container)

  const data = store.industryBreakdown
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const size = Math.min(containerWidth, 240)
  const radius = size / 2
  const innerRadius = radius * 0.55

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', size)
    .append('g')
    .attr('transform', `translate(${containerWidth / 2},${size / 2})`)

  const pie = d3.pie()
    .value(d => d.count)
    .sort(null)
    .padAngle(0.02)

  const arc = d3.arc()
    .innerRadius(innerRadius)
    .outerRadius(radius - 4)
    .cornerRadius(3)

  const color = d3.scaleOrdinal()
    .domain(data.map(d => d.industry))
    .range(CHART_COLORS)

  const arcs = svg.selectAll('.arc')
    .data(pie(data))
    .join('g')
    .attr('class', 'arc')

  arcs.append('path')
    .attr('d', arc)
    .attr('fill', d => color(d.data.industry))
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((_, i) => i * 80)
    .style('opacity', 1)
    .attrTween('d', function (d) {
      const interpolate = d3.interpolate({ startAngle: d.startAngle, endAngle: d.startAngle }, d)
      return t => arc(interpolate(t))
    })

  // Center total label
  const total = data.reduce((s, d) => s + d.count, 0)
  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .attr('font-size', '22px')
    .attr('font-weight', '700')
    .attr('fill', 'var(--color-text)')
    .text(total)

  svg.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .attr('font-size', '11px')
    .attr('fill', 'var(--color-text-muted)')
    .text('accounts')

  // Legend
  const legend = d3.select(container)
    .append('div')
    .style('display', 'flex')
    .style('flex-wrap', 'wrap')
    .style('gap', '8px 16px')
    .style('justify-content', 'center')
    .style('margin-top', '12px')

  data.forEach((d, i) => {
    const item = legend.append('span')
      .style('display', 'flex')
      .style('align-items', 'center')
      .style('gap', '6px')
      .style('font-size', '12px')
      .style('color', 'var(--color-text-muted)')

    item.append('span')
      .style('width', '8px')
      .style('height', '8px')
      .style('border-radius', '2px')
      .style('background', CHART_COLORS[i])
      .style('flex-shrink', '0')

    item.append('span').text(`${d.industry} (${d.count})`)
  })
}

function renderBar() {
  const container = barRef.value
  if (!container || !store.stageDistribution.length) return
  clearEl(container)

  const data = store.stageDistribution
  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 8, right: 12, bottom: 28, left: 80 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 28
  const gap = 6
  const height = data.length * (barHeight + gap) - gap
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = d3.max(data, d => d.count)

  const x = d3.scaleLinear()
    .domain([0, maxVal])
    .range([0, width])

  const y = d3.scaleBand()
    .domain(data.map(d => d.stage))
    .range([0, height])
    .padding(gap / (barHeight + gap))

  // Stage labels
  g.selectAll('.label')
    .data(data)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d.stage) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '12px')
    .attr('fill', 'var(--color-text-secondary)')
    .text(d => d.stage)

  // Bar background
  g.selectAll('.bar-bg')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.stage))
    .attr('width', width)
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', 'var(--color-tint)')

  // Color per stage
  function stageColor(stage) {
    if (stage === 'Closed Won') return 'var(--color-success)'
    if (stage === 'Closed Lost') return 'var(--color-error)'
    return 'var(--color-primary)'
  }

  // Animated bars
  g.selectAll('.bar')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.stage))
    .attr('width', 0)
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', d => stageColor(d.stage))
    .style('opacity', 0.85)
    .transition()
    .duration(600)
    .delay((_, i) => i * 80)
    .attr('width', d => x(d.count))

  // Count labels
  g.selectAll('.count')
    .data(data)
    .join('text')
    .attr('x', d => x(d.count) + 6)
    .attr('y', d => y(d.stage) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .attr('fill', 'var(--color-text)')
    .style('opacity', 0)
    .text(d => d.count)
    .transition()
    .duration(300)
    .delay((_, i) => 600 + i * 80)
    .style('opacity', 1)
}

function setupObserver(elRef, renderFn, timerRef) {
  const el = elRef.value
  if (!el) return null
  const observer = new ResizeObserver(() => {
    clearTimeout(timerRef.value)
    timerRef.value = setTimeout(renderFn, 200)
  })
  observer.observe(el)
  return observer
}

// Use object refs for timers so setupObserver can clear them
const donutTimerRef = { value: null }
const barTimerRef = { value: null }

watch(
  () => [store.industryBreakdown.length, store.stageDistribution.length],
  () => nextTick(() => { renderDonut(); renderBar() }),
)

onMounted(() => {
  if (!store.stats && !store.loading) store.fetchStats()
  nextTick(() => {
    renderDonut()
    renderBar()
    donutObserver = setupObserver(donutRef, renderDonut, donutTimerRef)
    barObserver = setupObserver(barRef, renderBar, barTimerRef)
  })
})

onUnmounted(() => {
  if (donutObserver) donutObserver.disconnect()
  if (barObserver) barObserver.disconnect()
  clearTimeout(donutTimerRef.value)
  clearTimeout(barTimerRef.value)
})
</script>

<template>
  <section>
    <!-- Stat Cards -->
    <div v-if="store.loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <ShimmerCard v-for="i in 4" :key="i" :lines="2" height="88px" />
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div
        v-for="card in statCards"
        :key="card.label"
        class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-5 flex items-start gap-4"
        style="box-shadow: var(--card-shadow)"
      >
        <!-- Icon -->
        <div
          class="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0"
          :style="{ background: card.color + '14' }"
        >
          <!-- Accounts -->
          <svg v-if="card.icon === 'accounts'" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" :fill="card.color" />
          </svg>
          <!-- ARR -->
          <svg v-else-if="card.icon === 'arr'" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v1H8a1 1 0 100 2h3a1 1 0 010 2H8a1 1 0 100 2h1v1a1 1 0 102 0v-1a3 3 0 001-5.83V7z" :fill="card.color" />
          </svg>
          <!-- Health -->
          <svg v-else-if="card.icon === 'health'" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" :fill="card.color" />
          </svg>
          <!-- Pipeline -->
          <svg v-else-if="card.icon === 'pipeline'" width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zm6-4a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zm6-3a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" :fill="card.color" />
          </svg>
        </div>

        <div class="min-w-0">
          <div class="text-2xl font-bold text-[var(--color-text)] leading-tight" :style="card.icon === 'health' ? { color: card.color } : {}">
            {{ card.value }}
          </div>
          <div class="text-sm text-[var(--color-text-muted)] mt-0.5">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div v-if="store.loading" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <ShimmerCard :lines="6" height="320px" />
      <ShimmerCard :lines="6" height="320px" />
    </div>

    <div v-else-if="store.error" class="text-center py-12 text-[var(--color-error)]">
      {{ store.error }}
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- Industry Donut -->
      <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-5" style="box-shadow: var(--card-shadow)">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Industry Breakdown</h3>
        <div ref="donutRef" class="flex flex-col items-center" />
      </div>

      <!-- Stage Bar Chart -->
      <div class="bg-[var(--card-bg)] border border-[var(--card-border)] rounded-[var(--card-radius)] p-5" style="box-shadow: var(--card-shadow)">
        <h3 class="text-sm font-semibold text-[var(--color-text)] mb-4">Pipeline by Stage</h3>
        <div ref="barRef" />
      </div>
    </div>
  </section>
</template>
