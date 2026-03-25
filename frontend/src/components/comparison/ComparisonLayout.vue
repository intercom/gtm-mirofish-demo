<script setup>
import { ref, computed, onUnmounted, watch } from 'vue'
import { useSimulationStore } from '../../stores/simulation'

const props = defineProps({
  simulationIdA: { type: String, default: null },
  simulationIdB: { type: String, default: null },
})

const emit = defineEmits(['update:simulationIdA', 'update:simulationIdB'])

const simStore = useSimulationStore()

const selectedA = ref(props.simulationIdA)
const selectedB = ref(props.simulationIdB)
const syncScroll = ref(true)
const showDiffOverlay = ref(false)
const splitPercent = ref(50)

const panelARef = ref(null)
const panelBRef = ref(null)
let isSyncing = false
let isDragging = false

const availableRuns = computed(() => simStore.sessionRuns)

const selectedRunA = computed(() =>
  availableRuns.value.find(r => r.id === selectedA.value) || null
)
const selectedRunB = computed(() =>
  availableRuns.value.find(r => r.id === selectedB.value) || null
)

const hasBothSelected = computed(() => !!selectedA.value && !!selectedB.value)

watch(() => props.simulationIdA, (v) => { selectedA.value = v })
watch(() => props.simulationIdB, (v) => { selectedB.value = v })

watch(selectedA, (v) => emit('update:simulationIdA', v))
watch(selectedB, (v) => emit('update:simulationIdB', v))

function swapSimulations() {
  const tmp = selectedA.value
  selectedA.value = selectedB.value
  selectedB.value = tmp
}

function runLabel(run) {
  if (!run) return 'Unknown'
  const date = new Date(run.timestamp).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
  return `${run.scenarioName} (${date})`
}

// --- Synchronized scrolling ---
function onScrollA() {
  if (!syncScroll.value || isSyncing || !panelBRef.value) return
  isSyncing = true
  panelBRef.value.scrollTop = panelARef.value.scrollTop
  requestAnimationFrame(() => { isSyncing = false })
}

function onScrollB() {
  if (!syncScroll.value || isSyncing || !panelARef.value) return
  isSyncing = true
  panelARef.value.scrollTop = panelBRef.value.scrollTop
  requestAnimationFrame(() => { isSyncing = false })
}

