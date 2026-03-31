<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Object, default: () => null },
})

const chartRef = ref(null)
const tooltip = ref({ show: false, x: 0, y: 0, region: null })
const activeRegion = ref(null)
let resizeObserver = null
let resizeTimer = null
const uid = `venn-${Math.random().toString(36).slice(2, 8)}`

const COLORS = {
  match: '#009900',
  partial: '#d4940a',
  unique: '#ff5600',
  stroke: '#050505',
  text: '#1a1a1a',
}

const DEFAULT_DATA = {
  sources: ['Salesforce', 'Billing', 'Snowflake'],
  total: 857,
  regions: {
    a_only: { count: 42, examples: ['Acme Corp', 'Globex Inc', 'Soylent Corp'] },
    b_only: { count: 28, examples: ['Initech LLC', 'Umbrella Corp', 'Dunder Mifflin'] },
    c_only: { count: 15, examples: ['Wayne Enterprises', 'Hooli Inc'] },
    ab: { count: 67, examples: ['Stark Industries', 'Oscorp', 'Pied Piper'] },
    ac: { count: 53, examples: ['LexCorp', 'Cyberdyne Systems'] },
    bc: { count: 38, examples: ['Weyland-Yutani', 'Tyrell Corp'] },
    abc: { count: 614, examples: ['Intercom', 'Stripe', 'Notion', 'Figma', 'Linear'] },
  },
}

const vennData = computed(() => props.data || DEFAULT_DATA)

function clearChart() {
  if (!chartRef.value) return
  d3.select(chartRef.value).selectAll('*').remove()
}

function pct(key) {
  const d = vennData.value
  return ((d.regions[key].count / d.total) * 100).toFixed(1)
}

