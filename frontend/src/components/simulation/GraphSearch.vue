<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { graphApi } from '../../api/graph'

const props = defineProps({
  graphId: { type: String, default: '' },
  graphData: { type: Object, default: () => ({ nodes: [], edges: [] }) },
})

const emit = defineEmits(['select-node'])

const query = ref('')
const results = ref(null)
const loading = ref(false)
const error = ref('')
const expanded = ref(false)

let debounceTimer = null

function debounceSearch() {
  clearTimeout(debounceTimer)
  error.value = ''

  if (!query.value.trim()) {
    results.value = null
    expanded.value = false
    return
  }

  debounceTimer = setTimeout(() => runSearch(), 300)
}

async function runSearch() {
  const q = query.value.trim()
  if (!q) return

  loading.value = true
  error.value = ''

  try {
    if (props.graphId) {
      const res = await graphApi.search(props.graphId, q)
      const data = res.data?.data || res.data
      if (data?.demo || !data?.total_count) {
        results.value = localSearch(q)
      } else {
        results.value = data
      }
    } else {
      results.value = localSearch(q)
    }
    expanded.value = true
  } catch (e) {
    results.value = localSearch(q)
    expanded.value = true
  } finally {
    loading.value = false
  }
}

function localSearch(q) {
  const lower = q.toLowerCase()
  const keywords = lower.split(/\s+/).filter(k => k.length > 1)

  function score(text) {
    if (!text) return 0
    const t = text.toLowerCase()
    if (t.includes(lower)) return 100
    return keywords.reduce((s, kw) => s + (t.includes(kw) ? 10 : 0), 0)
  }

  const matchedNodes = props.graphData.nodes
    .map(n => ({ ...n, _score: score(n.name) + score(n.summary) }))
    .filter(n => n._score > 0)
    .sort((a, b) => b._score - a._score)
    .slice(0, 10)

  const matchedEdges = props.graphData.edges
    .map(e => ({ ...e, _score: score(e.name) + score(e.fact) }))
    .filter(e => e._score > 0)
    .sort((a, b) => b._score - a._score)
    .slice(0, 10)

  const facts = matchedEdges.map(e => e.fact).filter(Boolean)

  return {
    facts,
    nodes: matchedNodes.map(({ _score, ...n }) => n),
    edges: matchedEdges.map(({ _score, ...e }) => e),
    query: q,
    total_count: matchedNodes.length + matchedEdges.length,
  }
}

function clearSearch() {
  query.value = ''
  results.value = null
  expanded.value = false
  error.value = ''
}

function handleNodeClick(node) {
  emit('select-node', node.uuid)
}

function handleKeydown(e) {
  if (e.key === 'Escape') clearSearch()
}

const GENERIC_LABELS = new Set(['Entity', 'Node'])

const TYPE_COLORS = {
  persona: '#ff5600', person: '#ff5600', agent: '#ff5600', user: '#ff5600',
  customer: '#ff5600', stakeholder: '#ff5600', role: '#ff5600',
  topic: '#2068FF', theme: '#2068FF', subject: '#2068FF', concept: '#2068FF',
  category: '#2068FF', product: '#2068FF', feature: '#2068FF', technology: '#2068FF',
  relationship: '#AA00FF', interaction: '#AA00FF', connection: '#AA00FF',
  event: '#AA00FF', action: '#AA00FF', process: '#AA00FF',
}

function getNodeColor(labels) {
  const meaningful = (labels || []).filter(l => !GENERIC_LABELS.has(l))
  if (!meaningful.length) return '#667'
  const label = meaningful[0].toLowerCase()
  for (const [key, color] of Object.entries(TYPE_COLORS)) {
    if (label.includes(key)) return color
  }
  const palette = ['#ff5600', '#2068FF', '#AA00FF']
  let hash = 0
  for (const ch of label) hash = ((hash << 5) - hash + ch.charCodeAt(0)) | 0
  return palette[Math.abs(hash) % palette.length]
}

function getEntityType(labels) {
  const meaningful = (labels || []).filter(l => !GENERIC_LABELS.has(l))
  return meaningful[0] || 'Entity'
}

