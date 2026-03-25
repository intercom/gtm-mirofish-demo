<script setup>
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'

const props = defineProps({
  targetValue: { type: Number, required: true },
  duration: { type: Number, default: 800 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  decimals: { type: Number, default: 0 },
  abbreviate: { type: Boolean, default: true },
  label: { type: String, default: '' },
  trend: {
    type: String,
    default: 'neutral',
    validator: (v) => ['positive', 'negative', 'neutral'].includes(v),
  },
  sparklineData: { type: Array, default: () => [] },
})

const currentValue = ref(0)
const animProgress = ref(0)
const sparklineCanvas = ref(null)
let frameId = null

function cancel() {
  if (frameId) {
    cancelAnimationFrame(frameId)
    frameId = null
  }
}

function animate(from, to) {
  cancel()
  if (isNaN(to)) return

  const startTime = performance.now()
  const dur = props.duration

  function step(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / dur, 1)
    const eased = 1 - Math.pow(1 - progress, 3)

    currentValue.value = from + (to - from) * eased
    animProgress.value = progress

    if (progress < 1) {
      frameId = requestAnimationFrame(step)
    } else {
      frameId = null
    }
  }

  frameId = requestAnimationFrame(step)
}

function formatNumber(value) {
  const absTarget = Math.abs(props.targetValue)

  if (props.abbreviate && absTarget >= 1e9) {
    return (value / 1e9).toFixed(1) + 'B'
  }
  if (props.abbreviate && absTarget >= 1e6) {
    return (value / 1e6).toFixed(1) + 'M'
  }
  if (props.abbreviate && absTarget >= 1e4) {
    return (value / 1e3).toFixed(1) + 'K'
  }

  const fixed = value.toFixed(props.decimals)
  const [whole, frac] = fixed.split('.')
  const withCommas = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return frac !== undefined ? `${withCommas}.${frac}` : withCommas
}

const displayValue = computed(() => formatNumber(currentValue.value))

const valueColor = computed(() => {
  const p = animProgress.value
  // Interpolate from gray (153,153,153) to target color
  const isNeg = props.trend === 'negative'
  const tR = isNeg ? 239 : 32
  const tG = isNeg ? 68 : 104
  const tB = isNeg ? 68 : 255

  const r = Math.round(153 + (tR - 153) * p)
  const g = Math.round(153 + (tG - 153) * p)
  const b = Math.round(153 + (tB - 153) * p)

  return `rgb(${r}, ${g}, ${b})`
})

function drawSparkline() {
  const canvas = sparklineCanvas.value
  if (!canvas || !props.sparklineData.length) return

  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  if (!rect.width || !rect.height) return

  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)

  const w = rect.width
  const h = rect.height
  const data = props.sparklineData
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1

  const revealCount = Math.max(2, Math.ceil(data.length * animProgress.value))
  const visibleData = data.slice(0, revealCount)

  const points = visibleData.map((v, i) => ({
    x: (i / (data.length - 1)) * w,
    y: h - ((v - min) / range) * (h * 0.8) - h * 0.1,
  }))

  ctx.clearRect(0, 0, w, h)
  if (points.length < 2) return

  const isNeg = props.trend === 'negative'
  const rgb = isNeg ? '239, 68, 68' : '32, 104, 255'

  // Area fill
  const gradient = ctx.createLinearGradient(0, 0, 0, h)
  gradient.addColorStop(0, `rgba(${rgb}, 0.15)`)
  gradient.addColorStop(1, `rgba(${rgb}, 0)`)

  ctx.beginPath()
  ctx.moveTo(points[0].x, h)
  points.forEach((p) => ctx.lineTo(p.x, p.y))
  ctx.lineTo(points[points.length - 1].x, h)
  ctx.closePath()
  ctx.fillStyle = gradient
  ctx.fill()

  // Line stroke
  ctx.beginPath()
  points.forEach((p, i) => (i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)))
  ctx.strokeStyle = isNeg ? '#ef4444' : '#2068FF'
  ctx.lineWidth = 1.5
  ctx.stroke()
}

watch(
  () => props.targetValue,
  (newVal) => {
    animate(currentValue.value, newVal)
  },
  { immediate: true },
)

watch(animProgress, () => {
  if (props.sparklineData.length) {
    nextTick(drawSparkline)
  }
})

watch(
  () => props.sparklineData,
  () => {
    if (animProgress.value > 0) nextTick(drawSparkline)
  },
  { deep: true },
)

onUnmounted(cancel)
</script>

<template>
  <div class="animated-counter">
    <div
      class="text-3xl md:text-4xl font-semibold tabular-nums leading-tight"
      :style="{ color: valueColor }"
    >
      <span v-if="prefix" class="text-lg md:text-xl font-medium mr-0.5">{{ prefix }}</span>
      {{ displayValue }}
      <span v-if="suffix" class="text-lg md:text-xl font-medium ml-0.5">{{ suffix }}</span>
    </div>
    <div v-if="label" class="text-xs text-[var(--color-text-muted)] mt-1.5">
      {{ label }}
    </div>
    <canvas
      v-if="sparklineData.length"
      ref="sparklineCanvas"
      class="w-full mt-2"
      style="height: 32px"
    />
  </div>
</template>
