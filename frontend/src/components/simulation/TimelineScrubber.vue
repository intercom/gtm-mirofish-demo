<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useTimelineScrubberInject } from '../../composables/useTimelineScrubber'
import EventMarkers from '../timeline/EventMarkers.vue'

const scrubber = useTimelineScrubberInject()

const trackRef = ref(null)
const isDragging = ref(false)
const speeds = [1, 2, 4]

function getPositionFromEvent(e) {
  const track = trackRef.value
  if (!track) return 0
  const rect = track.getBoundingClientRect()
  return Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
}

function onTrackMouseDown(e) {
  isDragging.value = true
  scrubber.seekToPosition(getPositionFromEvent(e))
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

function onMouseMove(e) {
  if (isDragging.value) {
    scrubber.seekToPosition(getPositionFromEvent(e))
  }
}

function onMouseUp() {
  isDragging.value = false
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
}

function handleKeydown(e) {
  if (!scrubber) return
  const tag = document.activeElement?.tagName?.toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return

  switch (e.key) {
    case ' ':
      e.preventDefault()
      scrubber.togglePlay()
      break
    case 'ArrowLeft':
      e.preventDefault()
      scrubber.stepBack()
      break
    case 'ArrowRight':
      e.preventDefault()
      scrubber.stepForward()
      break
    case '+':
    case '=': {
      const idx = speeds.indexOf(scrubber.playbackSpeed.value)
      if (idx < speeds.length - 1) scrubber.setSpeed(speeds[idx + 1])
      break
    }
    case '-': {
      const idx = speeds.indexOf(scrubber.playbackSpeed.value)
      if (idx > 0) scrubber.setSpeed(speeds[idx - 1])
      break
    }
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (isDragging.value) {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }
})
</script>

<template>
  <div
    v-if="scrubber && scrubber.totalRounds.value > 0"
    class="border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 select-none"
  >
    <div class="flex items-center gap-3 max-w-6xl mx-auto">
      <!-- Transport controls -->
      <div class="flex items-center gap-0.5">
        <button
          class="p-1.5 rounded hover:bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
          title="Previous round (←)"
          @click="scrubber.stepBack()"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
          </svg>
        </button>
        <button
          class="p-1.5 rounded-full hover:bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)] transition-colors"
          :title="scrubber.isPlaying.value ? 'Pause (Space)' : 'Play (Space)'"
          @click="scrubber.togglePlay()"
        >
          <svg v-if="scrubber.isPlaying.value" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
          </svg>
          <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5v14l11-7z" />
          </svg>
        </button>
        <button
          class="p-1.5 rounded hover:bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
          title="Next round (→)"
          @click="scrubber.stepForward()"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
          </svg>
        </button>
      </div>

      <!-- Timeline track -->
      <div class="flex-1 min-w-0">
        <EventMarkers
          :events="scrubber.events.value"
          :totalRounds="scrubber.totalRounds.value"
        />
        <div
          ref="trackRef"
          class="relative h-2 bg-[var(--color-tint)] rounded-full cursor-pointer group"
          @mousedown="onTrackMouseDown"
        >
          <!-- Live progress background (shows how far simulation has progressed) -->
          <div
            v-if="scrubber.isRunning.value"
            class="absolute inset-y-0 left-0 bg-[rgba(32,104,255,0.12)] rounded-full"
            :style="{ width: `${(scrubber.liveRound.value / scrubber.totalRounds.value) * 100}%` }"
          />
          <!-- Active fill -->
          <div
            class="absolute inset-y-0 left-0 bg-[var(--color-primary)] rounded-full transition-[width] duration-75"
            :style="{ width: `${scrubber.position.value * 100}%` }"
          />
          <!-- Round tick marks -->
          <template v-if="scrubber.totalRounds.value <= 30">
            <div
              v-for="r in scrubber.totalRounds.value - 1"
              :key="r"
              class="absolute top-1/2 -translate-y-1/2 w-px h-1.5 bg-white/40 rounded-full"
              :style="{ left: `${(r / scrubber.totalRounds.value) * 100}%` }"
            />
          </template>
          <!-- Playhead -->
          <div
            class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-[var(--color-primary)] border-2 border-white shadow-sm transition-[left] duration-75"
            :class="isDragging ? 'scale-125 cursor-grabbing' : 'cursor-grab group-hover:scale-110'"
            :style="{ left: `${scrubber.position.value * 100}%` }"
          />
        </div>
      </div>

      <!-- Speed selector -->
      <div class="flex items-center gap-0.5 bg-[var(--color-tint)] rounded-md p-0.5">
        <button
          v-for="speed in speeds"
          :key="speed"
          class="px-1.5 py-0.5 text-[10px] font-medium rounded transition-colors"
          :class="scrubber.playbackSpeed.value === speed
            ? 'bg-[var(--color-surface)] text-[var(--color-text)] shadow-sm'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]'"
          @click="scrubber.setSpeed(speed)"
        >
          {{ speed }}x
        </button>
      </div>

      <!-- Round display -->
      <span class="text-xs font-medium text-[var(--color-text-muted)] whitespace-nowrap tabular-nums">
        R{{ scrubber.currentRound.value }} / {{ scrubber.totalRounds.value }}
      </span>

      <!-- Live indicator (only during active simulation) -->
      <button
        v-if="scrubber.isRunning.value"
        class="flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider transition-colors"
        :class="scrubber.isLive.value
          ? 'bg-red-500/10 text-red-500'
          : 'bg-[var(--color-tint)] text-[var(--color-text-muted)] hover:text-red-500'"
        @click="scrubber.goToLive()"
      >
        <span
          class="w-1.5 h-1.5 rounded-full"
          :class="scrubber.isLive.value ? 'bg-red-500 animate-pulse' : 'bg-[var(--color-text-muted)]'"
        />
        Live
      </button>
    </div>
  </div>
</template>
