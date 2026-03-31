<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useBeliefsStore } from '../../stores/beliefs'

const props = defineProps({
  actions: { type: Array, default: () => [] },
  simulationId: { type: String, default: '' },
})

const beliefsStore = useBeliefsStore()
const chartRef = ref(null)
const viewMode = ref('evolution') // 'evolution' | 'radar'
let resizeObserver = null
let resizeTimer = null

const DIMENSIONS = [
  { key: 'product_quality', label: 'Product Quality', color: '#2068FF' },
  { key: 'pricing', label: 'Pricing', color: '#ff5600' },
  { key: 'brand_trust', label: 'Brand Trust', color: '#009900' },
  { key: 'competitive_position', label: 'Competitive', color: '#AA00FF' },
  { key: 'adoption_intent', label: 'Adoption', color: '#E67E00' },
]

const beliefData = computed(() => {
  if (beliefsStore.hasData) return beliefsStore.rounds
  return extractLocal(props.actions)
})

const latestSnapshot = computed(() => {
  if (!beliefData.value.length) return null
  return beliefData.value[beliefData.value.length - 1]
})

// Local keyword extraction for real-time updates without hitting the API
function extractLocal(actions) {
  if (!actions.length) return []

  const KEYWORDS = {
    product_quality: {
      pos: ['impressive', 'innovative', 'reliable', 'powerful', 'robust', 'excellent', 'seamless'],
      neg: ['buggy', 'unreliable', 'clunky', 'outdated', 'limited', 'broken', 'slow'],
    },
    pricing: {
      pos: ['affordable', 'value', 'worth', 'reasonable', 'competitive', 'cost-effective'],
      neg: ['expensive', 'overpriced', 'costly', 'pricey', 'steep', 'unaffordable'],
    },
    brand_trust: {
      pos: ['trust', 'reliable', 'transparent', 'reputable', 'credible', 'proven'],
      neg: ['skeptical', 'distrust', 'misleading', 'questionable', 'doubt', 'suspicious'],
    },
    competitive_position: {
      pos: ['leader', 'best', 'ahead', 'dominant', 'preferred', 'winning', 'top'],
      neg: ['behind', 'losing', 'inferior', 'weaker', 'lagging', 'switch'],
    },
    adoption_intent: {
      pos: ['adopt', 'implement', 'migrate', 'purchase', 'subscribe', 'interested', 'excited'],
      neg: ['abandon', 'cancel', 'churn', 'leave', 'reject', 'avoid', 'defer'],
    },
  }

  const roundMap = new Map()
  for (const action of actions) {
    const rn = action.round_num
    if (rn == null) continue
    if (!roundMap.has(rn)) roundMap.set(rn, { agents: new Set(), scores: {} })
    const entry = roundMap.get(rn)
    entry.agents.add(action.agent_name || action.agent_id)
    const content = (action.action_args?.content || '').toLowerCase()

    for (const dim of DIMENSIONS) {
      if (!entry.scores[dim.key]) entry.scores[dim.key] = []
      const kw = KEYWORDS[dim.key]
      const pos = kw.pos.filter(w => content.includes(w)).length
      const neg = kw.neg.filter(w => content.includes(w)).length
      const total = pos + neg
      entry.scores[dim.key].push(total === 0 ? 0 : (pos - neg) / total)
    }
  }

  return Array.from(roundMap.keys()).sort((a, b) => a - b).map(rn => {
    const entry = roundMap.get(rn)
    const dimensions = {}
    for (const dim of DIMENSIONS) {
      const s = entry.scores[dim.key]
      dimensions[dim.key] = s.length ? +(s.reduce((a, b) => a + b, 0) / s.length).toFixed(3) : 0
    }
    return { round: rn, dimensions, agent_count: entry.agents.size, action_count: actions.filter(a => a.round_num === rn).length }
  })
}

// Try to fetch from backend when actions change significantly
let lastExtractCount = 0
watch(() => props.actions.length, (len) => {
  if (len > 0 && len - lastExtractCount >= 20) {
    lastExtractCount = len
    beliefsStore.extractBeliefs(props.simulationId, props.actions).catch(() => {})
  }
})

// --- D3 Rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  if (!chartRef.value || !beliefData.value.length) return
  const containerWidth = chartRef.value.clientWidth
  if (containerWidth === 0) return

  if (viewMode.value === 'radar') {
    renderRadar(chartRef.value, containerWidth)
  } else {
    renderEvolution(chartRef.value, containerWidth)
  }
}

