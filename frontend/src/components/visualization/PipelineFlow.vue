<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as d3 from 'd3'
import { useFlowAnimation } from '../../composables/useFlowAnimation'

const props = defineProps({
  data: { type: Object, default: null },
  autoplay: { type: Boolean, default: true },
  height: { type: Number, default: 320 },
})

const containerRef = ref(null)
const svgRef = ref(null)
const svgWidth = ref(800)

const flow = useFlowAnimation({ autoplay: props.autoplay })

// ── Pipeline Definition ─────────────────────────────────────────────────

const STAGES = [
  { id: 'lead', label: 'Lead' },
  { id: 'mql', label: 'MQL' },
  { id: 'sql', label: 'SQL' },
  { id: 'sao', label: 'SAO' },
  { id: 'proposal', label: 'Proposal' },
  { id: 'won', label: 'Won' },
]

const DEFAULT_RATES = [0.35, 0.45, 0.60, 0.70, 0.30]
const DEFAULT_COUNTS = { lead: 1000, mql: 350, sql: 158, sao: 95, proposal: 66, won: 20 }

function getCounts() { return props.data?.counts ?? DEFAULT_COUNTS }
function getRates() { return props.data?.conversionRates ?? DEFAULT_RATES }

// ── Layout ──────────────────────────────────────────────────────────────

const M = { top: 28, right: 28, bottom: 40, left: 28 }
const BOX = { w: 78, h: 48, r: 8 }
const PIPE_Y = 80

function sx(i) {
  const lo = M.left + BOX.w / 2
  const hi = svgWidth.value - M.right - BOX.w / 2
  return lo + (i / (STAGES.length - 1)) * (hi - lo)
}

// ── Animation State ─────────────────────────────────────────────────────

let dots = []
let falling = []
let pulses = []
let spawnAcc = 0
let uid = 0

const SPAWN_MS = 200
const BASE_SPEED = 0.0007

// ── Dot Logic ───────────────────────────────────────────────────────────

function spawnDot() {
  const rates = getRates()
  let failAt = -1
  for (let i = 0; i < rates.length; i++) {
    if (Math.random() > rates[i]) { failAt = i; break }
  }
  dots.push({ id: uid++, seg: 0, t: 0, failAt })
}

function onAnimFrame({ delta }) {
  if (!svgRef.value) return

  // Spawn new dots — cap accumulator to avoid burst after pause/tab-switch
  spawnAcc = Math.min(spawnAcc + delta, SPAWN_MS * 3)
  while (spawnAcc >= SPAWN_MS) { spawnAcc -= SPAWN_MS; spawnDot() }

  const rates = getRates()

  // Advance active dots
  for (let i = dots.length - 1; i >= 0; i--) {
    const d = dots[i]

    // Later stages are slower (longer sales cycles)
    let spd = BASE_SPEED / (1 + d.seg * 0.25)

    // Bottleneck slowdown near gate — lower conversion = more accumulation
    if (d.t > 0.7) {
      const rate = rates[d.seg] ?? 0.5
      spd *= 0.3 + 0.7 * rate
    }

    d.t += spd * delta

    if (d.t >= 1) {
      if (d.seg === d.failAt) {
        // Lost: dot falls off at this gate
        const gx = (sx(d.seg) + sx(d.seg + 1)) / 2
        falling.push({ id: d.id, x: gx, y: PIPE_Y, sy: PIPE_Y, vy: 0, op: 1, age: 0 })
        dots.splice(i, 1)
        continue
      }
      d.seg++
      d.t = 0
      if (d.seg >= STAGES.length - 1) {
        // Won: celebrate with green expanding ring
        pulses.push({ id: d.id, x: sx(STAGES.length - 1), y: PIPE_Y, r: 4, op: 1, age: 0 })
        dots.splice(i, 1)
        continue
      }
    }
  }

  // Falling dot physics — gravity + fade
  for (let i = falling.length - 1; i >= 0; i--) {
    const f = falling[i]
    f.age += delta
    f.vy += delta * 0.0002
    f.y += f.vy * delta
    f.op = Math.max(0, 1 - f.age / 1200)
    if (f.op <= 0 || f.y > props.height + 10) falling.splice(i, 1)
  }

  // Won pulse expansion + fade
  for (let i = pulses.length - 1; i >= 0; i--) {
    const p = pulses[i]
    p.age += delta
    p.r = 4 + p.age * 0.02
    p.op = Math.max(0, 1 - p.age / 700)
    if (p.op <= 0) pulses.splice(i, 1)
  }

  render()
}

