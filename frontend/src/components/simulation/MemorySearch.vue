<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'
import { memoryApi } from '../../api/memory'
import LoadingSpinner from '../ui/LoadingSpinner.vue'
import EmptyState from '../ui/EmptyState.vue'

const props = defineProps({
  graphId: { type: String, required: true },
})

const emit = defineEmits(['navigate-round'])

// Search form state
const query = ref('')
const selectedAgent = ref('')
const selectedType = ref('')
const sortBy = ref('relevance')

// Data state
const memories = ref([])
const agents = ref([])
const topics = ref([])
const loading = ref(false)
const loadingTopics = ref(false)
const totalResults = ref(0)

// Word cloud refs
const wordCloudRef = ref(null)
let resizeObserver = null

const memoryTypes = [
  { value: '', label: 'All types' },
  { value: 'facts', label: 'Facts' },
  { value: 'beliefs', label: 'Beliefs' },
  { value: 'decisions', label: 'Decisions' },
]

const typeColors = {
  facts: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  beliefs: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  decisions: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
}

function getTypeStyle(type) {
  return typeColors[type] || typeColors.facts
}

// Debounce search on query input
let searchTimer = null
watch(query, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(doSearch, 400)
})

watch([selectedAgent, selectedType, sortBy], () => {
  doSearch()
  if (selectedAgent.value !== undefined) loadTopics()
})

async function doSearch() {
  loading.value = true
  try {
    const res = await memoryApi.search(props.graphId, {
      query: query.value,
      agent_name: selectedAgent.value || undefined,
      memory_type: selectedType.value || undefined,
      sort_by: sortBy.value,
      limit: 50,
    })
    const data = res.data?.data || res.data || {}
    memories.value = data.memories || []
    totalResults.value = data.total || 0
  } catch (e) {
    console.error('Memory search failed:', e)
    memories.value = []
    totalResults.value = 0
  } finally {
    loading.value = false
  }
}

async function loadAgents() {
  try {
    const res = await memoryApi.getAgents(props.graphId)
    agents.value = res.data?.data || res.data || []
  } catch (e) {
    console.error('Failed to load agents:', e)
    agents.value = []
  }
}

async function loadTopics() {
  loadingTopics.value = true
  try {
    const params = {}
    if (selectedAgent.value) params.agent_name = selectedAgent.value
    const res = await memoryApi.getTopics(props.graphId, params)
    topics.value = res.data?.data || res.data || []
    await nextTick()
    renderWordCloud()
  } catch (e) {
    console.error('Failed to load topics:', e)
    topics.value = []
  } finally {
    loadingTopics.value = false
  }
}

