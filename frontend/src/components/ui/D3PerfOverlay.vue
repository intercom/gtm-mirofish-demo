<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useD3PerfMonitor } from '@/composables/useD3PerfMonitor'

const { enabled, components, clear } = useD3PerfMonitor()

const collapsed = ref(false)
const refreshKey = ref(0)
let refreshInterval = null

const entries = computed(() => {
  void refreshKey.value
  return Object.entries(components).map(([name, data]) => ({
    name,
    ...data,
    status: getStatus(data),
  }))
})

function getStatus(data) {
  if (data.fps > 0) {
    if (data.fps >= 55) return 'good'
    if (data.fps >= 30) return 'warn'
    return 'bad'
  }
  if (data.lastRenderMs <= 16) return 'good'
  if (data.lastRenderMs <= 33) return 'warn'
  return 'bad'
}

const statusColor = {
  good: '#009900',
  warn: '#ff5600',
  bad: '#e00',
}

function toggle(e) {
  if (e.key === 'F7') enabled.value = !enabled.value
}

function sparklinePath(history) {
  if (!history.length) return ''
  const w = 60
  const h = 16
  const max = Math.max(33, ...history)
  const step = w / Math.max(history.length - 1, 1)
  return history
    .map((v, i) => `${i === 0 ? 'M' : 'L'}${i * step},${h - (v / max) * h}`)
    .join(' ')
}

onMounted(() => {
  window.addEventListener('keydown', toggle)
  refreshInterval = setInterval(() => refreshKey.value++, 500)
})

onUnmounted(() => {
  window.removeEventListener('keydown', toggle)
  clearInterval(refreshInterval)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="enabled"
      class="fixed bottom-4 right-4 z-[9999] font-mono text-[11px] leading-tight select-none"
      style="pointer-events: auto"
    >
      <div
        class="rounded-lg border shadow-lg overflow-hidden"
        style="
          background: rgba(5, 5, 5, 0.92);
          border-color: rgba(32, 104, 255, 0.3);
          backdrop-filter: blur(8px);
          min-width: min(300px, 100%);
        "
      >
        <!-- Header -->
        <div
          class="flex items-center justify-between px-3 py-2 cursor-pointer"
          style="border-bottom: 1px solid rgba(255,255,255,0.08)"
          @click="collapsed = !collapsed"
        >
          <div class="flex items-center gap-2">
            <span
              class="inline-block w-1.5 h-1.5 rounded-full"
              style="background: #009900; box-shadow: 0 0 4px #009900"
            />
            <span style="color: #e0e0e0; font-weight: 600">D3 Perf</span>
            <span style="color: #666">{{ entries.length }} components</span>
          </div>
          <div class="flex items-center gap-2">
            <button
              class="px-1.5 py-0.5 rounded"
              style="color: #888; background: rgba(255,255,255,0.06)"
              @click.stop="clear()"
            >
              Reset
            </button>
            <span style="color: #555">{{ collapsed ? '&#9654;' : '&#9660;' }}</span>
          </div>
        </div>

        <!-- Body -->
        <div v-if="!collapsed" class="px-3 py-2 space-y-2">
          <div v-if="!entries.length" style="color: #666" class="py-2 text-center">
            No D3 renders captured yet
          </div>

          <div v-for="entry in entries" :key="entry.name" class="space-y-1">
            <div class="flex items-center justify-between">
              <span style="color: #ccc">{{ entry.name }}</span>
              <span
                class="inline-block w-1.5 h-1.5 rounded-full"
                :style="{ background: statusColor[entry.status] }"
              />
            </div>

            <div class="flex items-center gap-3" style="color: #888">
              <!-- Render time -->
              <span>
                <span :style="{ color: statusColor[entry.status] }">
                  {{ entry.lastRenderMs }}ms
                </span>
                last
              </span>
              <span>{{ entry.avgRenderMs }}ms avg</span>
              <span>{{ entry.maxRenderMs }}ms max</span>
            </div>

            <div class="flex items-center gap-3" style="color: #888">
              <span v-if="entry.fps > 0">
                <span :style="{ color: statusColor[entry.status] }">{{ entry.fps }}</span> fps
              </span>
              <span v-if="entry.domNodes > 0">{{ entry.domNodes }} nodes</span>
              <span>{{ entry.renderCount }}x renders</span>
            </div>

            <!-- Sparkline -->
            <svg
              v-if="entry.history.length > 1"
              :width="60"
              :height="16"
              class="block"
              style="opacity: 0.7"
            >
              <!-- 16ms budget line -->
              <line
                x1="0"
                :y1="16 - (16 / Math.max(33, ...entry.history)) * 16"
                x2="60"
                :y2="16 - (16 / Math.max(33, ...entry.history)) * 16"
                stroke="rgba(0,153,0,0.3)"
                stroke-width="0.5"
                stroke-dasharray="2,2"
              />
              <path
                :d="sparklinePath(entry.history)"
                fill="none"
                :stroke="statusColor[entry.status]"
                stroke-width="1"
              />
            </svg>
          </div>

          <!-- Footer hint -->
          <div style="color: #444; border-top: 1px solid rgba(255,255,255,0.06)" class="pt-2">
            Press F7 to toggle
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
