<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  totalRounds: { type: Number, default: 0 },
  currentRound: { type: Number, default: 0 },
  markers: { type: Array, default: () => [] },
  timeline: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:currentRound', 'seek', 'play', 'pause', 'speed-change'])

const trackRef = ref(null)
const isPlaying = ref(false)
const playbackSpeed = ref(1)
const isDragging = ref(false)
const hoverInfo = ref(null)

let playbackTimer = null

const speeds = [0.5, 1, 2, 4]

const normalizedPosition = computed(() => {
  if (!props.totalRounds) return 0
  return props.currentRound / props.totalRounds
})

const displayRound = computed(() => {
  if (isDragging.value && hoverInfo.value) return hoverInfo.value.round
  return props.currentRound
})

const simulatedTime = computed(() => {
  const hours = Math.floor(props.currentRound * 0.75)
  const minutes = Math.round((props.currentRound * 0.75 - hours) * 60)
  if (hours === 0) return `${minutes}m`
  return `${hours}h ${minutes}m`
})

// --- Sparkline data for track background ---
const sparklinePath = computed(() => {
  if (!props.timeline.length || !props.totalRounds) return ''
  const data = props.timeline
  const maxVal = Math.max(...data.map(d => (d.twitter_actions || 0) + (d.reddit_actions || 0)), 1)
  const points = data.map(d => {
    const x = (d.round_num / props.totalRounds) * 100
    const y = 100 - ((d.twitter_actions || 0) + (d.reddit_actions || 0)) / maxVal * 80
    return `${x},${y}`
  })
  return `M${points.join(' L')}`
})

const sparklineAreaPath = computed(() => {
  if (!sparklinePath.value) return ''
  const data = props.timeline
  const maxVal = Math.max(...data.map(d => (d.twitter_actions || 0) + (d.reddit_actions || 0)), 1)
  const points = data.map(d => {
    const x = (d.round_num / props.totalRounds) * 100
    const y = 100 - ((d.twitter_actions || 0) + (d.reddit_actions || 0)) / maxVal * 80
    return `${x},${y}`
  })
  const first = (data[0].round_num / props.totalRounds) * 100
  const last = (data[data.length - 1].round_num / props.totalRounds) * 100
  return `M${first},100 L${points.join(' L')} L${last},100 Z`
})

// --- Playback controls ---
function startPlayback() {
  if (props.currentRound >= props.totalRounds) {
    emit('update:currentRound', 0)
    emit('seek', 0)
  }
  isPlaying.value = true
  emit('play')
  scheduleNextTick()
}

function scheduleNextTick() {
  if (playbackTimer) clearTimeout(playbackTimer)
  const interval = 1000 / playbackSpeed.value
  playbackTimer = setTimeout(() => {
    if (!isPlaying.value) return
    const next = props.currentRound + 1
    if (next > props.totalRounds) {
      pausePlayback()
      return
    }
    emit('update:currentRound', next)
    emit('seek', next)
    scheduleNextTick()
  }, interval)
}

function pausePlayback() {
  isPlaying.value = false
  if (playbackTimer) {
    clearTimeout(playbackTimer)
    playbackTimer = null
  }
  emit('pause')
}

function togglePlay() {
  if (isPlaying.value) pausePlayback()
  else startPlayback()
}

function stepForward() {
  pausePlayback()
  const next = Math.min(props.currentRound + 1, props.totalRounds)
  emit('update:currentRound', next)
  emit('seek', next)
}

function stepBack() {
  pausePlayback()
  const prev = Math.max(props.currentRound - 1, 0)
  emit('update:currentRound', prev)
  emit('seek', prev)
}

function skipToStart() {
  pausePlayback()
  emit('update:currentRound', 0)
  emit('seek', 0)
}

function skipToEnd() {
  pausePlayback()
  emit('update:currentRound', props.totalRounds)
  emit('seek', props.totalRounds)
}

function setSpeed(speed) {
  playbackSpeed.value = speed
  emit('speed-change', speed)
  if (isPlaying.value) {
    if (playbackTimer) clearTimeout(playbackTimer)
    scheduleNextTick()
  }
}

// --- Track interaction (drag + click) ---
function roundFromPointer(e) {
  const track = trackRef.value
  if (!track) return 0
  const rect = track.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  return Math.round(ratio * props.totalRounds)
}

