<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const canvasRef = ref(null)
let animId = null

const WAVES = [
  { color: [32, 104, 255], opacity: 0.25, speed: 0.015, amplitude: 35, freq: 0.008, phase: 0 },
  { color: [255, 86, 0], opacity: 0.2, speed: 0.02, amplitude: 28, freq: 0.01, phase: 2 },
  { color: [170, 0, 255], opacity: 0.15, speed: 0.012, amplitude: 22, freq: 0.012, phase: 4 },
]

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

  let frame = 0

  function draw() {
    ctx.clearRect(0, 0, width, height)

    for (const wave of WAVES) {
      ctx.beginPath()
      for (let x = 0; x <= width; x++) {
        const y = height * 0.5 +
          Math.sin(x * wave.freq + frame * wave.speed + wave.phase) * wave.amplitude +
          Math.sin(x * wave.freq * 0.6 + frame * wave.speed * 0.7) * wave.amplitude * 0.4
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      }
      ctx.lineTo(width, height)
      ctx.lineTo(0, height)
      ctx.closePath()
      const [r, g, b] = wave.color
      ctx.fillStyle = `rgba(${r},${g},${b},${wave.opacity})`
      ctx.fill()
    }

    frame++
    animId = requestAnimationFrame(draw)
  }

  animId = requestAnimationFrame(draw)
}

onMounted(() => canvasRef.value && init())
onUnmounted(() => { if (animId) cancelAnimationFrame(animId) })
</script>

<template>
  <canvas ref="canvasRef" class="w-full h-full" />
</template>
