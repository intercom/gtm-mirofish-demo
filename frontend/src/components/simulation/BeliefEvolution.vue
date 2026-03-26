<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  actions: { type: Array, default: () => [] },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

// --- Belief topic definitions with keyword scoring ---

const BELIEF_TOPICS = [
  {
    key: 'product_quality',
    label: 'Product Quality',
    positive: ['quality', 'reliable', 'robust', 'solid', 'polished', 'impressive', 'excellent', 'powerful', 'innovative', 'seamless'],
    negative: ['buggy', 'unreliable', 'poor', 'broken', 'lacking', 'unstable', 'immature', 'clunky', 'confusing', 'limited'],
  },
  {
    key: 'market_timing',
    label: 'Market Timing',
    positive: ['right time', 'growing', 'demand', 'trending', 'momentum', 'opportunity', 'exciting', 'promising', 'emerging'],
    negative: ['too early', 'too late', 'saturated', 'declining', 'slowdown', 'bad timing', 'premature', 'overcrowded'],
  },
  {
    key: 'competitive_position',
    label: 'Competitive Position',
    positive: ['differentiated', 'unique', 'first mover', 'advantage', 'better', 'leading', 'ahead', 'superior', 'unmatched'],
    negative: ['competitor', 'threat', 'losing', 'behind', 'catch up', 'commoditized', 'outpaced', 'weaker', 'copied'],
  },
  {
    key: 'value_proposition',
    label: 'Value Proposition',
    positive: ['valuable', 'worth', 'save', 'efficient', 'cost-effective', 'benefit', 'roi', 'compelling', 'transformative'],
    negative: ['expensive', 'overpriced', 'not worth', 'waste', 'costly', 'questionable', 'unclear value', 'no benefit'],
  },
  {
    key: 'adoption_readiness',
    label: 'Adoption Readiness',
    positive: ['ready', 'interested', 'eager', 'adopt', 'implement', 'integrate', 'onboard', 'committed', 'champion'],
    negative: ['concerned', 'skeptical', 'hesitant', 'resist', 'risk', 'worry', 'doubt', 'afraid', 'dismiss'],
  },
]

function scoreBelief(content, topic) {
  if (!content) return { value: 0, confidence: 0.2 }
  const lower = content.toLowerCase()
  let pos = 0
  let neg = 0
  for (const w of topic.positive) {
    if (lower.includes(w)) pos++
  }
  for (const w of topic.negative) {
    if (lower.includes(w)) neg++
  }
  const total = pos + neg
  if (total === 0) return { value: 0, confidence: 0.2 }
  return {
    value: (pos - neg) / total,
    confidence: Math.min(1, 0.3 + total * 0.15),
  }
}

// --- Seeded PRNG for deterministic demo data ---

function seededRandom(seed) {
  let s = seed | 0
  return () => {
    s = (s * 1664525 + 1013904223) | 0
    return (s >>> 0) / 0xffffffff
  }
}

const DEMO_TRIGGERS = [
  'Competitor launched new feature',
  'Positive customer testimonial shared',
  'Market analyst published bearish report',
  'Successful product demo to key account',
  'Team member raised budget concerns',
  'Industry event generated positive buzz',
  'Customer churn data surfaced in meeting',
  'New strategic partnership announced',
]

