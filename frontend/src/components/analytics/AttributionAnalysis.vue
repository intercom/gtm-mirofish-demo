<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useAttributionStore } from '../../stores/attribution'

const props = defineProps({
  simulationId: { type: String, default: null },
})

const store = useAttributionStore()
const sankeyRef = ref(null)
const revenueRef = ref(null)
const activeTab = ref('sankey')
let resizeObserver = null
let resizeTimer = null

const COLORS = {
  primary: '#2068FF',
  orange: '#ff5600',
  purple: '#AA00FF',
  green: '#009900',
  navy: '#050505',
  text: '#1a1a1a',
}

const MODEL_COLORS = {
  first_touch: '#2068FF',
  last_touch: '#ff5600',
  linear: '#009900',
  time_decay: '#AA00FF',
  position_based: '#f59e0b',
}

const tabs = [
  { id: 'sankey', label: 'Journey Flow' },
  { id: 'touchpoints', label: 'Touchpoint Sequences' },
  { id: 'models', label: 'Model Comparison' },
]

const modelOptions = computed(() => {
  if (!store.models) return []
  return Object.entries(store.models).map(([id, label]) => ({ id, label }))
})

const revenueByChannel = computed(() => {
  if (!store.data?.channel_revenue) return []
  const entries = Object.entries(store.data.channel_revenue)
  return entries
    .map(([channel, models]) => ({ channel, ...models }))
    .sort((a, b) => (b[store.selectedModel] || 0) - (a[store.selectedModel] || 0))
})

onMounted(() => {
  store.fetchAnalysis(props.simulationId)

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => renderActiveChart(), 200)
  })
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
  store.reset()
})

watch(() => store.hasData, (ready) => {
  if (ready) nextTick(() => renderActiveChart())
})

watch(activeTab, () => {
  nextTick(() => renderActiveChart())
})

watch(() => store.selectedModel, () => {
  if (activeTab.value === 'models') {
    nextTick(() => renderRevenueChart())
  }
})

function renderActiveChart() {
  if (!store.hasData) return
  if (activeTab.value === 'sankey') renderSankey()
  if (activeTab.value === 'models') renderRevenueChart()

  if (resizeObserver) {
    resizeObserver.disconnect()
    if (sankeyRef.value) resizeObserver.observe(sankeyRef.value)
    if (revenueRef.value) resizeObserver.observe(revenueRef.value)
  }
}

// --- Sankey Diagram ---