function renderEvolution(container, containerWidth) {
  const data = beliefData.value
  const margin = { top: 16, right: 16, bottom: 32, left: 40 }
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
    .domain([data[0].round, data[data.length - 1].round])
    .range([0, width])

  const y = d3.scaleLinear()
    .domain([-0.6, 0.6])
    .range([height, 0])
    .clamp(true)

  // Grid
  const gridValues = [-0.4, -0.2, 0, 0.2, 0.4]
  g.selectAll('.grid')
    .data(gridValues)
    .join('line')
    .attr('x1', 0).attr('x2', width)
    .attr('y1', d => y(d)).attr('y2', d => y(d))
    .attr('stroke', d => d === 0 ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', d => d === 0 ? 'none' : '2,3')

  // Y-axis labels
  g.selectAll('.y-label')
    .data(gridValues)
    .join('text')
    .attr('x', -6).attr('y', d => y(d)).attr('dy', '0.35em')
    .attr('text-anchor', 'end').attr('font-size', '10px')
    .attr('fill', d => d > 0 ? '#009900' : d < 0 ? '#ff5600' : '#888')
    .text(d => d === 0 ? '0' : d > 0 ? `+${d.toFixed(1)}` : d.toFixed(1))

  // X-axis
  const step = Math.max(1, Math.floor(data.length / 8))
  g.selectAll('.x-label')
    .data(data.filter((_, i) => i % step === 0 || i === data.length - 1))
    .join('text')
    .attr('x', d => x(d.round)).attr('y', height + 20)
    .attr('text-anchor', 'middle').attr('font-size', '10px').attr('fill', '#888')
    .text(d => `R${d.round}`)

  // Draw a line per dimension
  for (const dim of DIMENSIONS) {
    const line = d3.line()
      .x(d => x(d.round))
      .y(d => y(d.dimensions[dim.key] || 0))
      .curve(d3.curveMonotoneX)

    const path = g.append('path')
      .datum(data)
      .attr('d', line)
      .attr('fill', 'none')
      .attr('stroke', dim.color)
      .attr('stroke-width', 2)
      .attr('opacity', 0.85)

    // Animate
    const totalLength = path.node().getTotalLength()
    path
      .attr('stroke-dasharray', `${totalLength} ${totalLength}`)
      .attr('stroke-dashoffset', totalLength)
      .transition().duration(800).ease(d3.easeCubicOut)
      .attr('stroke-dashoffset', 0)

    // End dots
    if (data.length > 0) {
      const last = data[data.length - 1]
      g.append('circle')
        .attr('cx', x(last.round))
        .attr('cy', y(last.dimensions[dim.key] || 0))
        .attr('r', 0)
        .attr('fill', dim.color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .transition().delay(800).duration(300)
        .attr('r', 4)
    }
  }

  // Tooltip overlay
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

  g.selectAll('.hover-target')
    .data(data)
    .join('rect')
    .attr('x', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round) : x(d.round)
      return (prev + x(d.round)) / 2
    })
    .attr('y', 0)
    .attr('width', (d, i) => {
      const prev = i > 0 ? x(data[i - 1].round) : x(d.round)
      const next = i < data.length - 1 ? x(data[i + 1].round) : x(d.round)
      return Math.max(8, ((x(d.round) - prev) + (next - x(d.round))) / 2)
    })
    .attr('height', height)
    .attr('fill', 'transparent')
    .attr('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      const lines = DIMENSIONS.map(dim => {
        const v = d.dimensions[dim.key] || 0
        const sign = v >= 0 ? '+' : ''
        return `<div style="display:flex;align-items:center;gap:6px;margin-top:3px">
          <span style="width:8px;height:8px;border-radius:50%;background:${dim.color};display:inline-block"></span>
          <span style="flex:1;color:var(--color-text-secondary,#555)">${dim.label}</span>
          <span style="font-weight:600;color:${v > 0.1 ? '#009900' : v < -0.1 ? '#ff5600' : '#888'}">${sign}${v.toFixed(2)}</span>
        </div>`
      }).join('')
      tooltip
        .html(`<div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:6px">Round ${d.round}</div>
          <div style="color:var(--color-text-muted,#888);font-size:11px;margin-bottom:4px">${d.agent_count} agents · ${d.action_count} actions</div>
          ${lines}`)
        .style('opacity', 1)
    })
    .on('mousemove', (event) => {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', `${event.clientX - rect.left + 14}px`)
        .style('top', `${event.clientY - rect.top - 60}px`)
    })
    .on('mouseleave', () => tooltip.style('opacity', 0))
}

