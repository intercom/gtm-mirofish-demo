<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  history: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// Stage transitions
const TRANSITIONS = [
  { key: 'lead_to_mql', label: 'Lead → MQL', color: '#2068FF' },
  { key: 'mql_to_sql', label: 'MQL → SQL', color: '#AA00FF' },
  { key: 'sql_to_sao', label: 'SQL → SAO', color: '#009900' },
  { key: 'sao_to_proposal', label: 'SAO → Proposal', color: '#ff5600' },
  { key: 'proposal_to_won', label: 'Proposal → Won', color: '#050505' },
]

// Toggleable line visibility
const visibleLines = ref(new Set(TRANSITIONS.map(t => t.key)))

function toggleLine(key) {
  const next = new Set(visibleLines.value)
  if (next.has(key)) {
    if (next.size > 1) next.delete(key)
  } else {
    next.add(key)
  }
  visibleLines.value = next
}

// Generate 6 months of realistic demo data when no API data is provided
function generateDemoData() {
  const months = ['Oct 2025', 'Nov 2025', 'Dec 2025', 'Jan 2026', 'Feb 2026', 'Mar 2026']
  const baseRates = {
    lead_to_mql: 32,
    mql_to_sql: 45,
    sql_to_sao: 58,
    sao_to_proposal: 72,
    proposal_to_won: 28,
  }
  // Seasonal patterns: Q4 boost, Q1 dip
  const seasonal = [1.08, 1.12, 1.15, 0.90, 0.93, 0.97]

  // Seeded PRNG for determinism
  let seed = 42
  function rand() {
    seed = (seed * 16807 + 0) % 2147483647
    return (seed - 1) / 2147483646
  }

  return months.map((month, i) => {
    const entry = { month }
    for (const t of TRANSITIONS) {
      const base = baseRates[t.key]
      const variance = (rand() - 0.5) * base * 0.2
      entry[t.key] = Math.max(2, Math.min(98, +(base * seasonal[i] + variance).toFixed(1)))
    }
    return entry
  })
}

const chartData = computed(() => {
  if (props.history && props.history.length) return props.history
  return generateDemoData()
})

// Averages per transition
const averages = computed(() => {
  const data = chartData.value
  const avgs = {}
  for (const t of TRANSITIONS) {
    const vals = data.map(d => d[t.key]).filter(v => v != null)
    avgs[t.key] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0
  }
  return avgs
})