// ── D3 Rendering (per frame) ────────────────────────────────────────────

function render() {
  const svg = d3.select(svgRef.value)

  // Active pipeline dots
  svg.select('.layer-dots').selectAll('circle').data(dots, d => d.id)
    .join(
      enter => enter.append('circle').attr('r', 3.5).attr('fill', '#2068FF'),
      update => update,
      exit => exit.remove(),
    )
    .attr('opacity', d => Math.min(0.85, d.t * 5))
    .attr('cx', d => {
      const x0 = sx(d.seg) + BOX.w / 2 + 4
      const x1 = sx(Math.min(d.seg + 1, STAGES.length - 1)) - BOX.w / 2 - 4
      return x0 + (x1 - x0) * d.t
    })
    .attr('cy', d => {
      const wobble = Math.sin(d.id * 2.3) * 3
      if (d.t > 0.65) {
        const spread = (d.t - 0.65) / 0.35
        return PIPE_Y + wobble * (1 + spread * 2.5)
      }
      return PIPE_Y + wobble
    })

  // Falling dot trails (red lines from gate to current position)
  svg.select('.falling-trails').selectAll('line').data(falling, d => d.id)
    .join('line')
    .attr('x1', d => d.x).attr('y1', d => d.sy)
    .attr('x2', d => d.x).attr('y2', d => d.y)
    .attr('stroke', '#ef4444')
    .attr('stroke-width', 1.5)
    .attr('opacity', d => d.op * 0.35)

  // Falling dot heads
  svg.select('.falling-heads').selectAll('circle').data(falling, d => d.id)
    .join(
      enter => enter.append('circle').attr('r', 3).attr('fill', '#ef4444'),
      update => update,
      exit => exit.remove(),
    )
    .attr('cx', d => d.x).attr('cy', d => d.y)
    .attr('opacity', d => d.op)

  // Won celebration pulses (expanding green rings)
  svg.select('.layer-pulses').selectAll('circle').data(pulses, d => d.id)
    .join(
      enter => enter.append('circle').attr('fill', 'none').attr('stroke', '#009900').attr('stroke-width', 2),
      update => update,
      exit => exit.remove(),
    )
    .attr('cx', d => d.x).attr('cy', d => d.y)
    .attr('r', d => d.r)
    .attr('opacity', d => d.op)
}

// ── Static SVG Setup ────────────────────────────────────────────────────