function onTrackPointerDown(e) {
  if (!props.totalRounds) return
  e.preventDefault()
  isDragging.value = true
  pausePlayback()
  const round = roundFromPointer(e)
  emit('update:currentRound', round)
  emit('seek', round)
  trackRef.value?.setPointerCapture(e.pointerId)
}

function onTrackPointerMove(e) {
  if (!props.totalRounds) return
  const round = roundFromPointer(e)

  if (isDragging.value) {
    emit('update:currentRound', round)
    emit('seek', round)
  }

  const track = trackRef.value
  if (!track) return
  const rect = track.getBoundingClientRect()
  hoverInfo.value = {
    round,
    x: e.clientX - rect.left,
  }
}

function onTrackPointerUp(e) {
  isDragging.value = false
  trackRef.value?.releasePointerCapture(e.pointerId)
}

function onTrackPointerLeave() {
  if (!isDragging.value) {
    hoverInfo.value = null
  }
}

// --- Marker click ---
function seekToMarker(marker) {
  pausePlayback()
  emit('update:currentRound', marker.round)
  emit('seek', marker.round)
}

function markerColor(type) {
  const colors = {
    decision: 'var(--color-error, #ef4444)',
    milestone: 'var(--color-success, #009900)',
    interaction: 'var(--color-primary, #2068FF)',
  }
  return colors[type] || 'var(--color-text-muted, #888)'
}

function markerPosition(round) {
  if (!props.totalRounds) return '0%'
  return `${(round / props.totalRounds) * 100}%`
}

// --- Tick labels ---
const tickLabels = computed(() => {
  if (!props.totalRounds) return []
  const count = Math.min(8, props.totalRounds)
  const step = Math.max(1, Math.floor(props.totalRounds / count))
  const labels = []
  for (let i = 0; i <= props.totalRounds; i += step) {
    labels.push({ round: i, position: (i / props.totalRounds) * 100 })
  }
  if (labels[labels.length - 1]?.round !== props.totalRounds) {
    labels.push({ round: props.totalRounds, position: 100 })
  }
  return labels
})

// --- Keyboard shortcuts ---
function onKeydown(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return
  if (!props.totalRounds) return

  switch (e.code) {
    case 'Space':
      e.preventDefault()
      togglePlay()
      break
    case 'ArrowRight':
      e.preventDefault()
      stepForward()
      break
    case 'ArrowLeft':
      e.preventDefault()
      stepBack()
      break
    case 'Home':
      e.preventDefault()
      skipToStart()
      break
    case 'End':
      e.preventDefault()
      skipToEnd()
      break
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (playbackTimer) clearTimeout(playbackTimer)
})
</script>

