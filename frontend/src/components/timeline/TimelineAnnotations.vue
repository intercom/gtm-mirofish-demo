<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { useAnnotationsStore } from '../../stores/annotations'

const props = defineProps({
  taskId: { type: String, required: true },
  rounds: { type: Array, default: () => [] },
})

const emit = defineEmits(['export'])

const store = useAnnotationsStore()

const scrubberRef = ref(null)
const editingId = ref(null)
const editText = ref('')
const editInputRef = ref(null)
const showImport = ref(false)
const importText = ref('')
let resizeObserver = null
let resizeTimer = null

const annotations = computed(() => store.getAnnotations(props.taskId))

const roundExtent = computed(() => {
  if (!props.rounds.length) return [1, 10]
  const nums = props.rounds.map(r => (typeof r === 'object' ? r.round : r))
  return [Math.min(...nums), Math.max(...nums)]
})

// --- Scrubber rendering ---

function clearScrubber() {
  if (scrubberRef.value) {
    d3.select(scrubberRef.value).selectAll('*').remove()
  }
}

function renderScrubber() {
  clearScrubber()
  const container = scrubberRef.value
  if (!container) return

  const containerWidth = container.clientWidth
  if (containerWidth === 0) return

  const margin = { left: 36, right: 16 }
  const width = containerWidth - margin.left - margin.right
  const height = 32

  const svg = d3.select(container)
    .append('svg')
    .attr('width', containerWidth)
    .attr('height', height)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left}, 0)`)

  const [minRound, maxRound] = roundExtent.value
  const x = d3.scaleLinear()
    .domain([minRound, maxRound])
    .range([0, width])
    .clamp(true)

  // Scrubber track
  g.append('rect')
    .attr('x', 0)
    .attr('y', 13)
    .attr('width', width)
    .attr('height', 6)
    .attr('rx', 3)
    .attr('fill', 'var(--color-tint, rgba(0,0,0,0.06))')

  // Round tick marks
  const step = Math.max(1, Math.floor((maxRound - minRound) / 12))
  const ticks = []
  for (let r = minRound; r <= maxRound; r += step) ticks.push(r)
  if (ticks[ticks.length - 1] !== maxRound) ticks.push(maxRound)

  g.selectAll('.tick')
    .data(ticks)
    .join('line')
    .attr('x1', d => x(d))
    .attr('x2', d => x(d))
    .attr('y1', 11)
    .attr('y2', 21)
    .attr('stroke', 'var(--color-border, rgba(0,0,0,0.12))')
    .attr('stroke-width', 1)

  g.selectAll('.tick-label')
    .data(ticks)
    .join('text')
    .attr('x', d => x(d))
    .attr('y', 30)
    .attr('text-anchor', 'middle')
    .attr('font-size', '9px')
    .attr('fill', 'var(--color-text-muted, #888)')
    .text(d => `R${d}`)

  // Annotation flags
  const flags = g.selectAll('.annotation-flag')
    .data(annotations.value, d => d.id)
    .join('g')
    .attr('class', 'annotation-flag')
    .attr('transform', d => `translate(${x(d.round)}, 0)`)
    .style('cursor', 'pointer')

  // Flag pole
  flags.append('line')
    .attr('x1', 0)
    .attr('x2', 0)
    .attr('y1', 2)
    .attr('y2', 14)
    .attr('stroke', d => d.color || 'var(--color-primary)')
    .attr('stroke-width', 1.5)

  // Flag icon (small pennant)
  flags.append('path')
    .attr('d', 'M0,2 L8,5 L0,8 Z')
    .attr('fill', d => d.color || 'var(--color-primary)')

  // Invisible larger hit target
  flags.append('rect')
    .attr('x', -6)
    .attr('y', 0)
    .attr('width', 16)
    .attr('height', 20)
    .attr('fill', 'transparent')

  flags.on('click', (event, d) => {
    event.stopPropagation()
    startEdit(d)
  })

  // Click on track to add annotation
  g.append('rect')
    .attr('x', 0)
    .attr('y', 0)
    .attr('width', width)
    .attr('height', 24)
    .attr('fill', 'transparent')
    .style('cursor', 'crosshair')
    .on('click', (event) => {
      const [mx] = d3.pointer(event)
      const round = Math.round(x.invert(mx))
      const clamped = Math.max(minRound, Math.min(maxRound, round))
      const annotation = store.addAnnotation(props.taskId, { round: clamped, text: '' })
      nextTick(() => startEdit(annotation))
    })
}

// --- Editing ---

function startEdit(annotation) {
  editingId.value = annotation.id
  editText.value = annotation.text
  nextTick(() => {
    editInputRef.value?.focus()
  })
}

function saveEdit() {
  if (editingId.value) {
    store.updateAnnotation(props.taskId, editingId.value, { text: editText.value })
    editingId.value = null
    editText.value = ''
  }
}

function cancelEdit() {
  editingId.value = null
  editText.value = ''
}

function deleteAnnotation(id) {
  store.removeAnnotation(props.taskId, id)
  if (editingId.value === id) {
    editingId.value = null
    editText.value = ''
  }
}

// --- Import/Export ---

function handleExport() {
  const data = store.exportAnnotations(props.taskId)
  emit('export', data)
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `annotations-${props.taskId}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function handleImport() {
  try {
    const parsed = JSON.parse(importText.value)
    const items = Array.isArray(parsed) ? parsed : []
    store.importAnnotations(props.taskId, items)
    showImport.value = false
    importText.value = ''
  } catch {
    // Invalid JSON — ignore
  }
}