function setupSvg() {
  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()

  const w = svgWidth.value
  const h = props.height
  svg.attr('viewBox', `0 0 ${w} ${h}`)
    .attr('role', 'img')
    .attr('aria-label', 'Animated GTM pipeline flow showing lead progression through sales stages')
    .style('font-family', 'system-ui, sans-serif')

  const counts = getCounts()
  const rates = getRates()

  // Connection lines (dashed) between stages
  const gConn = svg.append('g').attr('class', 'connections')
  for (let i = 0; i < STAGES.length - 1; i++) {
    gConn.append('line')
      .attr('x1', sx(i) + BOX.w / 2).attr('y1', PIPE_Y)
      .attr('x2', sx(i + 1) - BOX.w / 2).attr('y2', PIPE_Y)
      .attr('stroke', 'var(--color-border-strong)')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '6,4')
  }

  // Gate markers (orange diamonds) + conversion rate labels
  const gGates = svg.append('g').attr('class', 'gates')
  for (let i = 0; i < rates.length; i++) {
    const mx = (sx(i) + sx(i + 1)) / 2
    gGates.append('path')
      .attr('d', `M${mx},${PIPE_Y - 5}L${mx + 4},${PIPE_Y}L${mx},${PIPE_Y + 5}L${mx - 4},${PIPE_Y}Z`)
      .attr('fill', '#ff5600')
      .attr('opacity', 0.9)
    gGates.append('text')
      .attr('x', mx).attr('y', PIPE_Y - 14)
      .attr('text-anchor', 'middle')
      .attr('font-size', 11).attr('font-weight', 600)
      .attr('fill', '#ff5600')
      .text(`${Math.round(rates[i] * 100)}%`)
  }

  // Stage boxes, labels, and counters
  const gStages = svg.append('g').attr('class', 'stages')
  STAGES.forEach((stage, i) => {
    const cx = sx(i)
    const bx = cx - BOX.w / 2
    const by = PIPE_Y - BOX.h / 2
    const isWon = stage.id === 'won'
    const stroke = isWon ? '#009900' : '#2068FF'
    const fill = isWon ? 'rgba(0,153,0,0.06)' : 'rgba(32,104,255,0.04)'

    gStages.append('rect')
      .attr('x', bx).attr('y', by)
      .attr('width', BOX.w).attr('height', BOX.h)
      .attr('rx', BOX.r)
      .attr('fill', fill)
      .attr('stroke', stroke)
      .attr('stroke-width', 1.5)

    gStages.append('text')
      .attr('x', cx).attr('y', PIPE_Y + 1)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', 12).attr('font-weight', 600)
      .attr('fill', 'var(--color-text)')
      .text(stage.label)

    const count = counts[stage.id] ?? 0
    gStages.append('text')
      .attr('x', cx).attr('y', PIPE_Y + BOX.h / 2 + 18)
      .attr('text-anchor', 'middle')
      .attr('font-size', 13).attr('font-weight', 700)
      .attr('fill', stroke)
      .text(count.toLocaleString())
  })

  // Lost total counter at bottom
  const lostTotal = (counts.lead ?? 1000) - (counts.won ?? 20)
  svg.append('text')
    .attr('class', 'lost-label')
    .attr('x', w / 2).attr('y', h - 8)
    .attr('text-anchor', 'middle')
    .attr('font-size', 11).attr('font-weight', 600)
    .attr('fill', '#ef4444')
    .text(`${lostTotal.toLocaleString()} lost`)

  // Animation layers — falling has sub-groups so trails render behind dot heads
  const fallingG = svg.append('g').attr('class', 'layer-falling')
  fallingG.append('g').attr('class', 'falling-trails')
  fallingG.append('g').attr('class', 'falling-heads')
  svg.append('g').attr('class', 'layer-dots')
  svg.append('g').attr('class', 'layer-pulses')
}

// ── Lifecycle ───────────────────────────────────────────────────────────

let resizeObs = null

onMounted(() => {
  if (containerRef.value) {
    svgWidth.value = containerRef.value.clientWidth || 800
    resizeObs = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width
      if (w > 0 && Math.abs(w - svgWidth.value) > 2) {
        svgWidth.value = w
        nextTick(setupSvg)
      }
    })
    resizeObs.observe(containerRef.value)
    flow.observe(containerRef.value)
  }
  nextTick(setupSvg)
  flow.onFrame(onAnimFrame)
})

onUnmounted(() => {
  if (resizeObs) resizeObs.disconnect()
  dots = []
  falling = []
  pulses = []
})

watch(() => props.data, () => nextTick(setupSvg), { deep: true })
</script>

<template>
  <div
    ref="containerRef"
    class="pipeline-flow bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg overflow-hidden"
  >
    <!-- Header with playback controls -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Pipeline Flow</h3>
      <div class="flex items-center gap-2">
        <button
          @click="flow.playing.value ? flow.pause() : flow.play()"
          class="w-7 h-7 flex items-center justify-center rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] transition-colors"
          :title="flow.playing.value ? 'Pause' : 'Play'"
        >
          <svg v-if="flow.playing.value" class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
            <rect x="3" y="2" width="4" height="12" rx="1" />
            <rect x="9" y="2" width="4" height="12" rx="1" />
          </svg>
          <svg v-else class="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
            <path d="M4 2v12l10-6z" />
          </svg>
        </button>
        <div class="flex items-center gap-0.5">
          <button
            v-for="s in [0.5, 1, 2, 4]"
            :key="s"
            @click="flow.setSpeed(s)"
            class="px-1.5 py-0.5 rounded text-[10px] transition-colors"
            :class="flow.speed.value === s
              ? 'bg-[var(--color-primary-tint)] text-[var(--color-primary)] font-semibold'
              : 'text-[var(--color-text-muted)] hover:bg-[var(--color-tint)]'"
          >{{ s }}x</button>
        </div>
      </div>
    </div>

    <!-- SVG canvas -->
    <svg ref="svgRef" class="w-full" :style="{ height: `${height}px` }" />
  </div>
</template>
