<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { forceSimulation, forceX, forceY, forceManyBody, forceCollide } from 'd3-force'

const canvasRef = ref(null)
let simulation = null
let animationId = null
let particles = []

const COLORS = ['#2068FF', '#ff5600', '#AA00FF']
const PARTICLE_COUNT = 30
const LINE_DISTANCE = 120
const LINE_OPACITY_MIN = 0.08
const LINE_OPACITY_MAX = 0.12
const PARTICLE_OPACITY = 0.35
const PARTICLE_RADIUS_MIN = 2
const PARTICLE_RADIUS_MAX = 5

function initParticles(width, height) {
  return Array.from({ length: PARTICLE_COUNT }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: 0,
    vy: 0,
    r: PARTICLE_RADIUS_MIN + Math.random() * (PARTICLE_RADIUS_MAX - PARTICLE_RADIUS_MIN),
    color: COLORS[Math.floor(Math.random() * COLORS.length)],
  }))
}

function draw(ctx, width, height) {
  ctx.clearRect(0, 0, width, height)

  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x
      const dy = particles[i].y - particles[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < LINE_DISTANCE) {
        const t = 1 - dist / LINE_DISTANCE
        const opacity = LINE_OPACITY_MIN + t * (LINE_OPACITY_MAX - LINE_OPACITY_MIN)
        ctx.beginPath()
        ctx.moveTo(particles[i].x, particles[i].y)
        ctx.lineTo(particles[j].x, particles[j].y)
        ctx.strokeStyle = `rgba(255,255,255,${opacity})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
  }

  for (const p of particles) {
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fillStyle = p.color
    ctx.globalAlpha = PARTICLE_OPACITY
    ctx.fill()
    ctx.globalAlpha = 1
  }
}

function startAnimation(canvas) {
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    canvas.style.width = `${rect.width}px`
    canvas.style.height = `${rect.height}px`
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    return { width: rect.width, height: rect.height }
  }

  let { width, height } = resize()
  particles = initParticles(width, height)

  simulation = forceSimulation(particles)
    .force('x', forceX(width / 2).strength(0.002))
    .force('y', forceY(height / 2).strength(0.002))
    .force('charge', forceManyBody().strength(-0.3))
    .force('collide', forceCollide().radius((d) => d.r + 1))
    .alphaDecay(0)
    .velocityDecay(0.05)
    .on('tick', () => {
      for (const p of particles) {
        p.vx += (Math.random() - 0.5) * 0.15
        p.vy += (Math.random() - 0.5) * 0.15

        if (p.x < 0) p.x = width
        else if (p.x > width) p.x = 0
        if (p.y < 0) p.y = height
        else if (p.y > height) p.y = 0
      }
    })

  function loop() {
    draw(ctx, width, height)
    animationId = requestAnimationFrame(loop)
  }
  animationId = requestAnimationFrame(loop)

  function onResize() {
    ;({ width, height } = resize())
    simulation.force('x', forceX(width / 2).strength(0.002))
    simulation.force('y', forceY(height / 2).strength(0.002))
  }

  window.addEventListener('resize', onResize)

  return () => {
    window.removeEventListener('resize', onResize)
  }
}

let cleanupResize = null

onMounted(() => {
  if (canvasRef.value) {
    cleanupResize = startAnimation(canvasRef.value)
  }
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
    animationId = null
  }
  if (simulation) {
    simulation.stop()
    simulation = null
  }
  if (cleanupResize) {
    cleanupResize()
  }
})
</script>

<template>
  <canvas ref="canvasRef" class="absolute inset-0 w-full h-full pointer-events-none" />
</template>