function highlightText(text) {
  if (!query.value || !query.value.trim()) return text
  const escaped = query.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${escaped})`, 'gi')
  return text.replace(regex, '<mark class="bg-yellow-200 rounded px-0.5">$1</mark>')
}

function importancePercent(val) {
  return Math.round((val || 0) * 100)
}

function importanceColor(val) {
  if (val >= 0.8) return 'bg-emerald-500'
  if (val >= 0.6) return 'bg-[var(--color-primary)]'
  if (val >= 0.4) return 'bg-amber-400'
  return 'bg-gray-300'
}

function navigateToRound(round) {
  if (round != null) emit('navigate-round', round)
}

// Word cloud rendering with D3
function renderWordCloud() {
  const container = wordCloudRef.value
  if (!container || !topics.value.length) return

  d3.select(container).selectAll('*').remove()

  const width = container.clientWidth || 300
  const height = 200

  const maxCount = d3.max(topics.value, d => d.count) || 1
  const minCount = d3.min(topics.value, d => d.count) || 1
  const fontScale = d3.scaleLinear()
    .domain([minCount, maxCount])
    .range([11, 28])
    .clamp(true)

  const colorScale = d3.scaleOrdinal()
    .range(['#2068FF', '#ff5600', '#050505', '#6366f1', '#059669', '#d97706', '#dc2626', '#8b5cf6'])

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)

  // Simple spiral placement for word cloud
  const words = topics.value.slice(0, 40)
  const placed = []

  // Calculate positions using a simple grid-flow layout
  let x = 12
  let y = 24
  const lineHeight = 32
  const padding = 8

  const textGroup = svg.append('g')

  words.forEach((word, i) => {
    const fontSize = fontScale(word.count)
    const estWidth = word.text.length * fontSize * 0.65

    if (x + estWidth > width - 12) {
      x = 12
      y += lineHeight
    }
    if (y > height - 10) return

    textGroup.append('text')
      .attr('x', x)
      .attr('y', y)
      .attr('font-size', `${fontSize}px`)
      .attr('font-weight', word.count > (maxCount * 0.6) ? '600' : '400')
      .attr('fill', colorScale(i))
      .attr('cursor', 'pointer')
      .attr('opacity', 0.85)
      .text(word.text)
      .on('click', () => {
        query.value = word.text
      })
      .on('mouseover', function () {
        d3.select(this).attr('opacity', 1).attr('font-weight', '700')
      })
      .on('mouseout', function () {
        d3.select(this)
          .attr('opacity', 0.85)
          .attr('font-weight', word.count > (maxCount * 0.6) ? '600' : '400')
      })
      .append('title')
      .text(`${word.text} (${word.count})`)

    x += estWidth + padding
    placed.push({ x, y, word })
  })
}

onMounted(() => {
  loadAgents()
  doSearch()
  loadTopics()

  if (wordCloudRef.value) {
    resizeObserver = new ResizeObserver(() => {
      renderWordCloud()
    })
    resizeObserver.observe(wordCloudRef.value)
  }
})

onUnmounted(() => {
  clearTimeout(searchTimer)
  if (resizeObserver) resizeObserver.disconnect()
})
</script>

<template>
  <div class="flex flex-col gap-4">
    <!-- Search Controls -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
      <div class="flex flex-col gap-3">
        <!-- Search input -->
        <div class="relative">
          <span class="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]">
            &#x1F50D;
          </span>
          <input
            v-model="query"
            type="text"
            placeholder="Search agent memories..."
            class="w-full pl-10 pr-4 py-2.5 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
          />
        </div>

        <!-- Filters row -->
        <div class="flex flex-wrap gap-3 items-center">
          <!-- Agent selector -->
          <select
            v-model="selectedAgent"
            class="flex-1 min-w-[140px] px-3 py-2 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
          >
            <option value="">All agents</option>
            <option v-for="agent in agents" :key="agent" :value="agent">{{ agent }}</option>
          </select>

          <!-- Memory type filter -->
          <select
            v-model="selectedType"
            class="flex-1 min-w-[120px] px-3 py-2 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)] transition-colors"
          >
            <option v-for="t in memoryTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>

          <!-- Sort toggle -->
          <div class="flex rounded-lg border border-[var(--color-border)] overflow-hidden">
            <button
              @click="sortBy = 'relevance'"
              :class="[
                'px-3 py-2 text-xs font-medium transition-colors',
                sortBy === 'relevance'
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)]'
              ]"
            >
              Relevance
            </button>
            <button
              @click="sortBy = 'chronological'"
              :class="[
                'px-3 py-2 text-xs font-medium transition-colors border-l border-[var(--color-border)]',
                sortBy === 'chronological'
                  ? 'bg-[var(--color-primary)] text-white'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)]'
              ]"
            >
              Chronological
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Content: two-column layout -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <!-- Results list (2/3 width) -->
      <div class="lg:col-span-2 flex flex-col gap-3">
        <!-- Results header -->
        <div class="flex items-center justify-between px-1">
          <span class="text-sm text-[var(--color-text-secondary)]">
            {{ totalResults }} {{ totalResults === 1 ? 'memory' : 'memories' }} found
          </span>
        </div>

        <!-- Loading state -->
        <LoadingSpinner v-if="loading" label="Searching memories..." />

        <!-- Empty state -->
        <EmptyState
          v-else-if="!memories.length"
          icon="&#x1F9E0;"
          title="No memories found"
          description="Try adjusting your search query or filters."
        />

        <!-- Memory cards -->
        <div v-else class="flex flex-col gap-2">
          <div
            v-for="mem in memories"
            :key="mem.id"
            class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 hover:border-[var(--color-primary)] transition-colors cursor-default group"
          >
            <div class="flex items-start gap-3">
              <!-- Content -->
              <div class="flex-1 min-w-0">
                <!-- Agent + type badge row -->
                <div class="flex items-center gap-2 mb-1.5">
                  <span class="text-xs font-semibold text-[var(--color-text)]">
                    {{ mem.agent_name }}
                  </span>
                  <span
                    :class="[
                      'text-[10px] px-1.5 py-0.5 rounded-full font-medium',
                      getTypeStyle(mem.memory_type).bg,
                      getTypeStyle(mem.memory_type).text,
                    ]"
                  >
                    {{ mem.memory_type }}
                  </span>
                  <span
                    v-if="mem.source_round != null"
                    class="text-[10px] px-1.5 py-0.5 rounded-full bg-[rgba(32,104,255,0.08)] text-[var(--color-primary)] font-medium cursor-pointer hover:bg-[rgba(32,104,255,0.16)] transition-colors"
                    @click="navigateToRound(mem.source_round)"
                    :title="`Go to round ${mem.source_round}`"
                  >
                    R{{ mem.source_round }}
                  </span>
                </div>

                <!-- Memory content with search highlighting -->
                <p
                  class="text-sm text-[var(--color-text)] leading-relaxed"
                  v-html="highlightText(mem.content)"
                ></p>

                <!-- Memory strength bar -->
                <div class="mt-2 flex items-center gap-2">
                  <span class="text-[10px] text-[var(--color-text-muted)] w-16 shrink-0">Strength</span>
                  <div class="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden max-w-[120px]">
                    <div
                      :class="['h-full rounded-full transition-all', importanceColor(mem.importance)]"
                      :style="{ width: importancePercent(mem.importance) + '%' }"
                    ></div>
                  </div>
                  <span class="text-[10px] text-[var(--color-text-muted)] w-8 text-right">
                    {{ importancePercent(mem.importance) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Memory Map (word cloud) sidebar (1/3 width) -->
      <div class="flex flex-col gap-3">
        <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4">
          <h3 class="text-sm font-semibold text-[var(--color-text)] mb-3">Memory Map</h3>
          <p class="text-xs text-[var(--color-text-muted)] mb-3">
            Frequent topics in {{ selectedAgent || 'all' }} agent memories. Click a topic to search.
          </p>
          <div
            ref="wordCloudRef"
            class="w-full min-h-[200px] rounded-lg bg-[var(--color-tint)]"
          >
            <LoadingSpinner v-if="loadingTopics" size="sm" label="Loading topics..." />
            <div
              v-else-if="!topics.length"
              class="flex items-center justify-center h-[200px] text-xs text-[var(--color-text-muted)]"
            >
              No topics available
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
