<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { branchesApi } from '../../api/branches'
import ShimmerCard from '../ui/ShimmerCard.vue'

const props = defineProps({
  branches: { type: Array, required: true },
  simulationId: { type: String, default: null },
})

const emit = defineEmits(['navigate-branch'])

const loading = ref(false)
const error = ref(null)
const insights = ref([])
const source = ref('template')
const expandedInsight = ref(null)

const hasEnoughBranches = computed(() => props.branches.length >= 2)

const sortedInsights = computed(() => {
  const order = { impact: 0, recommendation: 1, warning: 2, observation: 3 }
  return [...insights.value].sort(
    (a, b) => (order[a.type] ?? 4) - (order[b.type] ?? 4),
  )
})

const typeConfig = {
  impact: {
    icon: '⚡',
    label: 'Impact',
    bg: 'bg-[var(--color-primary-light)]',
    border: 'border-[var(--color-primary-border)]',
    text: 'text-[var(--color-primary)]',
    bar: 'bg-[var(--color-primary)]',
  },
  recommendation: {
    icon: '✦',
    label: 'Recommendation',
    bg: 'bg-[var(--color-success-light)]',
    border: 'border-[var(--color-success)]',
    text: 'text-[var(--color-success)]',
    bar: 'bg-[var(--color-success)]',
  },
  warning: {
    icon: '▲',
    label: 'Warning',
    bg: 'bg-[var(--color-warning-light)]',
    border: 'border-[var(--color-warning)]',
    text: 'text-[var(--color-warning)]',
    bar: 'bg-[var(--color-warning)]',
  },
  observation: {
    icon: '◉',
    label: 'Observation',
    bg: 'bg-[var(--color-accent-tint)]',
    border: 'border-[var(--color-accent)]',
    text: 'text-[var(--color-accent)]',
    bar: 'bg-[var(--color-accent)]',
  },
}

function getTypeConfig(type) {
  return typeConfig[type] || typeConfig.observation
}

function confidenceLabel(confidence) {
  if (confidence >= 0.8) return 'High'
  if (confidence >= 0.6) return 'Medium'
  return 'Low'
}

function confidenceColor(confidence) {
  if (confidence >= 0.8) return 'text-[var(--color-success)]'
  if (confidence >= 0.6) return 'text-[var(--color-warning)]'
  return 'text-[var(--color-text-muted)]'
}

function toggleExpand(id) {
  expandedInsight.value = expandedInsight.value === id ? null : id
}

function findBranchLabel(branchId) {
  const b = props.branches.find((br) => br.branch_id === branchId)
  return b?.label || branchId
}

