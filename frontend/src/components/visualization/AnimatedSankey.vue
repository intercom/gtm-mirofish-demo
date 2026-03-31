<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as d3 from 'd3'
import { sankey as d3Sankey, sankeyLinkHorizontal, sankeyJustify } from 'd3-sankey'

const props = defineProps({
  nodes: { type: Array, required: true },
  links: { type: Array, required: true },
  animated: { type: Boolean, default: true },
  nodeWidth: { type: Number, default: 20 },
  nodePadding: { type: Number, default: 16 },
  height: { type: Number, default: 400 },
})

const NODE_COLORS = [
  '#2068FF', '#ff5600', '#AA00FF', '#009900',
  '#050505', '#f59e0b', '#06b6d4', '#ec4899',
]

const containerRef = ref(null)
const svgRef = ref(null)
const canvasRef = ref(null)

let resizeObserver = null
let resizeTimer = null
let animFrame = null
let lastTime = 0
let particles = []
let linkPathData = []

const colorMap = computed(() => {
  const map = {}
  props.nodes.forEach((n, i) => {
    map[n.id] = n.color || NODE_COLORS[i % NODE_COLORS.length]
  })
  return map
})

// --- Layout computation (d3-sankey) ---

function computeLayout() {
  const el = containerRef.value
  if (!el || !props.nodes.length || !props.links.length) return null

  const width = el.clientWidth
  if (width <= 0) return null

  const pad = 16
  const layout = d3Sankey()
    .nodeId(d => d.id)
    .nodeWidth(props.nodeWidth)
    .nodePadding(props.nodePadding)
    .nodeAlign(sankeyJustify)
    .extent([[pad, pad], [width - pad, props.height - pad]])

  return {
    ...layout({
      nodes: props.nodes.map(n => ({ ...n })),
      links: props.links.map(l => ({ ...l })),
    }),
    width,
  }
}

// --- SVG rendering (nodes + links) ---

function render(animate = true) {
  const data = computeLayout()
  if (!data) return

  const { nodes, links, width } = data
  const h = props.height

  const svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', h)
    .attr('viewBox', `0 0 ${width} ${h}`)

  sizeCanvas(width, h)
  renderLinks(svg, links, animate)
  renderNodes(svg, nodes, links, width, animate)
  storeLinkData(links)
  particles = []
}

function sizeCanvas(width, height) {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  canvas.width = width * dpr
  canvas.height = height * dpr
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  canvas.getContext('2d').setTransform(dpr, 0, 0, dpr, 0, 0)
}

function renderLinks(svg, links, animate) {
  const gen = sankeyLinkHorizontal()

  svg.selectAll('.link-layer').data([null]).join('g').attr('class', 'link-layer')
    .selectAll('path')
    .data(links, d => `${d.source.id}→${d.target.id}`)
    .join(
      enter => enter.append('path')
        .attr('d', gen)
        .attr('fill', 'none')
        .attr('stroke', d => colorMap.value[d.source.id])
        .attr('stroke-opacity', 0.18)
        .attr('stroke-width', 0)
        .call(sel => animate
          ? sel.transition().duration(600).ease(d3.easeCubicOut)
              .attr('stroke-width', d => Math.max(1, d.width))
          : sel.attr('stroke-width', d => Math.max(1, d.width))
        ),
      update => update.call(sel => {
        const t = animate ? sel.transition().duration(600).ease(d3.easeCubicOut) : sel
        t.attr('d', gen)
          .attr('stroke', d => colorMap.value[d.source.id])
          .attr('stroke-width', d => Math.max(1, d.width))
      }),
      exit => exit.transition().duration(300).attr('stroke-opacity', 0).remove(),
    )
}

function renderNodes(svg, nodes, links, width, animate) {
  const maxDepth = d3.max(nodes, d => d.depth) || 0

  const join = svg.selectAll('.node-layer').data([null]).join('g').attr('class', 'node-layer')
    .selectAll('.node')
    .data(nodes, d => d.id)
    .join(
      enter => {
        const g = enter.append('g').attr('class', 'node')
        g.append('rect')
        g.append('text')
        return g
      },
      update => update,
      exit => exit.transition().duration(300).style('opacity', 0).remove(),
    )

  // Rects
  const rectBase = animate
    ? join.select('rect').transition().duration(600).ease(d3.easeCubicOut)
    : join.select('rect')

  rectBase
    .attr('x', d => d.x0)
    .attr('y', d => d.y0)
    .attr('width', d => d.x1 - d.x0)
    .attr('height', d => Math.max(1, d.y1 - d.y0))
    .attr('rx', 3)
    .attr('fill', d => colorMap.value[d.id])
    .attr('opacity', 0.9)

  // Labels
  join.select('text')
    .attr('x', d => d.depth >= maxDepth ? d.x0 - 8 : d.x1 + 8)
    .attr('y', d => (d.y0 + d.y1) / 2)
    .attr('dy', '0.35em')
    .attr('text-anchor', d => d.depth >= maxDepth ? 'end' : 'start')
    .attr('font-size', '12px')
    .attr('font-weight', '500')
    .attr('fill', '#1a1a1a')
    .text(d => d.name || d.id)
}

