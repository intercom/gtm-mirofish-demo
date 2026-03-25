<script setup>
import { ref, computed, watch, onMounted, inject } from 'vue'
import { scenariosApi } from '../../api/scenarios'

const props = defineProps({
  scenarioId: { type: String, default: '' },
})

const polling = inject('polling', null)

const collapsed = ref(false)
const sections = ref({})
const scenarioName = ref('')
const loading = ref(false)
const error = ref(null)
const openSections = ref({ revenue: true, pipeline: true, accounts: true, campaigns: true })
const highlightedKeys = ref(new Set())

// Metric keywords mapped to their keys for highlight detection
const keywordMap = computed(() => {
  const map = {}
  for (const section of Object.values(sections.value)) {
    for (const m of section.metrics || []) {
      // Map lowercased label words to the metric key
      const words = m.label.toLowerCase().split(/\s+/)
      for (const w of words) {
        if (w.length > 2) map[w] = m.key
      }
      map[m.label.toLowerCase()] = m.key
      map[m.key] = m.key
    }
  }
  return map
})

// Watch agent actions to auto-highlight referenced metrics
watch(
  () => polling?.recentActions?.value,
  (actions) => {
    if (!actions?.length) return
    const recent = actions.slice(-10)
    const newHighlights = new Set()
    for (const action of recent) {
      const text = (action.content || action.text || '').toLowerCase()
      for (const [keyword, key] of Object.entries(keywordMap.value)) {
        if (text.includes(keyword)) newHighlights.add(key)
      }
    }
    if (newHighlights.size > 0) {
      highlightedKeys.value = new Set([...highlightedKeys.value, ...newHighlights])
      // Clear highlights after 8 seconds
      setTimeout(() => {
        for (const k of newHighlights) highlightedKeys.value.delete(k)
        highlightedKeys.value = new Set(highlightedKeys.value)
      }, 8000)
    }
  },
  { deep: true },
)

const sectionOrder = ['revenue', 'pipeline', 'accounts', 'campaigns']

const sectionIcons = {
  revenue: '\u{1F4B0}',
  pipeline: '\u{1F4CA}',
  accounts: '\u{1F465}',
  campaigns: '\u{1F4E8}',
}

function toggleSection(key) {
  openSections.value[key] = !openSections.value[key]
}

async function fetchContext() {
  if (!props.scenarioId) return
  loading.value = true
  error.value = null
  try {
    const res = await scenariosApi.getContext(props.scenarioId)
    sections.value = res.data.sections || {}
    scenarioName.value = res.data.scenario_name || ''
  } catch (e) {
    error.value = e.message || 'Failed to load context'
    // Provide fallback empty sections
    sections.value = {}
  } finally {
    loading.value = false
  }
}

watch(() => props.scenarioId, fetchContext, { immediate: true })

onMounted(fetchContext)
</script>

<template>
  <div
    :class="[
      'gtm-context-panel border-l border-[var(--color-border)] bg-[var(--color-surface)] flex flex-col transition-all duration-300 ease-in-out h-full',
      collapsed ? 'w-10' : 'w-72',
    ]"
  >
    <!-- Collapse toggle -->
    <button
      class="flex items-center gap-1.5 px-2.5 py-2.5 text-xs font-semibold text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-[var(--color-tint)] transition-colors border-b border-[var(--color-border)] shrink-0"
      @click="collapsed = !collapsed"
    >
      <svg
        :class="['w-3.5 h-3.5 transition-transform duration-200', collapsed ? 'rotate-180' : '']"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <path d="M10 4l-4 4 4 4" />
      </svg>
      <span v-if="!collapsed" class="truncate">GTM Context</span>
    </button>

    <!-- Panel body -->
    <div v-if="!collapsed" class="flex-1 overflow-y-auto">
      <!-- Loading -->
      <div v-if="loading" class="p-4 flex items-center justify-center">
        <div class="w-5 h-5 border-2 border-[var(--color-primary)] border-t-transparent rounded-full animate-spin" />
      </div>

      <!-- Error -->
      <div v-else-if="error" class="p-3 m-2 text-xs text-[var(--color-error)] bg-[var(--color-error-light)] rounded">
        {{ error }}
      </div>

      <!-- Sections -->
      <div v-else class="py-1">
        <div
          v-for="sectionKey in sectionOrder"
          :key="sectionKey"
          class="border-b border-[var(--color-border)] last:border-b-0"
        >
          <!-- Section header -->
          <button
            v-if="sections[sectionKey]"
            class="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-[var(--color-tint)] transition-colors"
            @click="toggleSection(sectionKey)"
          >
            <span class="text-sm">{{ sectionIcons[sectionKey] }}</span>
            <span class="text-xs font-semibold text-[var(--color-text)] flex-1">
              {{ sections[sectionKey].label }}
            </span>
            <svg
              :class="[
                'w-3 h-3 text-[var(--color-text-muted)] transition-transform duration-200',
                openSections[sectionKey] ? 'rotate-0' : '-rotate-90',
              ]"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M4 6l4 4 4-4" />
            </svg>
          </button>

          <!-- Section metrics -->
          <Transition name="collapse">
            <div v-if="openSections[sectionKey] && sections[sectionKey]" class="px-3 pb-2">
              <div
                v-for="metric in sections[sectionKey].metrics"
                :key="metric.key"
                :class="[
                  'flex items-center justify-between py-1.5 px-2 rounded text-xs transition-all duration-300',
                  highlightedKeys.has(metric.key)
                    ? 'bg-[var(--color-primary-light)] ring-1 ring-[var(--color-primary-border)]'
                    : 'hover:bg-[var(--color-tint)]',
                ]"
              >
                <span class="text-[var(--color-text-secondary)] truncate mr-2">
                  {{ metric.label }}
                </span>
                <div class="flex items-center gap-1.5 shrink-0">
                  <span class="font-semibold text-[var(--color-text)] tabular-nums">
                    {{ metric.value }}
                  </span>
                  <span
                    v-if="metric.trend"
                    :class="[
                      'text-[10px] tabular-nums',
                      metric.trend.startsWith('+') ? 'text-[var(--color-success)]'
                        : metric.trend.startsWith('-') ? 'text-[var(--color-error)]'
                        : 'text-[var(--color-text-muted)]',
                    ]"
                  >
                    {{ metric.trend }}
                  </span>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- Collapsed vertical label -->
    <div v-if="collapsed" class="flex-1 flex items-center justify-center">
      <span class="text-[10px] font-semibold text-[var(--color-text-muted)] tracking-wider [writing-mode:vertical-lr] rotate-180">
        GTM CONTEXT
      </span>
    </div>
  </div>
</template>

<style scoped>
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}
.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 300px;
}
</style>
