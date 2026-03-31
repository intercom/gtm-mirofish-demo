<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { API_BASE } from '../../api/client'

const props = defineProps({
  customers: { type: Array, default: null },
})

const COLORS = {
  Essential: '#8B95A5',
  Advanced: '#2068FF',
  Expert: '#AA00FF',
  text: '#050505',
  textMuted: '#888',
  top10Border: '#ff5600',
}

const chartRef = ref(null)
const tooltipRef = ref(null)
const groupBy = ref('industry')
const zoomedGroup = ref(null)
const loading = ref(false)
const customerData = ref([])

let resizeObserver = null
let resizeTimer = null

const top10Ids = computed(() => {
  const sorted = [...customerData.value].sort((a, b) => b.mrr - a.mrr)
  return new Set(sorted.slice(0, 10).map((c) => c.id))
})

const totalMrr = computed(() => customerData.value.reduce((sum, c) => sum + c.mrr, 0))

async function fetchCustomers() {
  if (props.customers) {
    customerData.value = props.customers
    return
  }
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/revenue/customers`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    customerData.value = json.data?.customers || []
  } catch {
    customerData.value = []
  } finally {
    loading.value = false
  }
}

function buildHierarchy(data, field) {
  const groups = d3.group(data, (d) => d[field])
  return {
    name: 'Revenue',
    children: Array.from(groups, ([key, values]) => ({
      name: key,
      children: values.map((c) => ({ ...c, name: c.name, value: c.mrr })),
    })),
  }
}

function formatMrr(value) {
  if (value >= 1000) return `$${(value / 1000).toFixed(value >= 10000 ? 0 : 1)}k`
  return `$${value}`
}

function clearChart() {
  if (chartRef.value) d3.select(chartRef.value).selectAll('*').remove()
}

function render() {
  clearChart()
  const container = chartRef.value
  if (!container || customerData.value.length === 0) return

  const containerWidth = container.clientWidth
  const margin = { top: 4, right: 4, bottom: 4, left: 4 }
  const width = containerWidth - margin.left - margin.right
  const height = 480 - margin.top - margin.bottom

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', 480)
    .attr('viewBox', `0 0 ${containerWidth} 480`)
    .style('font-family', 'system-ui, -apple-system, sans-serif')

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const hierarchyData = buildHierarchy(customerData.value, groupBy.value)
  const root = d3
    .hierarchy(hierarchyData)
    .sum((d) => d.value || 0)
    .sort((a, b) => b.value - a.value)

  d3.treemap().size([width, height]).padding(3).paddingTop(24).round(true)(root)

  const groups = root.children || []
  const targetGroup = zoomedGroup.value
    ? groups.find((gr) => gr.data.name === zoomedGroup.value)
    : null

  const displayNodes = targetGroup ? [targetGroup] : groups

  // Compute scale for zoomed view
  const xScale = targetGroup
    ? d3.scaleLinear().domain([targetGroup.x0, targetGroup.x1]).range([0, width])
    : d3.scaleLinear().domain([0, width]).range([0, width])
  const yScale = targetGroup
    ? d3.scaleLinear().domain([targetGroup.y0, targetGroup.y1]).range([24, height])
    : d3.scaleLinear().domain([0, height]).range([0, height])

  // Back button when zoomed
  if (zoomedGroup.value) {
    const backG = g
      .append('g')
      .attr('cursor', 'pointer')
      .on('click', () => {
        zoomedGroup.value = null
      })

    backG
      .append('rect')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', width)
      .attr('height', 22)
      .attr('fill', '#f5f5f5')
      .attr('rx', 4)

    backG
      .append('text')
      .attr('x', 8)
      .attr('y', 15)
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .attr('fill', COLORS.text)
      .text(`\u2190 All ${groupBy.value === 'industry' ? 'Industries' : 'Plan Tiers'} / ${zoomedGroup.value}`)
  }

  for (const groupNode of displayNodes) {
    const groupG = g.append('g')

    // Group background
    const gx0 = xScale(groupNode.x0)
    const gy0 = yScale(groupNode.y0)
    const gx1 = xScale(groupNode.x1)
    const gy1 = yScale(groupNode.y1)

    groupG
      .append('rect')
      .attr('x', gx0)
      .attr('y', gy0)
      .attr('width', Math.max(0, gx1 - gx0))
      .attr('height', Math.max(0, gy1 - gy0))
      .attr('fill', 'rgba(0,0,0,0.03)')
      .attr('rx', 6)

    // Group label (clickable to zoom)
    const labelG = groupG
      .append('g')
      .attr('cursor', zoomedGroup.value ? 'default' : 'pointer')
      .on('click', () => {
        if (!zoomedGroup.value) zoomedGroup.value = groupNode.data.name
      })

    labelG
      .append('text')
      .attr('x', gx0 + 6)
      .attr('y', gy0 + 15)
      .attr('font-size', '11px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.textMuted)
      .text(groupNode.data.name)

    // Recompute children positions for zoomed view
    const leaves = groupNode.leaves()

    if (targetGroup) {
      // Relayout children to fill the available space
      const zoomRoot = d3
        .hierarchy(groupNode.data)
        .sum((d) => d.value || 0)
        .sort((a, b) => b.value - a.value)

      d3.treemap().size([gx1 - gx0, gy1 - gy0 - 20]).padding(2).round(true)(zoomRoot)

      const zoomLeaves = zoomRoot.leaves()
      for (const leaf of zoomLeaves) {
        const cx = gx0 + leaf.x0
        const cy = gy0 + 20 + leaf.y0
        const cw = Math.max(0, leaf.x1 - leaf.x0)
        const ch = Math.max(0, leaf.y1 - leaf.y0)
        const d = leaf.data
        const isTop10 = top10Ids.value.has(d.id)
        const tierColor = COLORS[d.planTier] || COLORS.Essential

        renderLeaf(groupG, cx, cy, cw, ch, d, tierColor, isTop10)
      }
    } else {
      for (const leaf of leaves) {
        const cx = xScale(leaf.x0)
        const cy = yScale(leaf.y0)
        const cw = Math.max(0, xScale(leaf.x1) - cx)
        const ch = Math.max(0, yScale(leaf.y1) - cy)
        const d = leaf.data
        const isTop10 = top10Ids.value.has(d.id)
        const tierColor = COLORS[d.planTier] || COLORS.Essential

        renderLeaf(groupG, cx, cy, cw, ch, d, tierColor, isTop10)
      }
    }
  }
}

function renderLeaf(parent, x, y, w, h, data, color, isTop10) {
  const cellG = parent.append('g')

  // Main rectangle
  cellG
    .append('rect')
    .attr('x', x)
    .attr('y', y)
    .attr('width', w)
    .attr('height', h)
    .attr('fill', color)
    .attr('opacity', 0.8)
    .attr('rx', 3)
    .attr('stroke', isTop10 ? COLORS.top10Border : 'rgba(255,255,255,0.6)')
    .attr('stroke-width', isTop10 ? 2.5 : 1)
    .style('cursor', 'pointer')
    .on('mouseover', function (event) {
      d3.select(this).attr('opacity', 1)
      showTooltip(event, data, isTop10)
    })
    .on('mousemove', function (event) {
      moveTooltip(event)
    })
    .on('mouseout', function () {
      d3.select(this).attr('opacity', 0.8)
      hideTooltip()
    })

  // Label: company name (only if rectangle is large enough)
  if (w > 60 && h > 32) {
    const maxChars = Math.floor(w / 7)
    const label = data.name.length > maxChars ? data.name.slice(0, maxChars - 1) + '\u2026' : data.name

    cellG
      .append('text')
      .attr('x', x + 5)
      .attr('y', y + 15)
      .attr('font-size', w > 100 ? '11px' : '9px')
      .attr('font-weight', '600')
      .attr('fill', '#fff')
      .style('pointer-events', 'none')
      .text(label)
  }

  // Label: MRR value (only if tall enough)
  if (w > 50 && h > 44) {
    cellG
      .append('text')
      .attr('x', x + 5)
      .attr('y', y + 29)
      .attr('font-size', '10px')
      .attr('fill', 'rgba(255,255,255,0.85)')
      .style('pointer-events', 'none')
      .text(formatMrr(data.mrr))
  }

  // Top 10 badge
  if (isTop10 && w > 40 && h > 20) {
    cellG
      .append('circle')
      .attr('cx', x + w - 9)
      .attr('cy', y + 9)
      .attr('r', 5)
      .attr('fill', COLORS.top10Border)
      .style('pointer-events', 'none')
  }
}

function showTooltip(event, data, isTop10) {
  const tip = tooltipRef.value
  if (!tip) return
  const mrrPercent = totalMrr.value > 0 ? ((data.mrr / totalMrr.value) * 100).toFixed(1) : '0'
  tip.innerHTML = `
    <div style="font-weight:600;margin-bottom:4px">${data.name}${isTop10 ? ' <span style="color:#ff5600">&#9679; Top 10</span>' : ''}</div>
    <div>MRR: <strong>${formatMrr(data.mrr)}</strong> (${mrrPercent}% of total)</div>
    <div>ARR: <strong>${formatMrr(data.mrr * 12)}</strong></div>
    <div>Plan: ${data.planTier} &middot; ${data.industry}</div>
    <div>Segment: ${data.segment} &middot; ${data.seats} seats</div>
    <div>Health: ${data.healthScore} &middot; Churn risk: ${data.churnRisk}</div>
  `
  tip.style.opacity = '1'
  moveTooltip(event)
}

function moveTooltip(event) {
  const tip = tooltipRef.value
  if (!tip) return
  tip.style.left = event.pageX + 12 + 'px'
  tip.style.top = event.pageY - 10 + 'px'
}

function hideTooltip() {
  const tip = tooltipRef.value
  if (tip) tip.style.opacity = '0'
}

watch(groupBy, () => {
  zoomedGroup.value = null
})

watch([customerData, groupBy, zoomedGroup], () => {
  nextTick(() => render())
})

watch(
  () => props.customers,
  (val) => {
    if (val) customerData.value = val
  },
)

onMounted(async () => {
  await fetchCustomers()
  nextTick(() => render())

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => render(), 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-white border border-black/10 rounded-lg p-4 md:p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h3 class="text-sm font-semibold" style="color: var(--color-text, #050505)">
          Customer Revenue Distribution
        </h3>
        <p class="text-xs mt-0.5" style="color: var(--color-text-muted, #888)">
          Each rectangle sized by MRR &middot; colored by plan tier
        </p>
      </div>

      <!-- Group-by toggle -->
      <div class="flex gap-1 bg-black/5 rounded-md p-0.5">
        <button
          v-for="opt in [
            { value: 'industry', label: 'Industry' },
            { value: 'planTier', label: 'Plan Tier' },
          ]"
          :key="opt.value"
          class="px-3 py-1 text-xs rounded-md transition-colors"
          :class="
            groupBy === opt.value
              ? 'bg-white shadow-sm font-medium text-[#050505]'
              : 'text-[#888] hover:text-[#050505]'
          "
          @click="groupBy = opt.value"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- Legend -->
    <div class="flex items-center gap-4 mb-3 text-xs">
      <span
        v-for="tier in [
          { name: 'Essential', color: '#8B95A5' },
          { name: 'Advanced', color: '#2068FF' },
          { name: 'Expert', color: '#AA00FF' },
        ]"
        :key="tier.name"
        class="flex items-center gap-1.5"
      >
        <span class="w-2.5 h-2.5 rounded-sm inline-block" :style="{ background: tier.color }" />
        <span style="color: var(--color-text-muted, #888)">{{ tier.name }}</span>
      </span>
      <span class="flex items-center gap-1.5 ml-2">
        <span
          class="w-2.5 h-2.5 rounded-full inline-block"
          style="background: #ff5600"
        />
        <span style="color: var(--color-text-muted, #888)">Top 10</span>
      </span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center h-[480px]">
      <div class="text-sm" style="color: var(--color-text-muted, #888)">Loading revenue data...</div>
    </div>

    <!-- Chart -->
    <div v-show="!loading" ref="chartRef" class="w-full" />

    <!-- Tooltip (portal-level to avoid clipping) -->
    <div
      ref="tooltipRef"
      class="fixed z-50 pointer-events-none opacity-0 transition-opacity duration-150"
      style="
        background: #fff;
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 12px;
        line-height: 1.6;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        max-width: 280px;
        color: #050505;
      "
    />
  </div>
</template>