// Annotations: >5% MoM change
const annotations = computed(() => {
  const data = chartData.value
  const notes = []
  for (let i = 1; i < data.length; i++) {
    for (const t of TRANSITIONS) {
      const prev = data[i - 1][t.key]
      const curr = data[i][t.key]
      if (prev == null || curr == null) continue
      const delta = curr - prev
      if (Math.abs(delta) > 5) {
        notes.push({
          monthIndex: i,
          key: t.key,
          delta,
          value: curr,
          label: t.label,
          color: t.color,
        })
      }
    }
  }
  return notes
})

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) {
    d3.select(chartRef.value).selectAll('*').remove()
  }
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const data = chartData.value
  if (!data.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 24, right: 20, bottom: 36, left: 44 }
  const width = containerWidth - margin.left - margin.right
  const height = 280
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const x = d3.scalePoint()
    .domain(data.map(d => d.month))
    .range([0, width])
    .padding(0.1)

  const y = d3.scaleLinear()
    .domain([0, 100])
    .range([height, 0])

  // Grid lines
  const gridValues = [0, 20, 40, 60, 80, 100]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', d => y(d))
    .attr('y2', d => y(d))
    .attr('stroke', d => d === 0 ? 'rgba(0,0,0,0.12)' : 'rgba(0,0,0,0.05)')
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(gridValues)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d))
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `${d}%`)

  // X-axis labels
  g.selectAll('.x-label')
    .data(data)
    .join('text')
    .attr('x', d => x(d.month))
    .attr('y', height + 22)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => d.month)

  // Dashed average lines for visible transitions
  const visible = visibleLines.value
  for (const t of TRANSITIONS) {
    if (!visible.has(t.key)) continue
    const avg = averages.value[t.key]
    g.append('line')
      .attr('x1', 0)
      .attr('x2', width)
      .attr('y1', y(avg))
      .attr('y2', y(avg))
      .attr('stroke', t.color)
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '4,4')
      .attr('opacity', 0.35)
  }

  // Line generator
  const line = d3.line()
    .x(d => x(d.month))
    .y(d => y(d.value))
    .curve(d3.curveMonotoneX)

  // Draw lines + dots per transition
  const allDots = []
  for (const t of TRANSITIONS) {
    if (!visible.has(t.key)) continue

    const lineData = data.map(d => ({ month: d.month, value: d[t.key] }))

    // Line path
    const path = g.append('path')
      .datum(lineData)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', t.color)
      .attr('stroke-width', 2.5)
      .attr('stroke-linejoin', 'round')
      .attr('stroke-linecap', 'round')

    // Animate drawing
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(800)
      .ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // Data points
    const dots = g.selectAll(`.dot-${t.key}`)
      .data(lineData)
      .join('circle')
      .attr('class', `dot-${t.key}`)
      .attr('cx', d => x(d.month))
      .attr('cy', d => y(d.value))
      .attr('r', 0)
      .attr('fill', t.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)

    dots.transition()
      .duration(300)
      .delay((_, i) => 800 + i * 60)
      .attr('r', 4)

    allDots.push({ key: t.key, color: t.color, dots })
  }

  // Annotation markers for >5% MoM changes
  const visibleAnnotations = annotations.value.filter(a => visible.has(a.key))
  // Limit to top 3 most significant to avoid clutter
  const topAnnotations = visibleAnnotations
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))
    .slice(0, 3)

  for (const ann of topAnnotations) {
    const cx = x(data[ann.monthIndex].month)
    const cy = y(ann.value)
    const sign = ann.delta > 0 ? '+' : ''
    const offsetY = ann.delta > 0 ? -18 : 18

    g.append('text')
      .attr('x', cx)
      .attr('y', cy + offsetY)
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('font-weight', '600')
      .attr('fill', ann.delta > 0 ? '#009900' : '#ff5600')
      .text(`${sign}${ann.delta.toFixed(1)}%`)
      .style('opacity', 0)
      .transition()
      .delay(1200)
      .duration(300)
      .style('opacity', 1)
  }

  // Crosshair + tooltip on hover
  const crosshairLine = g.append('line')
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.15)')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '3,3')
    .style('opacity', 0)

  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('pointer-events', 'none')
    .style('opacity', 0)
    .style('background', 'var(--color-surface, #fff)')
    .style('border', '1px solid var(--color-border, rgba(0,0,0,0.1))')
    .style('border-radius', '8px')
    .style('padding', '10px 14px')
    .style('font-size', '12px')
    .style('box-shadow', '0 4px 12px rgba(0,0,0,0.1)')
    .style('z-index', '10')
    .style('min-width', '160px')

  // Invisible hover rects per month
  const monthWidth = data.length > 1 ? x(data[1].month) - x(data[0].month) : width
  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', d => x(d.month) - monthWidth / 2)
    .attr('y', 0)
    .attr('width', monthWidth)
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'crosshair')
    .on('mouseenter', (event, d) => {
      const cx = x(d.month)
      crosshairLine
        .attr('x1', cx)
        .attr('x2', cx)
        .style('opacity', 1)

      // Build tooltip content
      let html = `<div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:6px">${d.month}</div>`
      for (const t of TRANSITIONS) {
        if (!visible.has(t.key)) continue
        const val = d[t.key]
        if (val == null) continue
        html += `<div style="display:flex;justify-content:space-between;gap:12px;margin-top:3px">
          <span style="display:flex;align-items:center;gap:5px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${t.color}"></span>
            <span style="color:var(--color-text-secondary,#555)">${t.label}</span>
          </span>
          <span style="font-weight:600;color:var(--color-text,#050505)">${val.toFixed(1)}%</span>
        </div>`
      }
      tooltip.html(html).style('opacity', 1)

      // Highlight dots at this month
      for (const { key, dots } of allDots) {
        dots.filter(dd => dd.month === d.month)
          .transition().duration(80)
          .attr('r', 6)
      }
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      const tipWidth = 180
      let left = event.clientX - rect.left + 14
      if (left + tipWidth > containerWidth) left = event.clientX - rect.left - tipWidth - 14
      tooltip
        .style('left', `${left}px`)
        .style('top', `${event.clientY - rect.top - 20}px`)
    })
    .on('mouseleave', (event, d) => {
      crosshairLine.style('opacity', 0)
      tooltip.style('opacity', 0)
      for (const { dots } of allDots) {
        dots.filter(dd => dd.month === d.month)
          .transition().duration(80)
          .attr('r', 4)
      }
    })
}

// --- Lifecycle ---

watch([chartData, visibleLines], () => {
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
      <div>
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Conversion Trends</h3>
        <p class="text-[11px] text-[var(--color-text-muted)] mt-0.5">Stage-to-stage conversion rates over time</p>
      </div>
    </div>

    <div ref="chartRef" class="relative" style="height: 340px" />

    <!-- Legend with toggleable lines -->
    <div class="flex flex-wrap items-center gap-x-4 gap-y-2 mt-3">
      <button
        v-for="t in TRANSITIONS"
        :key="t.key"
        class="flex items-center gap-1.5 text-xs transition-opacity cursor-pointer"
        :class="visibleLines.has(t.key) ? 'opacity-100' : 'opacity-35'"
        @click="toggleLine(t.key)"
      >
        <span
          class="inline-block w-3 h-[3px] rounded-full"
          :style="{ background: t.color }"
        />
        <span class="text-[var(--color-text-muted)]">{{ t.label }}</span>
      </button>
    </div>
  </div>
</template>