async function fetchInsights() {
  if (!hasEnoughBranches.value) return

  loading.value = true
  error.value = null

  try {
    const res = await branchesApi.getInsights({
      simulation_id: props.simulationId,
      branches: props.branches,
    })
    const data = res.data?.data || res.data
    insights.value = data.insights || []
    source.value = data.source || 'template'
  } catch (e) {
    error.value = e.message || 'Failed to generate insights'
    insights.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => props.branches,
  (val) => {
    if (val.length >= 2) fetchInsights()
  },
  { deep: true },
)

onMounted(() => {
  if (hasEnoughBranches.value) fetchInsights()
})
</script>

<template>
  <div class="branch-insights">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span class="text-lg">✦</span>
        <h3 class="text-base font-semibold text-[var(--color-text)]">
          Branch Insights
        </h3>
        <span
          v-if="source === 'llm'"
          class="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-[var(--color-primary-light)] text-[var(--color-primary)]"
        >
          AI
        </span>
      </div>
      <button
        v-if="!loading && hasEnoughBranches"
        class="text-xs text-[var(--color-primary)] hover:underline"
        @click="fetchInsights"
      >
        Refresh
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <ShimmerCard :lines="2" />
      <ShimmerCard :lines="2" />
      <ShimmerCard :lines="1" />
    </div>

    <!-- Not enough branches -->
    <div
      v-else-if="!hasEnoughBranches"
      class="text-center py-8 text-[var(--color-text-muted)] text-sm"
    >
      <div class="text-2xl mb-2 opacity-40">⑂</div>
      <p>At least 2 branches needed for insights.</p>
      <p class="text-xs mt-1">Create branches from the simulation timeline to compare outcomes.</p>
    </div>

    <!-- Error -->
    <div
      v-else-if="error"
      class="rounded-lg border border-[var(--color-error)] bg-[var(--color-error-light)] p-4 text-sm"
    >
      <p class="text-[var(--color-error)] font-medium">Failed to generate insights</p>
      <p class="text-[var(--color-text-secondary)] mt-1">{{ error }}</p>
      <button
        class="mt-2 text-xs text-[var(--color-primary)] hover:underline"
        @click="fetchInsights"
      >
        Try again
      </button>
    </div>

    <!-- Empty -->
    <div
      v-else-if="sortedInsights.length === 0"
      class="text-center py-8 text-[var(--color-text-muted)] text-sm"
    >
      <p>No insights could be generated from current branch data.</p>
    </div>

    <!-- Insight cards -->
    <div v-else class="space-y-3">
      <div
        v-for="insight in sortedInsights"
        :key="insight.id"
        class="rounded-lg border p-4 transition-all duration-200 cursor-pointer hover:shadow-sm"
        :class="[
          getTypeConfig(insight.type).bg,
          expandedInsight === insight.id
            ? getTypeConfig(insight.type).border
            : 'border-[var(--color-border)]',
        ]"
        @click="toggleExpand(insight.id)"
      >
        <!-- Card header -->
        <div class="flex items-start gap-3">
          <span class="text-base flex-shrink-0 mt-0.5">
            {{ getTypeConfig(insight.type).icon }}
          </span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span
                class="text-[10px] font-semibold uppercase tracking-wider"
                :class="getTypeConfig(insight.type).text"
              >
                {{ getTypeConfig(insight.type).label }}
              </span>
              <span class="text-[var(--color-text-muted)] text-[10px]">·</span>
              <span
                class="text-[10px] font-medium"
                :class="confidenceColor(insight.confidence)"
              >
                {{ confidenceLabel(insight.confidence) }} confidence
              </span>
            </div>
            <h4 class="text-sm font-semibold text-[var(--color-text)] leading-snug">
              {{ insight.title }}
            </h4>
            <p class="text-sm text-[var(--color-text-secondary)] mt-1 leading-relaxed">
              {{ insight.description }}
            </p>
          </div>
          <!-- Confidence bar -->
          <div class="flex-shrink-0 w-10 flex flex-col items-center gap-1">
            <span class="text-[10px] font-mono text-[var(--color-text-muted)]">
              {{ Math.round(insight.confidence * 100) }}%
            </span>
            <div class="w-1.5 h-8 rounded-full bg-[var(--color-border)] overflow-hidden">
              <div
                class="w-full rounded-full transition-all duration-500"
                :class="getTypeConfig(insight.type).bar"
                :style="{ height: `${insight.confidence * 100}%` }"
              />
            </div>
          </div>
        </div>

        <!-- Evidence (expanded) -->
        <div
          v-if="expandedInsight === insight.id && insight.evidence?.length"
          class="mt-3 pt-3 border-t border-[var(--color-border)]"
        >
          <p class="text-[10px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
            Evidence
          </p>
          <div class="space-y-1.5">
            <button
              v-for="(ev, idx) in insight.evidence"
              :key="idx"
              class="flex items-center gap-2 w-full text-left text-xs rounded px-2 py-1.5 hover:bg-[var(--color-tint)] transition-colors"
              @click.stop="emit('navigate-branch', ev.branch_id)"
            >
              <span class="text-[var(--color-primary)]">⑂</span>
              <span class="text-[var(--color-text)] font-medium truncate">
                {{ findBranchLabel(ev.branch_id) }}
              </span>
              <span class="text-[var(--color-text-muted)] ml-auto flex-shrink-0">
                {{ ev.metric }}:
                <span class="font-mono text-[var(--color-text)]">
                  {{ typeof ev.value === 'number' && ev.value < 1 && ev.value > 0
                    ? `${(ev.value * 100).toFixed(0)}%`
                    : ev.value
                  }}
                </span>
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