// --- Draggable divider ---
function onDividerPointerDown(e) {
  isDragging = true
  e.target.setPointerCapture(e.pointerId)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onDividerPointerMove(e) {
  if (!isDragging) return
  const container = e.target.closest('[data-comparison-root]')
  if (!container) return
  const rect = container.getBoundingClientRect()
  const x = e.clientX - rect.left
  const pct = Math.min(80, Math.max(20, (x / rect.width) * 100))
  splitPercent.value = pct
}

function onDividerPointerUp() {
  isDragging = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function resetSplit() {
  splitPercent.value = 50
}

onUnmounted(() => {
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
})
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header toolbar -->
    <div class="flex flex-wrap items-center gap-3 px-4 py-3 bg-[var(--color-surface)] border-b border-[var(--color-border)]">
      <!-- Simulation A selector -->
      <div class="flex items-center gap-2 min-w-0">
        <span class="shrink-0 w-6 h-6 rounded-full bg-[var(--color-primary)] text-white text-xs font-semibold flex items-center justify-center">A</span>
        <select
          v-model="selectedA"
          class="text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-[var(--color-text)] min-w-[180px] max-w-[260px] truncate focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--input-ring)]"
        >
          <option :value="null" disabled>Select simulation...</option>
          <option
            v-for="run in availableRuns"
            :key="run.id"
            :value="run.id"
            :disabled="run.id === selectedB"
          >
            {{ runLabel(run) }}
          </option>
        </select>
      </div>

      <!-- Swap button -->
      <button
        @click="swapSimulations"
        :disabled="!hasBothSelected"
        class="shrink-0 w-8 h-8 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-primary)] hover:border-[var(--color-primary)] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        title="Swap simulations"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 16l-4-4 4-4" />
          <path d="M17 8l4 4-4 4" />
          <path d="M3 12h18" />
        </svg>
      </button>

      <!-- Simulation B selector -->
      <div class="flex items-center gap-2 min-w-0">
        <span class="shrink-0 w-6 h-6 rounded-full bg-[var(--color-fin-orange)] text-white text-xs font-semibold flex items-center justify-center">B</span>
        <select
          v-model="selectedB"
          class="text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-1.5 text-[var(--color-text)] min-w-[180px] max-w-[260px] truncate focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--input-ring)]"
        >
          <option :value="null" disabled>Select simulation...</option>
          <option
            v-for="run in availableRuns"
            :key="run.id"
            :value="run.id"
            :disabled="run.id === selectedA"
          >
            {{ runLabel(run) }}
          </option>
        </select>
      </div>

      <div class="flex-1" />

      <!-- Sync scroll toggle -->
      <label class="flex items-center gap-2 cursor-pointer select-none">
        <div
          class="relative w-9 h-5 rounded-full transition-colors"
          :class="syncScroll ? 'bg-[var(--color-primary)]' : 'bg-[var(--color-border-strong)]'"
          @click="syncScroll = !syncScroll"
        >
          <div
            class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform"
            :class="syncScroll ? 'translate-x-4' : 'translate-x-0'"
          />
        </div>
        <span class="text-xs text-[var(--color-text-muted)]">Sync</span>
      </label>

      <!-- Diff overlay toggle -->
      <label class="flex items-center gap-2 cursor-pointer select-none">
        <div
          class="relative w-9 h-5 rounded-full transition-colors"
          :class="showDiffOverlay ? 'bg-[var(--color-fin-orange)]' : 'bg-[var(--color-border-strong)]'"
          @click="showDiffOverlay = !showDiffOverlay"
        >
          <div
            class="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-transform"
            :class="showDiffOverlay ? 'translate-x-4' : 'translate-x-0'"
          />
        </div>
        <span class="text-xs text-[var(--color-text-muted)]">Diff</span>
      </label>
    </div>

    <!-- Split-screen panels -->
    <div
      v-if="hasBothSelected"
      class="flex-1 flex min-h-0 relative"
      data-comparison-root
    >
      <!-- Panel A -->
      <div
        ref="panelARef"
        class="overflow-y-auto"
        :style="{ width: `${splitPercent}%` }"
        @scroll="onScrollA"
      >
        <div class="p-4">
          <div class="flex items-center gap-2 mb-4">
            <span class="w-5 h-5 rounded-full bg-[var(--color-primary)] text-white text-[10px] font-semibold flex items-center justify-center">A</span>
            <span class="text-sm font-medium text-[var(--color-text)] truncate">{{ selectedRunA?.scenarioName }}</span>
          </div>
          <slot name="panelA" :simulation="selectedRunA" :diff="showDiffOverlay" />
        </div>
      </div>

      <!-- Draggable divider -->
      <div
        class="shrink-0 w-1 bg-[var(--color-border)] hover:bg-[var(--color-primary)] cursor-col-resize transition-colors relative group"
        @pointerdown="onDividerPointerDown"
        @pointermove="onDividerPointerMove"
        @pointerup="onDividerPointerUp"
        @dblclick="resetSplit"
      >
        <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-5 h-8 rounded bg-[var(--color-border)] group-hover:bg-[var(--color-primary)] flex items-center justify-center transition-colors">
          <svg width="6" height="14" viewBox="0 0 6 14" fill="none">
            <circle cx="1.5" cy="2" r="1" fill="currentColor" class="text-[var(--color-text-muted)] group-hover:text-white" />
            <circle cx="4.5" cy="2" r="1" fill="currentColor" class="text-[var(--color-text-muted)] group-hover:text-white" />
            <circle cx="1.5" cy="7" r="1" fill="currentColor" class="text-[var(--color-text-muted)] group-hover:text-white" />
            <circle cx="4.5" cy="7" r="1" fill="currentColor" class="text-[var(--color-text-muted)] group-hover:text-white" />
            <circle cx="1.5" cy="12" r="1" fill="currentColor" class="text-[var(--color-text-muted)] group-hover:text-white" />
            <circle cx="4.5" cy="12" r="1" fill="currentColor" class="text-[var(--color-text-muted)] group-hover:text-white" />
          </svg>
        </div>
      </div>

      <!-- Panel B -->
      <div
        ref="panelBRef"
        class="overflow-y-auto flex-1"
        @scroll="onScrollB"
      >
        <div class="p-4">
          <div class="flex items-center gap-2 mb-4">
            <span class="w-5 h-5 rounded-full bg-[var(--color-fin-orange)] text-white text-[10px] font-semibold flex items-center justify-center">B</span>
            <span class="text-sm font-medium text-[var(--color-text)] truncate">{{ selectedRunB?.scenarioName }}</span>
          </div>
          <slot name="panelB" :simulation="selectedRunB" :diff="showDiffOverlay" />
        </div>
      </div>
    </div>

    <!-- Empty state when not both selected -->
    <div v-else class="flex-1 flex flex-col items-center justify-center py-16 px-4 text-center">
      <div class="w-16 h-16 rounded-full bg-[rgba(32,104,255,0.08)] flex items-center justify-center mb-4">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="8" height="18" rx="1" />
          <rect x="14" y="3" width="8" height="18" rx="1" />
          <path d="M10 12h4" stroke-dasharray="2 2" />
        </svg>
      </div>
      <h3 class="text-base font-semibold text-[var(--color-text)] mb-1">Compare Simulations</h3>
      <p class="text-sm text-[var(--color-text-muted)] max-w-sm">
        Select two completed simulations above to view them side by side. You can drag the divider to resize panels, and toggle sync scrolling.
      </p>
      <p v-if="availableRuns.length < 2" class="text-xs text-[var(--color-text-muted)] mt-4">
        Run at least two simulations to enable comparison.
      </p>
    </div>
  </div>
</template>
