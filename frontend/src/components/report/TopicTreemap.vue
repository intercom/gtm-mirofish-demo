<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Object, default: null },
  title: { type: String, default: 'Topic Distribution' },
  subtitle: { type: String, default: 'Relative weight of discussion topics across simulation' },
})

const chartRef = ref(null)
let resizeObserver = null
let resizeTimer = null

const COLORS = [
  '#2068FF', '#ff5600', '#AA00FF', '#009900',
  '#1a5ae0', '#e04d00', '#8800cc', '#007700',
  '#3a7fff', '#ff7733', '#bb33ff', '#33aa33',
]

const DEMO_DATA = {
  name: 'Topics',
  children: [
    {
      name: 'Product',
      children: [
        { name: 'AI Agent Capabilities', value: 28 },
        { name: 'Pricing & Packaging', value: 19 },
        { name: 'Platform Integration', value: 14 },
        { name: 'Self-Serve Onboarding', value: 8 },
      ],
    },
    {
      name: 'Market',
      children: [
        { name: 'Competitive Displacement', value: 22 },
        { name: 'Enterprise Expansion', value: 16 },
        { name: 'SMB Acquisition', value: 11 },
      ],
    },
    {
      name: 'Customer',
      children: [
        { name: 'Support Automation ROI', value: 25 },
        { name: 'Churn Risk Signals', value: 13 },
        { name: 'NPS & Satisfaction', value: 9 },
      ],
    },
    {
      name: 'Operations',
      children: [
        { name: 'Sales Cycle Length', value: 17 },
        { name: 'Pipeline Velocity', value: 12 },
        { name: 'Rep Enablement', value: 6 },
      ],
    },
  ],
}

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function render() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const treeData = props.data || DEMO_DATA
  const containerWidth = container.clientWidth
  if (containerWidth < 10) return

  const margin = { top: 52, right: 4, bottom: 4, left: 4 }
  const width = containerWidth - margin.left - margin.right
  const height = 360
  const totalHeight = height + margin.top + margin.bottom

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', totalHeight)
    .attr('viewBox', `0 0 ${containerWidth} ${totalHeight}`)
    .style('overflow', 'visible')

  svg.append('text')
    .attr('x', margin.left + 8)
    .attr('y', 22)
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', '#050505')
    .text(props.title)

  svg.append('text')
    .attr('x', margin.left + 8)
    .attr('y', 40)
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(props.subtitle)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const root = d3.hierarchy(treeData)
    .sum(d => d.value || 0)
    .sort((a, b) => b.value - a.value)

  const treemap = d3.treemap()
    .size([width, height])
    .paddingOuter(3)
    .paddingInner(2)
    .paddingTop(22)
    .round(true)

  treemap(root)

  const categoryColor = d3.scaleOrdinal()
    .domain(root.children ? root.children.map(d => d.data.name) : [])
    .range(COLORS)

  // Category group headers
  const groups = g.selectAll('.group')
    .data(root.children || [])
    .join('g')

  groups.append('rect')
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('height', d => d.y1 - d.y0)
    .attr('rx', 4)
    .attr('fill', d => categoryColor(d.data.name))
    .attr('opacity', 0.08)
    .style('opacity', 0)
    .transition()
    .duration(400)
    .style('opacity', 1)

  groups.append('text')
    .attr('x', d => d.x0 + 6)
    .attr('y', d => d.y0 + 14)
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', d => categoryColor(d.data.name))
    .attr('opacity', 0.7)
    .text(d => {
      const availableWidth = d.x1 - d.x0 - 12
      return availableWidth > 30 ? d.data.name.toUpperCase() : ''
    })

  // Leaf nodes
  const totalValue = root.value
  const leaves = root.leaves()

  const cells = g.selectAll('.cell')
    .data(leaves)
    .join('g')
    .attr('transform', d => `translate(${d.x0},${d.y0})`)

  cells.append('rect')
    .attr('width', d => Math.max(0, d.x1 - d.x0))
    .attr('height', d => Math.max(0, d.y1 - d.y0))
    .attr('rx', 3)
    .attr('fill', d => categoryColor(d.parent.data.name))
    .attr('opacity', 0)
    .transition()
    .duration(500)
    .delay((d, i) => i * 30)
    .ease(d3.easeCubicOut)
    .attr('opacity', 0.75)

  // Topic name labels
  cells.append('text')
    .attr('x', 5)
    .attr('y', 15)
    .attr('font-size', '11px')
    .attr('font-weight', '500')
    .attr('fill', '#fff')
    .style('opacity', 0)
    .text(d => {
      const cellWidth = d.x1 - d.x0
      if (cellWidth < 40) return ''
      const maxChars = Math.floor((cellWidth - 10) / 6)
      const name = d.data.name
      return name.length > maxChars ? name.slice(0, maxChars - 1) + '\u2026' : name
    })
    .transition()
    .duration(300)
    .delay((d, i) => 300 + i * 30)
    .style('opacity', 1)

  // Percentage labels
  cells.append('text')
    .attr('x', 5)
    .attr('y', 29)
    .attr('font-size', '10px')
    .attr('font-weight', '600')
    .attr('fill', 'rgba(255,255,255,0.8)')
    .style('opacity', 0)
    .text(d => {
      const cellWidth = d.x1 - d.x0
      const cellHeight = d.y1 - d.y0
      if (cellWidth < 36 || cellHeight < 34) return ''
      const pct = ((d.value / totalValue) * 100).toFixed(1)
      return `${pct}%`
    })
    .transition()
    .duration(300)
    .delay((d, i) => 400 + i * 30)
    .style('opacity', 1)

  // Tooltip rects (invisible, on top for hover)
  cells.append('title')
    .text(d => {
      const pct = ((d.value / totalValue) * 100).toFixed(1)
      return `${d.data.name}\n${d.parent.data.name} \u2022 ${pct}% (weight: ${d.value})`
    })
}

watch(() => props.data, () => nextTick(render), { deep: true })

onMounted(() => {
  render()
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(render, 200)
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
    <div ref="chartRef" class="w-full" />
  </div>
</template>
