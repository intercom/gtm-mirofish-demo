<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Object, default: () => null },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const viewMode = ref('cumulative') // 'cumulative' | 'density'

const CATEGORIES = ['product', 'customer', 'strategy', 'support', 'market', 'sentiment']

const CATEGORY_COLORS = {
  product: '#2068FF',
  customer: '#ff5600',
  strategy: '#AA00FF',
  support: '#009900',
  market: '#e68a00',
  sentiment: '#0891b2',
}

const CATEGORY_LABELS = {
  product: 'Product',
  customer: 'Customer',
  strategy: 'Strategy',
  support: 'Support',
  market: 'Market',
  sentiment: 'Sentiment',
}

const hasData = computed(() => {
  return props.data?.timeline?.length > 0
})

const timelineData = computed(() => {
  if (!hasData.value) return []
  return props.data.timeline
})

const events = computed(() => {
  if (!props.data?.events) return []
  return props.data.events
})

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container || !timelineData.value.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  if (viewMode.value === 'density') {
    renderDensity(container, containerWidth)
  } else {
    renderCumulative(container, containerWidth)
  }
}

function renderCumulative(container, containerWidth) {
  const data = timelineData.value
  const margin = { top: 12, right: 16, bottom: 32, left: 40 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Prepare stack data
  const stackData = data.map(d => {
    const row = { round: d.round_num }
    for (const cat of CATEGORIES) {
      row[cat] = d.cumulative[cat] || 0
    }
    return row
  })

  const x = d3.scaleLinear()
    .domain([data[0].round_num, data[data.length - 1].round_num])
    .range([0, width])

  const maxCumulative = d3.max(stackData, d =>
    CATEGORIES.reduce((sum, cat) => sum + d[cat], 0)
  ) || 1

  const y = d3.scaleLinear()
    .domain([0, maxCumulative * 1.1])
    .range([height, 0])

  // Stack
  const stack = d3.stack()
    .keys(CATEGORIES)
    .order(d3.stackOrderNone)

  const series = stack(stackData)

  const area = d3.area()
    .x(d => x(d.data.round))
    .y0(d => y(d[0]))
    .y1(d => y(d[1]))
    .curve(d3.curveMonotoneX)

  // Grid lines
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -6)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => d)

  // X-axis labels
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round_num))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round_num}`)

  // Stacked areas with animation
  g.selectAll('.area')
    .data(series)
    .join('path')
    .attr('d', area)
    .attr('fill', d => {
      const color = CATEGORY_COLORS[d.key] || '#888'
      return color + '40' // 25% opacity via hex alpha
    })
    .attr('stroke', d => CATEGORY_COLORS[d.key] || '#888')
    .attr('stroke-width', 1)
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((_, i) => i * 80)
    .style('opacity', 1)

  // Event markers — new concept emergence
  const eventData = events.value.filter(e => e.type === 'new_concept')
  const eventRounds = [...new Set(eventData.map(e => e.round_num))]

  g.selectAll('.event-marker')
    .data(eventRounds)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(32,104,255,0.2)')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')

  g.selectAll('.event-dot')
    .data(eventData.slice(0, 20)) // limit markers to avoid clutter
    .join('circle')
    .attr('cx', d => x(d.round_num))
    .attr('cy', 6)
    .attr('r', 0)
    .attr('fill', d => CATEGORY_COLORS[d.category] || '#888')
    .attr('stroke', '#fff')
    .attr('stroke-width', 1)
    .transition()
    .duration(300)
    .delay((_, i) => 600 + i * 30)
    .attr('r', 3)

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

  // Hover targets
  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round_num) : x(d.round_num)
      return (prev + x(d.round_num)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round_num) : x(d.round_num)
      const next = i < data.length - 1 ? x(data[i + 1].round_num) : x(d.round_num)
      return Math.max(8, ((x(d.round_num) - prev) + (next - x(d.round_num))) / 2)
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const cats = CATEGORIES
        .filter(c => d.cumulative[c] > 0)
        .sort((a, b) => d.cumulative[b] - d.cumulative[a])
      const catHtml = cats.map(c =>
        `<span style="color:${CATEGORY_COLORS[c]}">${CATEGORY_LABELS[c]}: ${d.cumulative[c]}</span>`
      ).join('<br/>')
      const newConcepts = d.new_concepts?.length
        ? `<div style="margin-top:4px;color:var(--color-primary,#2068FF);font-size:11px">+${d.new_concepts.length} new concept${d.new_concepts.length > 1 ? 's' : ''}</div>`
        : ''
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${d.round_num}</div>
          <div style="color:var(--color-text-muted,#888);margin-bottom:4px">${d.active_agents} agents · ${d.total_mentions} mentions</div>
          ${catHtml}
          ${newConcepts}
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
    })
}

function renderDensity(container, containerWidth) {
  const data = timelineData.value
  const margin = { top: 12, right: 16, bottom: 32, left: 40 }
  const width = containerWidth - margin.left - margin.right
  const height = 200
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const x = d3.scaleLinear()
    .domain([data[0].round_num, data[data.length - 1].round_num])
    .range([0, width])

  const maxMentions = d3.max(data, d => d.total_mentions) || 1

  const y = d3.scaleLinear()
    .domain([0, maxMentions * 1.15])
    .range([height, 0])

  // Grid
  const yTicks = y.ticks(5)
  g.selectAll('.grid')
    .data(yTicks)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  g.selectAll('.y-label')
    .data(yTicks)
    .join('text')
    .attr('x', -6).attr('y', d => y(d))
    .attr('dy', '0.35em').attr('text-anchor', 'end')
    .attr('font-size', '10px').attr('fill', '#888')
    .text(d => d)

  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round_num))
    .attr('y', height + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d.round_num}`)

  // Draw bars per category (grouped)
  const barWidth = Math.max(2, (width / data.length) * 0.7)

  for (const cat of CATEGORIES) {
    const line = d3.line()
      .x(d => x(d.round_num))
      .y(d => y(d.categories[cat] || 0))
      .curve(d3.curveMonotoneX)
      .defined(d => d.categories[cat] !== undefined)

    const path = g.append('path')
      .datum(data)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', CATEGORY_COLORS[cat])
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.8)

    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)
  }

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

  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round_num) : x(d.round_num)
      return (prev + x(d.round_num)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round_num) : x(d.round_num)
      const next = i < data.length - 1 ? x(data[i + 1].round_num) : x(d.round_num)
      return Math.max(8, ((x(d.round_num) - prev) + (next - x(d.round_num))) / 2)
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const cats = CATEGORIES
        .filter(c => (d.categories[c] || 0) > 0)
        .sort((a, b) => d.categories[b] - d.categories[a])
      const catHtml = cats.map(c =>
        `<span style="color:${CATEGORY_COLORS[c]}">${CATEGORY_LABELS[c]}: ${d.categories[c]}</span>`
      ).join('<br/>')
      tooltip
        .html(`
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:4px">Round ${d.round_num}</div>
          <div style="color:var(--color-text-muted,#888);margin-bottom:4px">${d.total_mentions} mentions</div>
          ${catHtml}
        `)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 12}px`)
        .style('top', `${event.clientY - rect.top - 40}px`)
    })
    .on('mouseleave', () => {
      tooltip.style('opacity', 0)
    })
}

// --- Lifecycle ---

watch([() => props.data, viewMode], () => {
  nextTick(() => renderChart())
}, { deep: true })

onMounted(() => {
  renderChart()
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderChart, 200)
    })
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Knowledge Timeline</h3>
      <div v-if="hasData" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'cumulative'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'cumulative'"
        >
          Cumulative
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'density'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'density'"
        >
          Per Round
        </button>
      </div>
    </div>

    <div v-if="hasData" class="relative" ref="chartRef" style="height: 244px" />

    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Knowledge data will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="hasData" class="flex flex-wrap items-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
      <span
        v-for="cat in CATEGORIES"
        :key="cat"
        class="flex items-center gap-1.5"
      >
        <span
          class="inline-block w-2.5 h-2 rounded-sm"
          :style="{ backgroundColor: CATEGORY_COLORS[cat] }"
        />
        {{ CATEGORY_LABELS[cat] }}
      </span>
    </div>

    <!-- Event summary -->
    <div v-if="events.length" class="mt-3 pt-3 border-t border-[var(--color-border)]">
      <p class="text-xs font-medium text-[var(--color-text-secondary)] mb-2">Key Moments</p>
      <div class="flex flex-wrap gap-1.5">
        <span
          v-for="(evt, i) in events.slice(0, 8)"
          :key="i"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium"
          :style="{
            backgroundColor: (CATEGORY_COLORS[evt.category] || '#888') + '18',
            color: CATEGORY_COLORS[evt.category] || '#888',
          }"
        >
          R{{ evt.round_num }}: {{ evt.keyword }}
        </span>
        <span
          v-if="events.length > 8"
          class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] text-[var(--color-text-muted)]"
        >
          +{{ events.length - 8 }} more
        </span>
      </div>
    </div>
  </div>
</template>