<template>
  <div
    class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-5 py-4"
    :class="{ 'opacity-50 pointer-events-none': !totalRounds }"
  >
    <!-- Top: Round display -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-baseline gap-2">
        <span class="text-sm font-semibold text-[var(--color-text)]">
          Round {{ displayRound }}
        </span>
        <span class="text-xs text-[var(--color-text-muted)]">
          / {{ totalRounds }}
        </span>
      </div>
      <span class="text-xs text-[var(--color-text-muted)]">
        {{ simulatedTime }} simulated
      </span>
    </div>

    <!-- Track area -->
    <div class="relative mb-1">
      <!-- Event markers above track -->
      <div v-if="markers.length" class="relative h-4 mb-1">
        <button
          v-for="(marker, idx) in markers"
          :key="idx"
          class="absolute top-0 -translate-x-1/2 group"
          :style="{ left: markerPosition(marker.round) }"
          :title="marker.label || `${marker.type} at R${marker.round}`"
          @click="seekToMarker(marker)"
        >
          <span
            class="block w-2.5 h-2.5 rounded-full border-2 border-[var(--color-surface)] shadow-sm transition-transform group-hover:scale-125"
            :style="{ backgroundColor: markerColor(marker.type) }"
          />
        </button>
      </div>

      <!-- Scrubber track -->
      <div
        ref="trackRef"
        class="relative h-8 rounded cursor-pointer select-none touch-none"
        @pointerdown="onTrackPointerDown"
        @pointermove="onTrackPointerMove"
        @pointerup="onTrackPointerUp"
        @pointerleave="onTrackPointerLeave"
      >
        <!-- Track background -->
        <div class="absolute inset-0 rounded bg-[var(--color-tint)] overflow-hidden">
          <!-- Sparkline background -->
          <svg
            v-if="sparklineAreaPath"
            class="absolute inset-0 w-full h-full"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
          >
            <path :d="sparklineAreaPath" fill="rgba(32, 104, 255, 0.06)" />
            <path :d="sparklinePath" fill="none" stroke="rgba(32, 104, 255, 0.15)" stroke-width="1" vector-effect="non-scaling-stroke" />
          </svg>

          <!-- Progress fill -->
          <div
            class="absolute inset-y-0 left-0 rounded-l transition-[width]"
            :class="isDragging ? '' : 'duration-150'"
            :style="{ width: `${normalizedPosition * 100}%`, background: 'rgba(32, 104, 255, 0.12)' }"
          />
        </div>

        <!-- Playhead -->
        <div
          class="absolute top-0 h-full flex items-center -translate-x-1/2 z-10 transition-[left]"
          :class="isDragging ? '' : 'duration-150'"
          :style="{ left: `${normalizedPosition * 100}%` }"
        >
          <div
            class="w-3.5 h-3.5 rounded-full bg-[var(--color-primary)] border-2 border-[var(--color-surface)] shadow-md transition-transform"
            :class="isDragging ? 'scale-125' : 'hover:scale-110'"
          />
        </div>

        <!-- Hover tooltip -->
        <Transition name="tooltip">
          <div
            v-if="hoverInfo && !isDragging"
            class="absolute -top-8 -translate-x-1/2 px-2 py-0.5 rounded bg-[var(--color-navy)] text-[var(--color-text-inverse)] text-[11px] font-medium whitespace-nowrap pointer-events-none z-20"
            :style="{ left: `${hoverInfo.x}px` }"
          >
            R{{ hoverInfo.round }}
          </div>
        </Transition>
      </div>

      <!-- Tick labels below track -->
      <div class="relative h-4 mt-0.5">
        <span
          v-for="tick in tickLabels"
          :key="tick.round"
          class="absolute top-0 -translate-x-1/2 text-[10px] text-[var(--color-text-muted)]"
          :style="{ left: `${tick.position}%` }"
        >
          R{{ tick.round }}
        </span>
      </div>
    </div>

    <!-- Controls -->
    <div class="flex items-center justify-between mt-2">
      <!-- Transport controls -->
      <div class="flex items-center gap-1">
        <!-- Skip to start -->
        <button
          class="w-7 h-7 flex items-center justify-center rounded text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
          title="Skip to start (Home)"
          @click="skipToStart"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="19 20 9 12 19 4 19 20" />
            <line x1="5" y1="19" x2="5" y2="5" />
          </svg>
        </button>

        <!-- Step back -->
        <button
          class="w-7 h-7 flex items-center justify-center rounded text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
          title="Step back (←)"
          @click="stepBack"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="19 20 9 12 19 4 19 20" />
          </svg>
        </button>

        <!-- Play/Pause -->
        <button
          class="w-9 h-9 flex items-center justify-center rounded-full bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] transition-colors shadow-sm"
          :title="isPlaying ? 'Pause (Space)' : 'Play (Space)'"
          @click="togglePlay"
        >
          <!-- Pause icon -->
          <svg v-if="isPlaying" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="4" width="4" height="16" rx="1" />
            <rect x="14" y="4" width="4" height="16" rx="1" />
          </svg>
          <!-- Play icon -->
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <polygon points="8 5 19 12 8 19" />
          </svg>
        </button>

        <!-- Step forward -->
        <button
          class="w-7 h-7 flex items-center justify-center rounded text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
          title="Step forward (→)"
          @click="stepForward"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 4 15 12 5 20 5 4" />
          </svg>
        </button>

        <!-- Skip to end -->
        <button
          class="w-7 h-7 flex items-center justify-center rounded text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
          title="Skip to end (End)"
          @click="skipToEnd"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polygon points="5 4 15 12 5 20 5 4" />
            <line x1="19" y1="5" x2="19" y2="19" />
          </svg>
        </button>
      </div>

      <!-- Speed selector -->
      <div class="flex items-center gap-1">
        <span class="text-[10px] text-[var(--color-text-muted)] mr-1">Speed</span>
        <button
          v-for="speed in speeds"
          :key="speed"
          class="px-2 py-0.5 text-[11px] font-medium rounded transition-colors"
          :class="playbackSpeed === speed
            ? 'bg-[var(--color-primary-tint)] text-[var(--color-primary)]'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)]'"
          @click="setSpeed(speed)"
        >
          {{ speed }}x
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.1s ease;
}
.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}
</style>