function renderSankey() {
  const container = sankeyRef.value
  if (!container || !store.data?.sankey) return

  d3.select(container).selectAll('*').remove()

  const { nodes, links } = store.data.sankey
  if (!nodes.length) return

  const containerWidth = container.clientWidth
  const margin = { top: 16, right: 160, bottom: 16, left: 16 }
  const width = containerWidth - margin.left - margin.right
  const height = Math.max(400, nodes.length * 28)
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Categorize nodes into columns
  const channelNames = new Set(store.data.channels || [])
  const stageNames = new Set(['Awareness', 'Consideration', 'Evaluation', 'Purchase'])
  const outcomeNames = new Set(['Closed Won', 'Closed Lost', 'Open Pipeline'])

  const nodeColumns = nodes.map(n => {
    if (channelNames.has(n.name)) return 0
    if (stageNames.has(n.name)) return 1
    if (outcomeNames.has(n.name)) return 2
    return 1
  })

  // Compute node positions using simple layout
  const colWidth = width / 3
  const colNodes = [[], [], []]
  nodes.forEach((n, i) => colNodes[nodeColumns[i]].push(i))

  const nodeHeight = 24
  const nodePositions = []

  for (let col = 0; col < 3; col++) {
    const colCount = colNodes[col].length
    const totalNodeHeight = colCount * nodeHeight
    const gap = colCount > 1
      ? Math.min(12, (height - totalNodeHeight) / (colCount - 1))
      : 0
    const startY = (height - totalNodeHeight - gap * (colCount - 1)) / 2

    colNodes[col].forEach((nodeIdx, i) => {
      nodePositions[nodeIdx] = {
        x: col * colWidth,
        y: startY + i * (nodeHeight + gap),
        width: colWidth * 0.25,
        height: nodeHeight,
      }
    })
  }

  // Compute link values for node sizing
  const nodeValues = new Array(nodes.length).fill(0)
  links.forEach(l => {
    nodeValues[l.source] += l.value
    nodeValues[l.target] += l.value
  })
  const maxNodeVal = Math.max(...nodeValues, 1)

  // Draw links
  const maxLinkVal = Math.max(...links.map(l => l.value), 1)

  g.selectAll('.sankey-link')
    .data(links)
    .join('path')
    .attr('class', 'sankey-link')
    .attr('d', d => {
      const src = nodePositions[d.source]
      const tgt = nodePositions[d.target]
      const sx = src.x + src.width
      const sy = src.y + src.height / 2
      const tx = tgt.x
      const ty = tgt.y + tgt.height / 2
      const mx = (sx + tx) / 2
      return `M${sx},${sy} C${mx},${sy} ${mx},${ty} ${tx},${ty}`
    })
    .attr('fill', 'none')
    .attr('stroke', COLORS.primary)
    .attr('stroke-opacity', 0.15)
    .attr('stroke-width', d => Math.max(2, (d.value / maxLinkVal) * 18))
    .style('opacity', 0)
    .transition()
    .duration(600)
    .delay((d, i) => i * 20)
    .style('opacity', 1)

  // Draw nodes
  const nodeColorScale = d3.scaleOrdinal()
    .domain([0, 1, 2])
    .range([COLORS.primary, COLORS.orange, COLORS.green])

  g.selectAll('.sankey-node')
    .data(nodes)
    .join('rect')
    .attr('x', (d, i) => nodePositions[i].x)
    .attr('y', (d, i) => nodePositions[i].y)
    .attr('width', (d, i) => nodePositions[i].width)
    .attr('height', nodeHeight)
    .attr('rx', 4)
    .attr('fill', (d, i) => nodeColorScale(nodeColumns[i]))
    .attr('opacity', 0.85)
    .style('opacity', 0)
    .transition()
    .duration(400)
    .delay((d, i) => nodeColumns[i] * 150)
    .style('opacity', 0.85)

  // Node labels
  g.selectAll('.sankey-label')
    .data(nodes)
    .join('text')
    .attr('x', (d, i) => nodePositions[i].x + nodePositions[i].width + 6)
    .attr('y', (d, i) => nodePositions[i].y + nodeHeight / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text(d => d.name)
    .style('opacity', 0)
    .transition()
    .duration(300)
    .delay((d, i) => 400 + nodeColumns[i] * 100)
    .style('opacity', 1)
}

// --- Revenue by Channel Bar Chart ---

function renderRevenueChart() {
  const container = revenueRef.value
  if (!container || !revenueByChannel.value.length) return

  d3.select(container).selectAll('*').remove()

  const data = revenueByChannel.value
  const model = store.selectedModel
  const containerWidth = container.clientWidth
  const margin = { top: 16, right: 60, bottom: 24, left: 130 }
  const width = containerWidth - margin.left - margin.right
  const barHeight = 32
  const barGap = 8
  const height = data.length * (barHeight + barGap) - barGap
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const maxVal = Math.max(...data.map(d => d[model] || 0), 1)
  const x = d3.scaleLinear().domain([0, maxVal * 1.1]).range([0, width])
  const y = d3.scaleBand()
    .domain(data.map(d => d.channel))
    .range([0, height])
    .padding(barGap / (barHeight + barGap))

  // Grid
  const ticks = x.ticks(5)
  g.selectAll('.grid')
    .data(ticks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 0)
    .attr('y2', height)
    .attr('stroke', 'rgba(0,0,0,0.06)')
    .attr('stroke-dasharray', '2,3')

  // Labels
  g.selectAll('.label')
    .data(data)
    .join('text')
    .attr('x', -8)
    .attr('y', d => y(d.channel) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', 'end')
    .attr('font-size', '11px')
    .attr('fill', '#555')
    .text(d => d.channel)

  // Bars
  g.selectAll('.bar')
    .data(data)
    .join('rect')
    .attr('x', 0)
    .attr('y', d => y(d.channel))
    .attr('width', 0)
    .attr('height', y.bandwidth())
    .attr('rx', 4)
    .attr('fill', MODEL_COLORS[model] || COLORS.primary)
    .attr('opacity', 0.85)
    .transition()
    .duration(500)
    .delay((d, i) => i * 60)
    .ease(d3.easeCubicOut)
    .attr('width', d => x(d[model] || 0))

  // Value labels
  g.selectAll('.value')
    .data(data)
    .join('text')
    .attr('x', d => x(d[model] || 0) + 8)
    .attr('y', d => y(d.channel) + y.bandwidth() / 2)
    .attr('dy', '0.35em')
    .attr('font-size', '11px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .style('opacity', 0)
    .text(d => `$${((d[model] || 0) / 1000).toFixed(0)}k`)
    .transition()
    .duration(300)
    .delay((d, i) => 500 + i * 60)
    .style('opacity', 1)
}

function formatCurrency(val) {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`
  return `$${val}`
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-lg font-semibold" style="color: var(--color-navy)">
          Attribution Analysis
        </h2>
        <p class="text-sm text-gray-500 mt-0.5">
          Multi-touch attribution modeling across marketing channels
        </p>
      </div>
      <div
        v-if="store.summary"
        class="flex gap-4 text-sm text-gray-500"
      >
        <span>{{ store.summary.total_journeys }} journeys</span>
        <span>{{ store.summary.won_deals }} won</span>
        <span>{{ formatCurrency(store.summary.total_revenue) }} revenue</span>
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="store.loading"
      class="flex items-center justify-center py-20"
    >
      <div class="animate-spin h-6 w-6 border-2 rounded-full" style="border-color: var(--color-primary); border-top-color: transparent;" />
      <span class="ml-3 text-sm text-gray-500">Loading attribution data...</span>
    </div>

    <!-- Error -->
    <div
      v-else-if="store.error"
      class="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700"
    >
      {{ store.error }}
    </div>

    <template v-else-if="store.hasData">
      <!-- Insight Card -->
      <div
        v-if="store.insight?.type === 'divergence'"
        class="border rounded-lg p-4"
        style="border-color: var(--color-primary); background: rgba(32,104,255,0.04)"
      >
        <div class="flex items-start gap-3">
          <span class="text-lg">&#9670;</span>
          <div>
            <p class="text-sm font-medium" style="color: var(--color-navy)">Key Insight</p>
            <p class="text-sm text-gray-600 mt-1">{{ store.insight.text }}</p>
          </div>
        </div>
      </div>

      <!-- Tab Navigation -->
      <div class="flex gap-1 bg-gray-100 rounded-lg p-1">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="flex-1 py-2 px-3 text-sm font-medium rounded-md transition-colors"
          :class="activeTab === tab.id
            ? 'bg-white text-gray-900 shadow-sm'
            : 'text-gray-500 hover:text-gray-700'"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Sankey Tab -->
      <div
        v-show="activeTab === 'sankey'"
        class="bg-white border border-black/10 rounded-lg p-4 md:p-6"
      >
        <p class="text-xs text-gray-400 mb-3">
          Channel &rarr; Pipeline Stage &rarr; Outcome
        </p>
        <div ref="sankeyRef" class="w-full" />
      </div>

      <!-- Touchpoint Sequences Tab -->
      <div
        v-show="activeTab === 'touchpoints'"
        class="bg-white border border-black/10 rounded-lg overflow-hidden"
      >
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-200 bg-gray-50">
                <th class="text-left py-3 px-4 font-medium text-gray-600">Account</th>
                <th class="text-right py-3 px-4 font-medium text-gray-600">Deal Value</th>
                <th class="text-left py-3 px-4 font-medium text-gray-600">Touchpoint Journey</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(seq, i) in store.data.touchpoint_sequences"
                :key="i"
                class="border-b border-gray-100 hover:bg-gray-50/50"
              >
                <td class="py-3 px-4 font-medium" style="color: var(--color-navy)">
                  {{ seq.account }}
                </td>
                <td class="py-3 px-4 text-right text-gray-600">
                  {{ formatCurrency(seq.deal_value) }}
                </td>
                <td class="py-3 px-4">
                  <div class="flex items-center gap-1 flex-wrap">
                    <template v-for="(tp, j) in seq.touchpoints" :key="j">
                      <span
                        class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
                        :style="{
                          background: j === 0 ? 'rgba(32,104,255,0.1)' :
                                     j === seq.touchpoints.length - 1 ? 'rgba(255,86,0,0.1)' :
                                     'rgba(0,0,0,0.05)',
                          color: j === 0 ? '#2068FF' :
                                 j === seq.touchpoints.length - 1 ? '#ff5600' :
                                 '#555',
                        }"
                      >
                        {{ tp.channel }}
                      </span>
                      <span
                        v-if="j < seq.touchpoints.length - 1"
                        class="text-gray-300 text-xs"
                      >&rarr;</span>
                    </template>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Model Comparison Tab -->
      <div v-show="activeTab === 'models'" class="space-y-4">
        <!-- Model Selector -->
        <div class="flex items-center gap-2 flex-wrap">
          <span class="text-sm text-gray-500">Attribution model:</span>
          <button
            v-for="opt in modelOptions"
            :key="opt.id"
            class="px-3 py-1.5 text-xs font-medium rounded-full border transition-colors"
            :class="store.selectedModel === opt.id
              ? 'border-transparent text-white'
              : 'border-gray-200 text-gray-600 hover:border-gray-300'"
            :style="store.selectedModel === opt.id
              ? { background: MODEL_COLORS[opt.id] }
              : {}"
            @click="store.setModel(opt.id)"
          >
            {{ opt.label }}
          </button>
        </div>

        <!-- Revenue Chart -->
        <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
          <p class="text-xs text-gray-400 mb-3">
            Revenue attributed to each channel under
            <strong>{{ store.models[store.selectedModel] }}</strong> model
          </p>
          <div ref="revenueRef" class="w-full" />
        </div>

        <!-- Model Comparison Table -->
        <div class="bg-white border border-black/10 rounded-lg overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 bg-gray-50">
                  <th class="text-left py-3 px-4 font-medium text-gray-600">Channel</th>
                  <th
                    v-for="opt in modelOptions"
                    :key="opt.id"
                    class="text-right py-3 px-3 font-medium text-gray-600"
                  >
                    {{ opt.label }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in revenueByChannel"
                  :key="row.channel"
                  class="border-b border-gray-100 hover:bg-gray-50/50"
                >
                  <td class="py-2.5 px-4 font-medium" style="color: var(--color-navy)">
                    {{ row.channel }}
                  </td>
                  <td
                    v-for="opt in modelOptions"
                    :key="opt.id"
                    class="py-2.5 px-3 text-right font-mono text-xs"
                    :class="opt.id === store.selectedModel ? 'font-semibold' : 'text-gray-500'"
                    :style="opt.id === store.selectedModel ? { color: MODEL_COLORS[opt.id] } : {}"
                  >
                    {{ formatCurrency(row[opt.id] || 0) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