function renderRadar(container, containerWidth) {
  const snapshot = latestSnapshot.value
  if (!snapshot) return

  const size = Math.min(containerWidth, 280)
  const cx = containerWidth / 2
  const cy = size / 2 + 16
  const radius = size / 2 - 40

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', size + 32)
    .attr('viewBox', `0 0 ${containerWidth} ${size + 32}`)

  const g = svg.append('g')
    .attr('transform', `translate(${cx},${cy})`)

  const angleSlice = (2 * Math.PI) / DIMENSIONS.length

  // Grid rings
  const rings = [0.2, 0.4, 0.6, 0.8, 1.0]
  for (const r of rings) {
    g.append('circle')
      .attr('r', radius * r)
      .attr('fill', 'none')
      .attr('stroke', 'rgba(0,0,0,0.08)')
      .attr('stroke-dasharray', r < 1 ? '2,3' : 'none')
  }

  // Zero ring (maps to score=0 at the midpoint of the radius)
  const zeroR = radius * 0.5
  g.append('circle')
    .attr('r', zeroR)
    .attr('fill', 'none')
    .attr('stroke', 'rgba(0,0,0,0.15)')

  // Axis lines + labels
  DIMENSIONS.forEach((dim, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const lx = Math.cos(angle) * radius
    const ly = Math.sin(angle) * radius

    g.append('line')
      .attr('x1', 0).attr('y1', 0)
      .attr('x2', lx).attr('y2', ly)
      .attr('stroke', 'rgba(0,0,0,0.08)')

    const labelR = radius + 18
    g.append('text')
      .attr('x', Math.cos(angle) * labelR)
      .attr('y', Math.sin(angle) * labelR)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '10px')
      .attr('fill', dim.color)
      .attr('font-weight', '600')
      .text(dim.label)
  })

  // Map score from [-1, 1] to [0, radius]: -1→0, 0→radius*0.5, 1→radius
  function scoreToRadius(score) {
    return radius * ((score + 1) / 2)
  }

  // Data polygon
  const points = DIMENSIONS.map((dim, i) => {
    const angle = angleSlice * i - Math.PI / 2
    const val = snapshot.dimensions[dim.key] || 0
    const r = scoreToRadius(val)
    return { x: Math.cos(angle) * r, y: Math.sin(angle) * r, dim, val }
  })

  const lineGen = d3.lineRadial()
    .angle((_, i) => angleSlice * i)
    .radius((d) => scoreToRadius(d.dimensions[DIMENSIONS[0].key]))
    .curve(d3.curveLinearClosed)

  // Fill polygon
  const polyPoints = points.map(p => `${p.x},${p.y}`).join(' ')
  g.append('polygon')
    .attr('points', polyPoints)
    .attr('fill', 'rgba(32, 104, 255, 0.1)')
    .attr('stroke', '#2068FF')
    .attr('stroke-width', 2)
    .style('opacity', 0)
    .transition().duration(600)
    .style('opacity', 1)

  // Vertex dots
  points.forEach(p => {
    g.append('circle')
      .attr('cx', p.x).attr('cy', p.y)
      .attr('r', 0)
      .attr('fill', p.dim.color)
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .transition().delay(600).duration(300)
      .attr('r', 5)
  })

  // Value labels at vertices
  points.forEach(p => {
    const sign = p.val >= 0 ? '+' : ''
    const angle = Math.atan2(p.y, p.x)
    const offset = 14
    g.append('text')
      .attr('x', p.x + Math.cos(angle) * offset)
      .attr('y', p.y + Math.sin(angle) * offset)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('fill', p.val > 0.1 ? '#009900' : p.val < -0.1 ? '#ff5600' : '#888')
      .text(`${sign}${p.val.toFixed(2)}`)
      .style('opacity', 0)
      .transition().delay(800).duration(300)
      .style('opacity', 1)
  })
}

// --- Lifecycle ---

watch([() => props.actions.length, viewMode], () => {
  nextTick(() => renderChart())
})

watch(() => beliefsStore.rounds, () => {
  nextTick(() => renderChart())
}, { deep: true })

onMounted(() => {
  beliefsStore.fetchDimensions().catch(() => {})
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
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Belief System Tracker</h3>
      <div v-if="beliefData.length" class="flex gap-1 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'evolution'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'evolution'"
        >
          Evolution
        </button>
        <button
          class="px-2.5 py-1 text-[11px] rounded font-medium transition-colors"
          :class="viewMode === 'radar'
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="viewMode = 'radar'"
        >
          Snapshot
        </button>
      </div>
    </div>

    <div v-if="beliefData.length" class="relative" ref="chartRef" :style="{ height: viewMode === 'radar' ? '320px' : '248px' }" />

    <div v-else class="flex items-center justify-center h-[200px] text-[var(--color-text-muted)] text-sm">
      <span>Belief data will appear as agents interact</span>
    </div>

    <!-- Legend -->
    <div v-if="beliefData.length" class="flex flex-wrap items-center gap-3 mt-3 text-xs text-[var(--color-text-muted)]">
      <span v-for="dim in DIMENSIONS" :key="dim.key" class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full" :style="{ background: dim.color }" />
        {{ dim.label }}
      </span>
    </div>

    <!-- Mode badge -->
    <div v-if="beliefsStore.mode" class="mt-2 text-[10px] text-[var(--color-text-muted)]">
      Analysis: {{ beliefsStore.mode === 'llm' ? 'LLM' : beliefsStore.mode === 'keyword' ? 'Keyword' : 'Demo' }}
    </div>
  </div>
</template>