function handleFileImport(event) {
  const file = event.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const parsed = JSON.parse(e.target.result)
      const items = Array.isArray(parsed) ? parsed : []
      store.importAnnotations(props.taskId, items)
    } catch {
      // Invalid file
    }
  }
  reader.readAsText(file)
  event.target.value = ''
}

// --- Lifecycle ---

watch([annotations, () => props.rounds.length], () => {
  nextTick(() => renderScrubber())
})

onMounted(() => {
  renderScrubber()
  if (scrubberRef.value) {
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(renderScrubber, 200)
    })
    resizeObserver.observe(scrubberRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  clearTimeout(resizeTimer)
})
</script>

<template>
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Timeline Annotations</h3>
      <div class="flex items-center gap-2">
        <button
          v-if="annotations.length"
          class="px-2 py-1 text-[11px] rounded font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors"
          @click="handleExport"
        >
          Export
        </button>
        <label class="px-2 py-1 text-[11px] rounded font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors cursor-pointer">
          Import
          <input type="file" accept=".json" class="hidden" @change="handleFileImport" />
        </label>
      </div>
    </div>

    <!-- Scrubber bar -->
    <div ref="scrubberRef" class="relative" style="height: 32px" />

    <p class="text-[10px] text-[var(--color-text-muted)] mt-1 mb-2">
      Click the timeline bar to add an annotation
    </p>

    <!-- Annotation list -->
    <div v-if="annotations.length" class="flex flex-col gap-1.5 mt-2 max-h-[200px] overflow-y-auto">
      <div
        v-for="a in annotations"
        :key="a.id"
        class="flex items-start gap-2 px-2.5 py-1.5 rounded-md text-xs group"
        :class="editingId === a.id
          ? 'bg-[var(--color-primary-light)] border border-[var(--color-primary-border)]'
          : 'bg-[var(--color-tint)] hover:bg-[var(--color-hover)]'"
      >
        <!-- Flag icon -->
        <svg class="w-3.5 h-3.5 mt-0.5 shrink-0" viewBox="0 0 14 14">
          <line x1="2" y1="1" x2="2" y2="13" :stroke="a.color || 'var(--color-primary)'" stroke-width="1.5" />
          <path d="M2,1 L11,4 L2,7 Z" :fill="a.color || 'var(--color-primary)'" />
        </svg>

        <div class="flex-1 min-w-0">
          <span class="text-[10px] font-medium text-[var(--color-text-muted)]">Round {{ a.round }}</span>

          <!-- Editing mode -->
          <div v-if="editingId === a.id" class="mt-1 flex gap-1.5">
            <input
              ref="editInputRef"
              v-model="editText"
              class="flex-1 px-2 py-1 text-xs rounded bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text)] outline-none focus:border-[var(--color-primary)]"
              placeholder="Add annotation text..."
              @keydown.enter="saveEdit"
              @keydown.escape="cancelEdit"
            />
            <button
              class="px-2 py-1 text-[10px] rounded bg-[var(--color-primary)] text-white font-medium hover:opacity-90 transition-opacity"
              @click="saveEdit"
            >
              Save
            </button>
            <button
              class="px-2 py-1 text-[10px] rounded text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
              @click="cancelEdit"
            >
              Cancel
            </button>
          </div>

          <!-- Display mode -->
          <p
            v-else
            class="mt-0.5 text-[var(--color-text-secondary)] cursor-pointer truncate"
            :class="a.text ? '' : 'italic text-[var(--color-text-muted)]'"
            @click="startEdit(a)"
          >
            {{ a.text || 'Click to add note...' }}
          </p>
        </div>

        <!-- Delete button -->
        <button
          class="shrink-0 p-0.5 rounded text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 hover:text-[var(--color-error)] transition-all"
          @click="deleteAnnotation(a.id)"
          title="Delete annotation"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
            <line x1="3" y1="3" x2="11" y2="11" />
            <line x1="11" y1="3" x2="3" y2="11" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="flex items-center justify-center py-3 text-xs text-[var(--color-text-muted)]">
      No annotations yet — click the timeline to add one
    </div>
  </div>
</template>