function generateDemoData() {
  const rand = seededRandom(42)
  const rounds = 10
  const patterns = [
    { start: 0.6, trend: 0.04, volatility: 0.1, flipAt: 7 },
    { start: -0.2, trend: 0.1, volatility: 0.15, flipAt: 4 },
    { start: -0.4, trend: -0.03, volatility: 0.2, flipAt: 5 },
    { start: 0.5, trend: 0.02, volatility: 0.08, flipAt: null },
    { start: 0.1, trend: 0.08, volatility: 0.12, flipAt: 6 },
  ]

  return BELIEF_TOPICS.map((topic, ti) => {
    const p = patterns[ti]
    let current = p.start
    let conf = 0.55 + rand() * 0.35
    const data = []

    for (let r = 1; r <= rounds; r++) {
      const noise = (rand() - 0.5) * p.volatility * 2
      if (p.flipAt && r === p.flipAt) {
        current = -current * 0.7
        conf = Math.max(0.3, conf - 0.2)
      } else {
        current += p.trend + noise
      }
      current = Math.max(-1, Math.min(1, current))
      conf = Math.max(0.2, Math.min(1, conf + (rand() - 0.5) * 0.1))

      const prev = data.length > 0 ? data[data.length - 1] : null
      const changed = prev && Math.sign(prev.value) !== Math.sign(current) && Math.abs(current) > 0.12

      data.push({
        round: r,
        value: current,
        confidence: conf,
        trigger: changed ? DEMO_TRIGGERS[Math.floor(rand() * DEMO_TRIGGERS.length)] : null,
        changed: !!changed,
      })
    }
    return { label: topic.label, data }
  })
}

let _cachedDemoData = null

// --- Computed belief data ---

const beliefData = computed(() => {
  if (!props.actions.length) {
    if (!_cachedDemoData) _cachedDemoData = generateDemoData()
    return _cachedDemoData
  }

  const roundMap = new Map()
  for (const action of props.actions) {
    const round = action.round_num
    if (round == null) continue
    if (!roundMap.has(round)) roundMap.set(round, [])
    roundMap.get(round).push(action)
  }
  if (roundMap.size === 0) {
    if (!_cachedDemoData) _cachedDemoData = generateDemoData()
    return _cachedDemoData
  }

  const rounds = Array.from(roundMap.keys()).sort((a, b) => a - b)

  return BELIEF_TOPICS.map(topic => {
    const data = []
    for (const round of rounds) {
      const actions = roundMap.get(round)
      const scores = actions.map(a => scoreBelief(a.action_args?.content || '', topic))
      const avgValue = scores.reduce((s, sc) => s + sc.value, 0) / scores.length
      const avgConf = scores.reduce((s, sc) => s + sc.confidence, 0) / scores.length
      const value = Math.max(-1, Math.min(1, avgValue))
      const prev = data.length > 0 ? data[data.length - 1] : null
      const changed = prev && Math.sign(prev.value) !== Math.sign(value) && Math.abs(value) > 0.12

      data.push({
        round,
        value,
        confidence: avgConf,
        trigger: changed ? `Belief shifted in round ${round}` : null,
        changed: !!changed,
      })
    }
    return { label: topic.label, data }
  })
})

const summary = computed(() => {
  let totalChanges = 0
  let maxChanges = 0
  let mostVolatile = ''

  for (const topic of beliefData.value) {
    const changes = topic.data.filter(d => d.changed).length
    totalChanges += changes
    if (changes > maxChanges) {
      maxChanges = changes
      mostVolatile = topic.label
    }
  }
  return { totalChanges, mostVolatile: mostVolatile || beliefData.value[0]?.label || 'N/A' }
})

const isDemo = computed(() => !props.actions.length)

// --- Color helpers ---

function valueToColor(v) {
  if (v > 0.12) return '#009900'
  if (v < -0.12) return '#ff5600'
  return '#2068FF'
}

function valueToLabel(v) {
  if (v > 0.12) return 'Positive'
  if (v < -0.12) return 'Negative'
  return 'Neutral'
}