const hasResults = computed(() => results.value && results.value.total_count > 0)
const noResults = computed(() => results.value && results.value.total_count === 0 && query.value.trim())

watch(query, debounceSearch)

onUnmounted(() => clearTimeout(debounceTimer))
</script>

<template>
  <div class="graph-search">
    <!-- Search input -->
    <div class="relative">
      <div class="flex items-center bg-white/90 dark:bg-[#1a1a2e]/90 backdrop-blur-md border border-black/10 dark:border-white/10 rounded-lg overflow-hidden shadow-sm transition-shadow focus-within:shadow-md focus-within:border-[var(--color-primary)]">
        <svg class="w-4 h-4 ml-3 text-[var(--color-text-muted)] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
        </svg>
        <input
          v-model="query"
          type="text"
          placeholder="Search graph..."
          class="flex-1 bg-transparent px-3 py-2 text-xs text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none"
          @keydown="handleKeydown"
        />
        <div v-if="loading" class="mr-3">
          <svg class="w-3.5 h-3.5 animate-spin text-[var(--color-primary)]" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" class="opacity-25" />
            <path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" class="opacity-75" />
          </svg>
        </div>
        <button
          v-else-if="query"
          @click="clearSearch"
          class="mr-2 text-[var(--color-text-muted)] hover:text-[var(--color-text)] text-sm leading-none px-1 transition-colors"
        >&times;</button>
      </div>
    </div>

    <!-- Results panel -->
    <Transition name="search-panel">
      <div
        v-if="expanded && (hasResults || noResults)"
        class="mt-1.5 bg-white/95 dark:bg-[#1a1a2e]/95 backdrop-blur-md border border-black/10 dark:border-white/10 rounded-lg shadow-lg max-h-80 overflow-y-auto"
      >
        <!-- No results -->
        <div v-if="noResults" class="px-4 py-6 text-center">
          <p class="text-xs text-[var(--color-text-muted)]">No results for "{{ query }}"</p>
        </div>

        <!-- Results -->
        <div v-if="hasResults" class="p-2">
          <!-- Matching nodes -->
          <div v-if="results.nodes?.length">
            <h4 class="px-2 pt-1 pb-1.5 text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">
              Nodes ({{ results.nodes.length }})
            </h4>
            <button
              v-for="node in results.nodes"
              :key="node.uuid"
              class="w-full text-left px-3 py-2 rounded-md hover:bg-[var(--color-primary-light)] transition-colors group"
              @click="handleNodeClick(node)"
            >
              <div class="flex items-center gap-2">
                <span
                  class="w-2 h-2 rounded-full flex-shrink-0"
                  :style="{ backgroundColor: getNodeColor(node.labels) }"
                />
                <span class="text-xs font-medium text-[var(--color-text)] group-hover:text-[var(--color-primary)]">
                  {{ node.name }}
                </span>
                <span
                  v-if="node.labels?.length"
                  class="ml-auto text-[10px] text-[var(--color-text-muted)]"
                >
                  {{ getEntityType(node.labels) }}
                </span>
              </div>
              <p v-if="node.summary" class="text-[11px] text-[var(--color-text-muted)] mt-0.5 line-clamp-1 pl-4">
                {{ node.summary }}
              </p>
            </button>
          </div>

          <!-- Matching facts/edges -->
          <div v-if="results.facts?.length">
            <h4 class="px-2 pt-2 pb-1.5 text-[10px] uppercase tracking-widest text-[var(--color-text-muted)]">
              Facts ({{ results.facts.length }})
            </h4>
            <div
              v-for="(fact, i) in results.facts.slice(0, 8)"
              :key="i"
              class="px-3 py-2 rounded-md"
            >
              <p class="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">{{ fact }}</p>
            </div>
          </div>

          <!-- Summary -->
          <div class="px-3 py-2 border-t border-black/5 dark:border-white/5">
            <p class="text-[10px] text-[var(--color-text-muted)]">
              {{ results.total_count }} result{{ results.total_count !== 1 ? 's' : '' }} found
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.search-panel-enter-active,
.search-panel-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.search-panel-enter-from,
.search-panel-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
