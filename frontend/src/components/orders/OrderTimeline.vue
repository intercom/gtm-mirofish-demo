<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  events: {
    type: Array,
    default: () => [],
  },
})

const mounted = ref(false)

onMounted(() => {
  requestAnimationFrame(() => {
    mounted.value = true
  })
})

const STATUS_CONFIG = {
  success: { color: 'var(--color-success)', bg: 'var(--color-success-light)', label: 'Completed' },
  failed: { color: 'var(--color-error)', bg: 'var(--color-error-light)', label: 'Failed' },
  running: { color: 'var(--color-primary)', bg: 'var(--color-primary-light)', label: 'Running' },
  pending: { color: 'var(--color-text-muted)', bg: 'var(--color-tint)', label: 'Pending' },
}

function getStatusConfig(status) {
  return STATUS_CONFIG[status] || STATUS_CONFIG.pending
}

function formatTimestamp(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatElapsed(ms) {
  if (ms == null || ms < 0) return ''
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainSec = seconds % 60
  if (minutes < 60) return remainSec > 0 ? `${minutes}m ${remainSec}s` : `${minutes}m`
  const hours = Math.floor(minutes / 60)
  const remainMin = minutes % 60
  return remainMin > 0 ? `${hours}h ${remainMin}m` : `${hours}h`
}

const enrichedEvents = computed(() => {
  return props.events.map((event, i) => {
    let elapsed = null
    if (i > 0 && event.timestamp && props.events[i - 1].timestamp) {
      const curr = new Date(event.timestamp).getTime()
      const prev = new Date(props.events[i - 1].timestamp).getTime()
      if (!isNaN(curr) && !isNaN(prev) && curr >= prev) {
        elapsed = curr - prev
      }
    }
    return { ...event, elapsed, index: i }
  })
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-5">
    <h3 class="text-sm font-semibold text-[var(--color-text)] mb-5">Order Timeline</h3>

    <div v-if="!enrichedEvents.length" class="flex items-center justify-center h-[120px] text-[var(--color-text-muted)] text-sm">
      <span>No order events to display</span>
    </div>

    <div v-else class="relative pl-8">
      <!-- Vertical line -->
      <div
        class="absolute left-[11px] top-1 bottom-1 w-[2px] origin-top transition-transform duration-700 ease-out"
        :class="mounted ? 'scale-y-100' : 'scale-y-0'"
        style="background: var(--color-border)"
      />

      <!-- Events -->
      <div
        v-for="event in enrichedEvents"
        :key="event.index"
        class="relative pb-6 last:pb-0 transition-all duration-500 ease-out"
        :class="mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'"
        :style="{ transitionDelay: `${event.index * 120 + 100}ms` }"
      >
        <!-- Elapsed time between steps -->
        <div
          v-if="event.elapsed != null"
          class="absolute -top-3 left-[-21px] w-[24px] flex justify-center"
        >
          <span class="text-[10px] text-[var(--color-text-muted)] bg-[var(--color-surface)] px-0.5 leading-tight">
            {{ formatElapsed(event.elapsed) }}
          </span>
        </div>

        <!-- Node circle -->
        <div
          class="absolute left-[-21px] w-[24px] h-[24px] rounded-full flex items-center justify-center border-2 transition-colors duration-300"
          :style="{
            borderColor: getStatusConfig(event.status).color,
            backgroundColor: getStatusConfig(event.status).bg,
          }"
        >
          <!-- Success: check -->
          <svg v-if="event.status === 'success'" class="w-3 h-3" viewBox="0 0 12 12" fill="none">
            <path d="M2.5 6L5 8.5L9.5 3.5" :stroke="getStatusConfig('success').color" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <!-- Failed: x -->
          <svg v-else-if="event.status === 'failed'" class="w-3 h-3" viewBox="0 0 12 12" fill="none">
            <path d="M3 3L9 9M9 3L3 9" :stroke="getStatusConfig('failed').color" stroke-width="1.8" stroke-linecap="round" />
          </svg>
          <!-- Running: spinner -->
          <svg v-else-if="event.status === 'running'" class="w-3 h-3 animate-spin" viewBox="0 0 12 12" fill="none">
            <circle cx="6" cy="6" r="4.5" :stroke="getStatusConfig('running').color" stroke-width="1.5" stroke-dasharray="14 14" stroke-linecap="round" />
          </svg>
          <!-- Pending: clock -->
          <svg v-else class="w-2.5 h-2.5" viewBox="0 0 12 12" fill="none">
            <circle cx="6" cy="6" r="4.5" :stroke="getStatusConfig('pending').color" stroke-width="1.2" />
            <path d="M6 3.5V6L8 7.5" :stroke="getStatusConfig('pending').color" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>

        <!-- Event content -->
        <div class="min-h-[24px] flex flex-col justify-center">
          <div class="flex items-center gap-2">
            <span
              class="text-sm font-medium"
              :style="{ color: event.status === 'failed' ? 'var(--color-error)' : 'var(--color-text)' }"
            >
              {{ event.name }}
            </span>
            <span
              v-if="event.status === 'running'"
              class="text-[10px] font-medium px-1.5 py-0.5 rounded-full"
              style="background: var(--color-primary-light); color: var(--color-primary)"
            >
              In Progress
            </span>
          </div>

          <span v-if="event.timestamp" class="text-xs text-[var(--color-text-muted)] mt-0.5">
            {{ formatTimestamp(event.timestamp) }}
          </span>

          <!-- Error message for failed steps -->
          <div
            v-if="event.status === 'failed' && event.error"
            class="mt-1.5 text-xs px-2.5 py-1.5 rounded"
            style="background: var(--color-error-light); color: var(--color-error)"
          >
            {{ event.error }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