function renderChart() {
  clearChart()
  const container = chartRef.value
  if (!container) return

  const data = vennData.value
  const cw = container.clientWidth
  if (cw < 10) return

  const legendH = 32
  const margin = { top: 48, bottom: 12 + legendH, left: 16, right: 16 }
  const availW = cw - margin.left - margin.right
  const size = Math.min(availW, 400)
  const totalH = size + margin.top + margin.bottom
  const cx = cw / 2
  const cy = margin.top + size / 2
  const r = size * 0.30
  const dist = r * 0.68

  // Circle centers: equilateral triangle, A at top
  const centers = {
    a: [cx, cy - dist],
    b: [cx - dist * 0.866, cy + dist * 0.5],
    c: [cx + dist * 0.866, cy + dist * 0.5],
  }

  const svg = d3
    .select(container)
    .append('svg')
    .attr('width', cw)
    .attr('height', totalH)
    .attr('viewBox', `0 0 ${cw} ${totalH}`)
    .style('overflow', 'visible')

  // Title
  svg
    .append('text')
    .attr('x', cx)
    .attr('y', 20)
    .attr('text-anchor', 'middle')
    .attr('font-size', '14px')
    .attr('font-weight', '600')
    .attr('fill', COLORS.text)
    .text('Source Data Overlap')

  svg
    .append('text')
    .attr('x', cx)
    .attr('y', 36)
    .attr('text-anchor', 'middle')
    .attr('font-size', '11px')
    .attr('fill', '#888')
    .text(`${data.total.toLocaleString()} total accounts across three sources`)

  // --- Defs: clip paths + masks ---
  const defs = svg.append('defs')

  for (const [key, center] of Object.entries(centers)) {
    defs
      .append('clipPath')
      .attr('id', `${uid}-clip-${key}`)
      .append('circle')
      .attr('cx', center[0])
      .attr('cy', center[1])
      .attr('r', r)
  }

  function addMask(id, excludeKeys) {
    const mask = defs
      .append('mask')
      .attr('id', `${uid}-${id}`)
      .attr('maskUnits', 'userSpaceOnUse')
      .attr('x', 0)
      .attr('y', 0)
      .attr('width', cw)
      .attr('height', totalH)
    mask.append('rect').attr('width', cw).attr('height', totalH).attr('fill', 'white')
    for (const k of excludeKeys) {
      mask
        .append('circle')
        .attr('cx', centers[k][0])
        .attr('cy', centers[k][1])
        .attr('r', r)
        .attr('fill', 'black')
    }
  }

  addMask('no-bc', ['b', 'c'])
  addMask('no-ac', ['a', 'c'])
  addMask('no-ab', ['a', 'b'])
  addMask('no-c', ['c'])
  addMask('no-b', ['b'])
  addMask('no-a', ['a'])

  // --- Region fills ---
  const regions = svg.append('g').style('opacity', 0)

  // Unique regions (inside one circle, outside the other two)
  regions
    .append('circle')
    .attr('cx', centers.a[0])
    .attr('cy', centers.a[1])
    .attr('r', r)
    .attr('fill', COLORS.unique)
    .attr('fill-opacity', 0.25)
    .attr('mask', `url(#${uid}-no-bc)`)

  regions
    .append('circle')
    .attr('cx', centers.b[0])
    .attr('cy', centers.b[1])
    .attr('r', r)
    .attr('fill', COLORS.unique)
    .attr('fill-opacity', 0.25)
    .attr('mask', `url(#${uid}-no-ac)`)

  regions
    .append('circle')
    .attr('cx', centers.c[0])
    .attr('cy', centers.c[1])
    .attr('r', r)
    .attr('fill', COLORS.unique)
    .attr('fill-opacity', 0.25)
    .attr('mask', `url(#${uid}-no-ab)`)

  // Pair regions (inside two circles, outside the third)
  regions
    .append('g')
    .attr('clip-path', `url(#${uid}-clip-a)`)
    .append('circle')
    .attr('cx', centers.b[0])
    .attr('cy', centers.b[1])
    .attr('r', r)
    .attr('fill', COLORS.partial)
    .attr('fill-opacity', 0.3)
    .attr('mask', `url(#${uid}-no-c)`)

  regions
    .append('g')
    .attr('clip-path', `url(#${uid}-clip-a)`)
    .append('circle')
    .attr('cx', centers.c[0])
    .attr('cy', centers.c[1])
    .attr('r', r)
    .attr('fill', COLORS.partial)
    .attr('fill-opacity', 0.3)
    .attr('mask', `url(#${uid}-no-b)`)

  regions
    .append('g')
    .attr('clip-path', `url(#${uid}-clip-b)`)
    .append('circle')
    .attr('cx', centers.c[0])
    .attr('cy', centers.c[1])
    .attr('r', r)
    .attr('fill', COLORS.partial)
    .attr('fill-opacity', 0.3)
    .attr('mask', `url(#${uid}-no-a)`)

  // Center region (inside all three)
  regions
    .append('g')
    .attr('clip-path', `url(#${uid}-clip-a)`)
    .append('g')
    .attr('clip-path', `url(#${uid}-clip-b)`)
    .append('circle')
    .attr('cx', centers.c[0])
    .attr('cy', centers.c[1])
    .attr('r', r)
    .attr('fill', COLORS.match)
    .attr('fill-opacity', 0.35)

  // Entrance animation
  regions.transition().duration(500).ease(d3.easeCubicOut).style('opacity', 1)

  // --- Circle outlines ---
  for (const center of Object.values(centers)) {
    svg
      .append('circle')
      .attr('cx', center[0])
      .attr('cy', center[1])
      .attr('r', r)
      .attr('fill', 'none')
      .attr('stroke', COLORS.stroke)
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.2)
  }

  // --- Source labels ---
  const sourceLabels = [
    { text: data.sources[0], x: centers.a[0], y: centers.a[1] - r - 10 },
    { text: data.sources[1], x: centers.b[0] - 8, y: centers.b[1] + r + 16 },
    { text: data.sources[2], x: centers.c[0] + 8, y: centers.c[1] + r + 16 },
  ]

  for (const l of sourceLabels) {
    svg
      .append('text')
      .attr('x', l.x)
      .attr('y', l.y)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', '600')
      .attr('fill', COLORS.text)
      .style('opacity', 0)
      .text(l.text)
      .transition()
      .duration(300)
      .delay(400)
      .style('opacity', 1)
  }

  // --- Region count/percentage labels ---
  const positions = computeLabelPositions(centers, r)

  const labelG = svg.append('g').style('opacity', 0)
  for (const [key, pos] of Object.entries(positions)) {
    const region = data.regions[key]
    if (!region || region.count === 0) continue

    labelG
      .append('text')
      .attr('x', pos[0])
      .attr('y', pos[1] - 5)
      .attr('text-anchor', 'middle')
      .attr('font-size', '13px')
      .attr('font-weight', '700')
      .attr('fill', COLORS.text)
      .text(region.count.toLocaleString())

    labelG
      .append('text')
      .attr('x', pos[0])
      .attr('y', pos[1] + 9)
      .attr('text-anchor', 'middle')
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .text(`${pct(key)}%`)
  }

  labelG.transition().duration(300).delay(350).style('opacity', 1)

  // --- Legend ---
  const legendY = totalH - legendH + 4
  const legendItems = [
    { label: 'All match', color: COLORS.match },
    { label: 'Partial match', color: COLORS.partial },
    { label: 'Unique', color: COLORS.unique },
  ]
  const legend = svg
    .append('g')
    .attr('transform', `translate(${cx - 100}, ${legendY})`)

  legendItems.forEach((item, i) => {
    const x = i * 84
    legend
      .append('circle')
      .attr('cx', x + 5)
      .attr('cy', 0)
      .attr('r', 5)
      .attr('fill', item.color)
      .attr('fill-opacity', 0.6)

    legend
      .append('text')
      .attr('x', x + 14)
      .attr('y', 4)
      .attr('font-size', '10px')
      .attr('fill', '#666')
      .text(item.label)
  })

  // --- Hover overlay ---
  svg
    .append('rect')
    .attr('width', cw)
    .attr('height', totalH)
    .attr('fill', 'transparent')
    .on('mousemove', function (event) {
      const [mx, my] = d3.pointer(event, this)
      const region = detectRegion([mx, my], centers, r)
      if (region && data.regions[region]) {
        d3.select(this).style('cursor', 'pointer')
        activeRegion.value = region
        tooltip.value = {
          show: true,
          x: event.clientX,
          y: event.clientY,
          region: {
            label: regionLabel(region, data.sources),
            count: data.regions[region].count,
            pct: pct(region),
            examples: data.regions[region].examples,
          },
        }
      } else {
        d3.select(this).style('cursor', 'default')
        activeRegion.value = null
        tooltip.value = { ...tooltip.value, show: false }
      }
    })
    .on('mouseleave', () => {
      activeRegion.value = null
      tooltip.value = { ...tooltip.value, show: false }
    })
}

