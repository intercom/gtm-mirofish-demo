<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)
let animId = null

const STAGES = [
  { label: 'Awareness', color: '#2068FF' },
  { label: 'Interest', color: '#AA00FF' },
  { label: 'Evaluation', color: '#ff5600' },
  { label: 'Adoption', color: '#009900' },
]

function hexToRgb(hex) {
  return [parseInt(hex.slice(1, 3), 16), parseInt(hex.slice(3, 5), 16), parseInt(hex.slice(5, 7), 16)]
}

function init() {
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1
  const { width, height } = canvas.parentElement.getBoundingClientRect()

  canvas.width = width * dpr
  canvas.height = height * dpr
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  ctx.scale(dpr, dpr)

  const pad = 24
  const fTop = pad
  const fBottom = height - pad
  const fHeight = fBottom - fTop
  const topW = width * 0.82
  const bottomW = width * 0.22
  const stageH = fHeight / STAGES.length

  function funnelW(y) {
    const t = Math.max(0, Math.min(1, (y - fTop) / fHeight))
    return topW + t * (bottomW - topW)
  }

  const particles = []
  const MAX_PARTICLES = 55

  function spawn() {
    if (particles.length >= MAX_PARTICLES) return
    const w = funnelW(fTop)
    particles.push({
      x: (width - w) / 2 + Math.random() * w,
      y: fTop,
      speed: 0.4 + Math.random() * 0.8,
      r: 1.8 + Math.random() * 1.5,
    })
  }

  function draw() {
    ctx.clearRect(0, 0, width, height)

    // Draw funnel stages
    for (let i = 0; i < STAGES.length; i++) {
      const y = fTop + i * stageH
      const w1 = funnelW(y)
      const w2 = funnelW(y + stageH)
      const [r, g, b] = hexToRgb(STAGES[i].color)

      ctx.beginPath()
      ctx.moveTo((width - w1) / 2, y)
      ctx.lineTo((width + w1) / 2, y)
      ctx.lineTo((width + w2) / 2, y + stageH)
      ctx.lineTo((width - w2) / 2, y + stageH)
      ctx.closePath()
      ctx.fillStyle = `rgba(${r},${g},${b},0.06)`
      ctx.fill()

      if (i > 0) {
        ctx.beginPath()
        ctx.moveTo((width - w1) / 2, y)
        ctx.lineTo((width + w1) / 2, y)
        ctx.strokeStyle = `rgba(${r},${g},${b},0.2)`
        ctx.lineWidth = 1
        ctx.stroke()
      }

      ctx.fillStyle = STAGES[i].color
      ctx.font = 'bold 11px system-ui'
      ctx.textAlign = 'center'
      ctx.globalAlpha = 0.8
      ctx.fillText(STAGES[i].label, width / 2, y + stageH / 2 + 4)
      ctx.globalAlpha = 1
    }

    // Draw funnel outline
    ctx.beginPath()
    ctx.moveTo((width - topW) / 2, fTop)
    ctx.lineTo((width + topW) / 2, fTop)
    ctx.lineTo((width + bottomW) / 2, fBottom)
    ctx.lineTo((width - bottomW) / 2, fBottom)
    ctx.closePath()
    ctx.strokeStyle = 'rgba(128,128,128,0.15)'
    ctx.lineWidth = 1
    ctx.stroke()

    // Update and draw particles
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i]
      p.y += p.speed
      p.x += (Math.random() - 0.5) * 0.5

      const w = funnelW(p.y)
      const left = (width - w) / 2 + p.r
      const right = (width + w) / 2 - p.r
      p.x = Math.max(left, Math.min(right, p.x))

      if (p.y > fBottom) {
        particles.splice(i, 1)
        continue
      }

      const stageIdx = Math.min(Math.floor((p.y - fTop) / stageH), STAGES.length - 1)

      // Drop-off probability increases per stage
      if (stageIdx > 0 && Math.random() < 0.003 * stageIdx) {
        particles.splice(i, 1)
        continue
      }

      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = STAGES[Math.max(0, stageIdx)].color
      ctx.globalAlpha = 0.65
      ctx.fill()
      ctx.globalAlpha = 1
    }

    if (Math.random() < 0.3) spawn()
    animId = requestAnimationFrame(draw)
  }

  for (let i = 0; i < 20; i++) spawn()
  animId = requestAnimationFrame(draw)
}

onMounted(() => canvasRef.value && init())
onUnmounted(() => { if (animId) cancelAnimationFrame(animId) })
</script>

<template>
  <canvas ref="canvasRef" class="w-full h-full" />
</template>