// --- D3 rendering ---

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return
  const topics = beliefData.value
  if (!topics.length || !topics[0].data.length) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { top: 8, right: 16, bottom: 28, left: 130 }
  const bandHeight = 32
  const bandGap = 6
  const width = containerWidth - margin.left - margin.right
  const chartHeight = topics.length * bandHeight + (topics.length - 1) * bandGap
  const totalHeight = chartHeight + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const defs = svg.append('defs')
  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const roundExtent = d3.extent(topics[0].data, d => d.round)

  const x = d3.scaleLinear()
    .domain(roundExtent)
    .range([0, width])

  // Vertical grid
  const roundValues = topics[0].data.map(d => d.round)
  g.selectAll('.grid-v')
    .data(roundValues)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', chartHeight)
    .attr('stroke', 'rgba(0,0,0,0.04)')
    .attr('stroke-dasharray', '2,4')

  // X-axis labels
  const step = Math.max(1, Math.floor(roundValues.length / 10))
  g.selectAll('.x-label')
    .data(roundValues.filter((_, i) => i % step === 0 || i === roundValues.length - 1))
    .join('text')
    .attr('x', d => x(d))
    .attr('y', chartHeight + 18)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('fill', '#888')
    .text(d => `R${d}`)

  // Render each belief topic band
  topics.forEach((topic, ti) => {
    const bandY = ti * (bandHeight + bandGap)
    const bw = bandHeight

    // Topic label
    g.append('text')
      .attr('x', -10)
      .attr('y', bandY + bw / 2)
      .attr('dy', '0.35em')
      .attr('text-anchor', 'end')
      .attr('font-size', '11px')
      .attr('font-weight', '500')
      .attr('fill', 'var(--color-text, #1a1a1a)')
      .text(topic.label)

    // Background band
    g.append('rect')
      .attr('x', 0)
      .attr('y', bandY)
      .attr('width', width)
      .attr('height', bw)
      .attr('fill', 'rgba(0,0,0,0.02)')
      .attr('rx', 4)

    // Per-topic horizontal gradient (colors shift with belief value)
    const gradId = `belief-grad-${ti}`
    const grad = defs.append('linearGradient')
      .attr('id', gradId)
      .attr('gradientUnits', 'userSpaceOnUse')
      .attr('x1', x(roundExtent[0]))
      .attr('y1', 0)
      .attr('x2', x(roundExtent[1]))
      .attr('y2', 0)

    topic.data.forEach(d => {
      const pct = roundExtent[1] === roundExtent[0]
        ? 50
        : ((d.round - roundExtent[0]) / (roundExtent[1] - roundExtent[0])) * 100
      grad.append('stop')
        .attr('offset', `${pct}%`)
        .attr('stop-color', valueToColor(d.value))
        .attr('stop-opacity', 0.55)
    })

    // Belief ribbon — area whose vertical extent = confidence × band height
    const area = d3.area()
      .x(d => x(d.round))
      .y0(d => bandY + bw / 2 + (bw / 2) * d.confidence * 0.85)
      .y1(d => bandY + bw / 2 - (bw / 2) * d.confidence * 0.85)
      .curve(d3.curveMonotoneX)

    g.append('path')
      .datum(topic.data)
      .attr('d', area)
      .attr('fill', `url(#${gradId})`)
      .style('opacity', 0)
      .transition()
      .duration(500)
      .delay(ti * 70)
      .style('opacity', 1)

    // Center trend line
    g.append('line')
      .attr('x1', x(roundExtent[0]))
      .attr('x2', x(roundExtent[1]))
      .attr('y1', bandY + bw / 2)
      .attr('y2', bandY + bw / 2)
      .attr('stroke', 'rgba(0,0,0,0.06)')
      .attr('stroke-width', 0.5)

    // Change markers — dashed vertical lines + dots
    const changes = topic.data.filter(d => d.changed)

    g.selectAll(null)
      .data(changes)
      .join('line')
      .attr('x1', d => x(d.round))
      .attr('x2', d => x(d.round))
      .attr('y1', bandY + 3)
      .attr('y2', bandY + bw - 3)
      .attr('stroke', '#AA00FF')
      .attr('stroke-width', 1.5)
      .attr('stroke-dasharray', '3,3')
      .style('opacity', 0)
      .transition()
      .duration(250)
      .delay(ti * 70 + 500)
      .style('opacity', 0.65)

    g.selectAll(null)
      .data(changes)
      .join('circle')
      .attr('cx', d => x(d.round))
      .attr('cy', bandY + bw / 2)
      .attr('r', 0)
      .attr('fill', '#AA00FF')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)
      .transition()
      .duration(250)
      .delay(ti * 70 + 600)
      .attr('r', 3.5)
  })

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
    .style('max-width', '240px')

  // Invisible hover targets per topic × round
  topics.forEach((topic, ti) => {
    const bandY = ti * (bandHeight + bandGap)
    const bw = bandHeight
    const data = topic.data

    g.selectAll(null)
      .data(data)
      .join('rect')
      .attr('x', (d, i) => {
        if (i === 0) return 0
        return (x(data[i - 1].round) + x(d.round)) / 2
      })
      .attr('y', bandY)
      .attr('width', (d, i) => {
        const left = i === 0 ? 0 : (x(data[i - 1].round) + x(d.round)) / 2
        const right = i === data.length - 1 ? width : (x(d.round) + x(data[i + 1].round)) / 2
        return Math.max(0, right - left)
      })
      .attr('height', bw)
      .attr('fill', 'transparent')
      .attr('cursor', 'pointer')
      .on('mouseenter', (event, d) => {
        const color = valueToColor(d.value)
        const label = valueToLabel(d.value)
        let html = `
          <div style="font-weight:600;color:var(--color-text,#050505);margin-bottom:3px">${topic.label}</div>
          <div style="color:${color};font-weight:600">${label} (${d.value >= 0 ? '+' : ''}${d.value.toFixed(2)})</div>
          <div style="color:var(--color-text-muted,#888);margin-top:2px">
            Round ${d.round} · Confidence ${Math.round(d.confidence * 100)}%
          </div>
        `
        if (d.trigger) {
          html += `<div style="color:#AA00FF;margin-top:4px;font-size:11px">${d.trigger}</div>`
        }
        tooltip.html(html).style('opacity', 1)
      })
      .on('mousemove', (event) => {
        const rect = container.getBoundingClientRect()
        tooltip
          .style('left', `${event.clientX - rect.left + 14}px`)
          .style('top', `${event.clientY - rect.top - 36}px`)
      })
      .on('mouseleave', () => {
        tooltip.style('opacity', 0)
      })
  })
}