function computeLabelPositions(centers, r) {
  const { a, b, c } = centers
  const mid = [(a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3]

  function shiftAway(from, away, factor) {
    const dx = from[0] - away[0]
    const dy = from[1] - away[1]
    const d = Math.sqrt(dx * dx + dy * dy)
    if (d === 0) return from
    return [from[0] + (dx / d) * r * factor, from[1] + (dy / d) * r * factor]
  }

  function pairPos(c1, c2, away, factor) {
    const m = [(c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2]
    return shiftAway(m, away, factor)
  }

  return {
    abc: mid,
    ab: pairPos(a, b, c, 0.3),
    ac: pairPos(a, c, b, 0.3),
    bc: pairPos(b, c, a, 0.3),
    a_only: shiftAway(a, mid, 0.5),
    b_only: shiftAway(b, mid, 0.5),
    c_only: shiftAway(c, mid, 0.5),
  }
}

function detectRegion(point, centers, r) {
  const inside = (pt, center) => {
    const dx = pt[0] - center[0]
    const dy = pt[1] - center[1]
    return dx * dx + dy * dy <= r * r
  }
  const inA = inside(point, centers.a)
  const inB = inside(point, centers.b)
  const inC = inside(point, centers.c)
  if (inA && inB && inC) return 'abc'
  if (inA && inB) return 'ab'
  if (inA && inC) return 'ac'
  if (inB && inC) return 'bc'
  if (inA) return 'a_only'
  if (inB) return 'b_only'
  if (inC) return 'c_only'
  return null
}

function regionLabel(key, sources) {
  const map = {
    a_only: `Only in ${sources[0]}`,
    b_only: `Only in ${sources[1]}`,
    c_only: `Only in ${sources[2]}`,
    ab: `${sources[0]} \u2229 ${sources[1]}`,
    ac: `${sources[0]} \u2229 ${sources[2]}`,
    bc: `${sources[1]} \u2229 ${sources[2]}`,
    abc: 'All three sources',
  }
  return map[key] || key
}

watch(() => props.data, () => nextTick(renderChart), { deep: true })

onMounted(() => {
  renderChart()
  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(renderChart, 200)
  })
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="relative">
    <div ref="chartRef" class="w-full" />

    <Teleport to="body">
      <div
        v-if="tooltip.show && tooltip.region"
        class="fixed z-50 pointer-events-none bg-white border border-black/10 rounded-lg shadow-lg px-3 py-2 text-sm max-w-56"
        :style="{ left: tooltip.x + 12 + 'px', top: tooltip.y - 8 + 'px' }"
      >
        <div class="font-semibold text-[#1a1a1a]">{{ tooltip.region.label }}</div>
        <div class="text-[#555] mt-0.5">
          {{ tooltip.region.count.toLocaleString() }} accounts ({{ tooltip.region.pct }}%)
        </div>
        <div v-if="tooltip.region.examples?.length" class="mt-1 pt-1 border-t border-black/5">
          <div class="text-[10px] text-[#888] uppercase tracking-wider">Example accounts</div>
          <div
            v-for="ex in tooltip.region.examples.slice(0, 3)"
            :key="ex"
            class="text-[#555] text-xs"
          >
            {{ ex }}
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