function storeLinkData(links) {
  linkPathData = links.map(link => ({
    sx: link.source.x1,
    tx: link.target.x0,
    y0: link.y0,
    y1: link.y1,
    w: link.width,
    color: colorMap.value[link.source.id],
    value: link.value,
    spawnAccum: 0,
    spawnRate: 0,
  }))
}

// --- Particle animation (canvas) ---

function cubicBezier(a, b, c, d, t) {
  const mt = 1 - t
  return mt * mt * mt * a + 3 * mt * mt * t * b + 3 * mt * t * t * c + t * t * t * d
}

function startAnimation() {
  if (!props.animated || animFrame || !linkPathData.length) return

  const maxVal = Math.max(...linkPathData.map(l => l.value), 1)
  for (const lp of linkPathData) {
    lp.spawnRate = (lp.value / maxVal) * 10
    lp.spawnAccum = Math.random() * 2
  }

  lastTime = performance.now()
  animFrame = requestAnimationFrame(tick)
}

function stopAnimation() {
  if (animFrame) {
    cancelAnimationFrame(animFrame)
    animFrame = null
  }
  particles = []
  clearCanvas()
}

function clearCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function tick() {
  const now = performance.now()
  const dt = Math.min((now - lastTime) / 1000, 0.05)
  lastTime = now

  // Spawn new particles proportional to link volume
  for (const lp of linkPathData) {
    lp.spawnAccum += lp.spawnRate * dt
    while (lp.spawnAccum >= 1) {
      lp.spawnAccum--
      particles.push({
        lp,
        t: 0,
        speed: 0.2 + Math.random() * 0.15,
        yOff: (Math.random() - 0.5) * lp.w * 0.5,
        r: 1.5 + Math.random() * 1.5,
        alpha: 0.5 + Math.random() * 0.3,
      })
    }
  }

  // Advance particles, remove completed ones (swap-and-pop)
  let w = 0
  for (let i = 0; i < particles.length; i++) {
    particles[i].t += particles[i].speed * dt
    if (particles[i].t < 1) particles[w++] = particles[i]
  }
  particles.length = w

  drawParticles()
  animFrame = requestAnimationFrame(tick)
}

function drawParticles() {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  for (const p of particles) {
    const { lp, t, yOff, r, alpha } = p
    const midX = (lp.sx + lp.tx) / 2
    const x = cubicBezier(lp.sx, midX, midX, lp.tx, t)
    const y = cubicBezier(lp.y0, lp.y0, lp.y1, lp.y1, t) + yOff
    const fade = Math.min(t * 5, (1 - t) * 5, 1)

    ctx.beginPath()
    ctx.arc(x, y, r, 0, Math.PI * 2)
    ctx.fillStyle = lp.color
    ctx.globalAlpha = alpha * fade
    ctx.fill()
  }

  ctx.globalAlpha = 1
}

// --- Lifecycle ---

watch(
  [() => props.nodes, () => props.links],
  () => nextTick(() => {
    stopAnimation()
    render(true)
    if (props.animated) startAnimation()
  }),
  { deep: true },
)

watch(() => props.animated, val => {
  if (val) startAnimation()
  else stopAnimation()
})

onMounted(() => {
  render(true)
  if (props.animated) startAnimation()

  resizeObserver = new ResizeObserver(() => {
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => {
      stopAnimation()
      render(false)
      if (props.animated) startAnimation()
    }, 200)
  })
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onUnmounted(() => {
  stopAnimation()
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative w-full overflow-hidden"
    :style="{ height: `${height}px` }"
  >
    <svg ref="svgRef" class="w-full h-full" />
    <canvas ref="canvasRef" class="absolute top-0 left-0 pointer-events-none" />
  </div>
</template>