// --- Lifecycle ---

watch(() => props.actions.length, () => {
  nextTick(() => renderChart())
})

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
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Belief Evolution</h3>
        <p v-if="isDemo" class="text-[10px] text-[var(--color-text-muted)] mt-0.5">
          Demo data — beliefs will update as agents interact
        </p>
      </div>
    </div>

    <div
      v-if="beliefData.length"
      ref="chartRef"
      class="relative"
      :style="{ height: `${beliefData.length * 38 + 36}px` }"
    />

    <div v-else class="flex items-center justify-center h-[180px] text-[var(--color-text-muted)] text-sm">
      <span>Belief tracking will appear as agents interact</span>
    </div>

    <!-- Summary -->
    <div v-if="beliefData.length" class="flex items-center gap-4 mt-3 pt-3 border-t border-[var(--color-border)]">
      <span class="text-xs text-[var(--color-text-muted)]">
        <span class="font-medium text-[var(--color-text)]">{{ summary.totalChanges }}</span>
        belief {{ summary.totalChanges === 1 ? 'change' : 'changes' }} detected
      </span>
      <span v-if="summary.totalChanges > 0" class="text-xs text-[var(--color-text-muted)]">
        Most volatile:
        <span class="font-medium text-[#AA00FF]">{{ summary.mostVolatile }}</span>
      </span>
    </div>

    <!-- Legend -->
    <div v-if="beliefData.length" class="flex items-center gap-4 mt-2 text-xs text-[var(--color-text-muted)]">
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[rgba(0,153,0,0.55)]" /> Positive
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[rgba(32,104,255,0.55)]" /> Neutral
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-3 h-2 rounded-sm bg-[rgba(255,86,0,0.55)]" /> Negative
      </span>
      <span class="flex items-center gap-1.5">
        <span class="inline-block w-2 h-2 rounded-full bg-[#AA00FF]" /> Belief changed
      </span>
    </div>
  </div>
</template>
